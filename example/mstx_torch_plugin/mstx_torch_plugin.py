# Copyright (c) 2024, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from datetime import datetime
import os
import functools
import re
import site
import torch
from torch.nn import Module
from torch.utils.data import DataLoader
from torch.optim.optimizer import register_optimizer_step_post_hook

original_forward_call = Module.__call__
original_iter = DataLoader.__iter__
original_save = torch.serialization.save
original_singlenext = torch.utils.data.dataloader._SingleProcessDataLoaderIter.__next__
original_multinext = torch.utils.data.dataloader._MultiProcessingDataLoaderIter.__next__
origin_patch_step_function = torch.optim.Optimizer._patch_step_function


def _print_warn_msg(message: str):
    time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{time_str} [WARNING] [{os.getpid()}] mstx_torch_plugin.py: {message}")


def _check_directory_path_readable(path):
    if not os.path.exists(path):
        msg = f"The path dose not exist: {path}"
        raise RuntimeError(msg)
    if os.path.islink(path):
        msg = f"Invalid path is a soft chain: {path}"
        raise RuntimeError(msg)
    if not os.access(path, os.R_OK):
        msg = f"The path permission check failed: {path}"
        raise RuntimeError(msg)


class MstxState:
    def __init__(self):
        self.module_dict = {}
        self.is_outer_call = True
        self.fp_range_id = None
        self.dataloader_range_id = None
        self.save_range_id = None
        self.step_range_id = None
        self.step_id = 0
        self.last_optimizer_id = None

    def add_module_dict(self, module):
        self.module_dict[module] = [
            sub_module
            for _, sub_module in module.named_modules()
            if sub_module != module
        ]

    def is_child_module(self, module):
        return any(module in value for value in self.module_dict.values())

mstx_state = MstxState()


def _is_loss_module(module):
    return isinstance(module, torch.nn.modules.loss._Loss)


def _custom_forward_call(self, *args, **kwargs):
    global mstx_state

    if not torch.npu.is_initialized():
        return original_forward_call(self, *args, **kwargs)

    # the outermost module add mstx range_start
    if mstx_state.is_outer_call:
        # not the loss module and recalculation process
        if not mstx_state.is_child_module(self) and not _is_loss_module(self):
            stream = torch.npu.current_stream()
            mstx_state.fp_range_id = torch.npu.mstx.range_start("forward", stream)
            mstx_state.add_module_dict(self)
        mstx_state.is_outer_call = False
        self.tx_visited = True

    out_call = original_forward_call(self, *args, **kwargs)

    # the outermost module add mstx range_end
    if hasattr(self, "tx_visited") and self.tx_visited:
        mstx_state.is_outer_call = True
        self.tx_visited = False
        if not _is_loss_module(self) and mstx_state.fp_range_id is not None:
            torch.npu.mstx.range_end(mstx_state.fp_range_id)
            mstx_state.fp_range_id = None

    return out_call


def _custom_dataloader_iter(self):
    global mstx_state

    out_iter = original_iter(self)

    def dataloader_wrapper(func):
        def wrapper(*args, **kwargs):
            mstx_state.dataloader_range_id = torch.npu.mstx.range_start("dataloader")
            out = func(*args, **kwargs)
            if mstx_state.dataloader_range_id is not None:
                torch.npu.mstx.range_end(mstx_state.dataloader_range_id)
                mstx_state.dataloader_range_id = None
            return out

        return wrapper

    if self.num_workers == 0:
        torch.utils.data.dataloader._SingleProcessDataLoaderIter.__next__ = dataloader_wrapper(original_singlenext)
    else:
        torch.utils.data.dataloader._MultiProcessingDataLoaderIter.__next__ = dataloader_wrapper(original_multinext)

    return out_iter


def _custom_save(func):
    global mstx_state

    @functools.wraps(func)
    def save_wrapper(*args, **kwargs):
        stream = torch.npu.current_stream()
        mstx_state.save_range_id = torch.npu.mstx.range_start("save_checkpoint", stream)
        out = func(*args, **kwargs)
        if mstx_state.save_range_id is not None:
            torch.npu.mstx.range_end(mstx_state.save_range_id)
            mstx_state.save_range_id = None
        return out

    return save_wrapper


def _step_hook(self, *args, **kwargs):
    global mstx_state

    if id(self) != mstx_state.last_optimizer_id:
        return
    stream = torch.npu.current_stream()
    mstx_state.step_id += 1
    if mstx_state.step_range_id is not None:
        torch.npu.mstx.range_end(mstx_state.step_range_id)
    mstx_state.step_range_id = torch.npu.mstx.range_start(f"step {mstx_state.step_id}", stream)


def _custom_step(optimizer: torch.optim.Optimizer):
    global mstx_state

    origin_patch_step_function(optimizer)
    mstx_state.last_optimizer_id = id(optimizer)


def _get_torch_npu_version_str():
    torch_npu_version_str = ""
    site_packages = site.getsitepackages()
    if site_packages and site_packages[0]:
        path = site_packages[0]
        version_path = os.path.join(path, "torch_npu", "version.py")
        _check_directory_path_readable(version_path)
        # example version info: "__version__ = '2.1.0.post11.xxxxxx'"
        try:
            with open(version_path, "r") as f:
                for line in f:
                    if line.find("__version__") != -1:
                        torch_npu_version_str = line.strip().split("=")[-1][2:-1]
                        break
        except Exception as e:
            _print_warn_msg(f"Failed to open {version_path} to get torch npu version.")
    return torch_npu_version_str


def _get_torch_npu_info(version_str: str):
    # version info example: "2.1.0.post11.xxxxxx"
    match = re.search(r"^(\d+\.\d+\.\d+)\.post(\d+)", version_str)
    if match and len(match.groups()) == 2:
        return match.group(1), match.group(2)
    else:
        return '', ''


def _check_pta_support_patch():
    pta_support_patch_version = {
        "2.1.0": 10,
        "2.3.1": 4,
        "2.4.0": 2,
    }
    torch_npu_version_str = _get_torch_npu_version_str()
    if not torch_npu_version_str:
        _print_warn_msg("Failed to get torch_npu version info.")
        return False
    torch_branch, torch_npu_version = _get_torch_npu_info(torch_npu_version_str)
    if not torch_branch or not torch_npu_version or not torch_npu_version.isdigit():
        _print_warn_msg("Failed to get valid torch branch or torch_npu version.")
        return False
    for branch, post_version in pta_support_patch_version.items():
        if torch_branch == branch and int(torch_npu_version) <= post_version:
            return False
    return True


def apply_mstx_patch():
    pta_support_patch = _check_pta_support_patch()
    Module.__call__ = _custom_forward_call
    if not pta_support_patch:
        DataLoader.__iter__ = _custom_dataloader_iter
        torch.serialization.save = _custom_save(original_save)
    torch.optim.Optimizer._patch_step_function = _custom_step
    register_optimizer_step_post_hook(_step_hook)
