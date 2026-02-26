# calibrate_npu_gpu 自动拆解对比 NPU 和 GPU profile 指南

## 简介

msprof-analyze 提供了 `calibrate_npu_gpu` 功能，用于自动对比 NPU 和 GPU 的性能数据，帮助用户进行跨平台的性能校准和瓶颈分析。该功能能够：

* **跨平台分析**：支持 GPU（NVIDIA）Nsys SQLite 格式和 NPU（Ascend）PyTorch Profiler DB 格式的性能数据
* **模块匹配**：使用规则匹配和模糊匹配（Levenshtein 距离），自动对齐 GPU 和 NPU 的模块层次结构
* **性能差异分析**：精确计算 GPU 与 NPU 在相同模块下的时间比例，识别性能退化点
* **可视化报告**：生成 Excel 格式的对比报告

## 操作指导

### 性能数据准备

#### 1. GPU 性能数据采集

对于 GPU 平台，推荐使用 NVIDIA Nsys 工具采集 PyTorch 模型的性能数据。以下脚本展示了如何使用 `nsys profile` 采集 vLLM 推理的 GPU 性能数据：

```bash
#!/bin/bash

echo "Start Profiling"
export CUDA_VISIBLE_DEVICES=0,1
dir_model="/path/to/model"
dir_ouput_prof="/path/to/model_profile_gpu"

nsys profile  \
    --stats=true \
    --trace-fork-before-exec=true \
    --cuda-graph-trace=node \
    --trace=cuda,nvtx \
    --capture-range=cudaProfilerApi \
    --pytorch=autograd-nvtx \
    -o ${dir_ouput_prof} \
vllm bench latency \
    --enforce-eager \
    --model ${dir_model} \
    --num-iters-warmup 5 \
    --num-iters 1 \
    --batch-size 16 \
    --input-len 512 \
    --model-parallel-size 2 \
    --output-len 8
```

**关键参数说明：**
* `--stats=true`：nsys 在完成 profile 采集后会自动生成 sqlite 数据库文件
* `--trace=cuda,nvtx`：启用 CUDA 和 NVTX 跟踪，NVTX 标记用于模块层次解析
* `--pytorch=autograd-nvtx`：启用 PyTorch autograd 的 NVTX 标记
* `--capture-range=cudaProfilerApi`：捕获 `cudaProfilerStart/Stop` 范围内的性能数据
* `--enforce-eager`：禁用 CUDA Graph，确保算子逐条执行以便准确计时

#### 2. NPU 性能数据采集

对于 NPU（Ascend）平台，需要使用 PyTorch Profiler 采集性能数据，并确保开启 `msprof_tx` 打点功能：

```bash
#!/bin/bash

# eager模式
# 使用 vllm 的 profiler 能力，如果要支持 msprof_tx 需要修改 vllm-ascend/vllm_ascend/worker/worker_v1.py
# - 修改 experimental_config 中的 msprof_tx 为 True，开启自定义打点功能
# - 数据导出类型 export_type 添加 db
# - vllm 推理时候打开 enforce_eager=True

dir_model="/path/to/model"
dir_ouput_prof="/path/to/model_profile_npu"

# 通过 VLLM_TORCH_PROFILER_DIR 环境变量开启性能采集，设置性能数据落盘位置，也可以在终端设置该环境变量
export VLLM_TORCH_PROFILER_DIR=${dir_ouput_prof}
export ASCEND_RT_VISIBLE_DEVICES=0,1

echo "Start Profiling"
# 修改benchmark代码加入mstx打点
# 增加profile选项启动llm.start_profile()
vllm bench latency \
    --enforce-eager \
    --model ${dir_model} \
    --num-iters-warmup 5 \
    --num-iters 1 \
    --batch-size 16 \
    --input-len 512 \
    --output-len 8 \
    --model-parallel-size 2 \
    --profile
```

**关键配置说明：**
* **环境变量**：`VLLM_TORCH_PROFILER_DIR` 设置性能数据输出目录
* **打点配置**：需修改 vLLM-Ascend 代码，在 `experimental_config` 中设置 `msprof_tx=True` 和 `export_type=['text', 'db']`
* **eager 模式**：当前只支持 eager 模式，请使用 `--enforce-eager` 确保算子逐条执行

#### 3. 数据文件要求

确保采集到的性能数据文件满足以下要求：
* **GPU 文件**：Nsys 导出的 SQLite 文件（扩展名通常为 `.sqlite`）
* **NPU 文件**：PyTorch Profiler 生成的 DB 文件（通常为 `ascend_pytorch_profiler_0.db`）
* **数据完整性**：文件中必须包含完整的模块层次信息（NVTX/mstx 打点）和 Kernel 执行信息

### 执行分析命令

使用以下命令执行 GPU/NPU 校准分析：

```bash
msprof-analyze cluster -m calibrate_npu_gpu \
  --profiling_path /path/to/npu_profile \
  --baseline_profiling_path /path/to/gpu_profile.sqlite \
  --output_path ./calibration_result \
  --export_type text \
  --dump_intermediate_results 
```

**参数说明：**
* `-m calibrate_npu_gpu`：指定使用校准分析模式
* `--profiling_path`：NPU 性能数据路径（必须）
* `--baselin_profiling_path`：GPU 性能数据文件路径（必须）
* `--output_path`：分析结果输出目录
* `--export_type`：导出类型，可选`db`或`text`，默认为 `db`
* `--fuzzy_threshold`：NPU/GPU module name fuzzy 匹配的阈值，默认为 `0.8`
* `--dump_intermediate_results`: 保存中间分析结果（GPU/NPU profile 分析结果）

### 输出说明

#### 1. Excel 输出

msprof-analyze 会在输出目录生成 `compare_profile_report_{rank_id}.xlsx` 文件，包含以下信息：

| 字段 | 说明 |
|------|------|
| (GPU) Parent Module | GPU 侧的父模块名称 |
| (GPU) Module | GPU 侧的模块名称 |
| (NPU) Parent Module | NPU 侧的父模块名称 |
| (NPU) Module | NPU 侧的模块名称 |
| Match Type | 匹配类型：`rule`（规则匹配）或 `fuzzy`（模糊匹配） |
| (GPU) Op Name | GPU 侧的算子名称列表 |
| (GPU) Op Count | GPU 侧算子出现次数 |
| (GPU) Kernel List | GPU 侧的 Kernel 名称列表 |
| (GPU) Total Kernel Duration(us) | GPU 侧总执行时间（微秒） |
| (GPU) Total Kernel Duration(%) | GPU 侧总执行时间占比（百分比） |
| (GPU) Avg Kernel Duration(us) | GPU 侧平均执行时间（微秒） |
| (NPU) Op Name | NPU 侧的算子名称列表 |
| (NPU) Op Count | NPU 侧算子出现次数 |
| (NPU) Kernel List | NPU 侧的 Kernel 名称列表 |
| (NPU) Total Kernel Duration(us) | NPU 侧总执行时间（微秒） |
| (NPU) Total Kernel Duration(%) | NPU 侧总执行时间占比（百分比） |
| (NPU) Avg Kernel Duration(us) | NPU 侧平均执行时间（微秒） |
| (NPU/GPU) Module Time Ratio | Module 级别的 NPU/GPU 耗时对比 |
| (NPU-GPU,us) Module Time Diff | Module 级别的 NPU-GPU 耗时对比（微妙） |

#### 2. 中间输出

指定 `--dump_intermediate_results` 时，保存GPU/NPU中间分析结果在 `{platform}_report_{rank_id}.xlsx` 文件中


## 附录

### `vllm bench latency` 脚本修改说明

下列脚本为 GPU 环境中的修改后的 `vllm/vllm/benchmarks/latency.py`，NPU 替换为 `mstx` 即可

```python
import argparse
import dataclasses
import json
import os
import time
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from tqdm import tqdm

import vllm.envs as envs
from vllm.benchmarks.lib.utils import convert_to_pytorch_benchmark_format, write_to_json
from vllm.engine.arg_utils import EngineArgs
from vllm.inputs import PromptType
from vllm.sampling_params import BeamSearchParams

# Modification 1: Inject NVTX ranges into nn.Module calls for profiling
# --- START OF INJECTION ---
import nvtx
import torch.cuda.profiler as cuda_profiler
original_call = nn.Module.__call__

def custom_call(self, *args, **kwargs):
    module_name = self.__class__.__name__
    nvtx.push_range(module_name)
    tmp = original_call(self, *args, **kwargs)
    nvtx.pop_range()
    return tmp
nn.Module.__call__ = custom_call
# --- END OF INJECTION ---

... # original code

def main(args: argparse.Namespace):
    
    ... # original code

    def llm_generate():
        if not args.use_beam_search:
            llm.generate(dummy_prompts, sampling_params=sampling_params, use_tqdm=False)
        else:
            llm.beam_search(
                dummy_prompts,
                BeamSearchParams(
                    beam_width=args.n,
                    max_tokens=args.output_len,
                    ignore_eos=True,
                ),
            )

    def run_to_completion(profile_dir: str | None = None):
        if profile_dir:
            llm.start_profile()
            llm_generate()
            llm.stop_profile()
        else:
            start_time = time.perf_counter()
            llm_generate()
            end_time = time.perf_counter()
            latency = end_time - start_time
            return latency

    print("Warming up...")
    for _ in tqdm(range(args.num_iters_warmup), desc="Warmup iterations"):
        run_to_completion(profile_dir=None)

    if args.profile:
        profile_dir = envs.VLLM_TORCH_PROFILER_DIR
        print(f"Profiling (results will be saved to '{profile_dir}')...")
        run_to_completion(profile_dir=profile_dir)
        return

    cuda_profiler.start() # Modification 2: inform nsys to start profiling at this point

    # Benchmark.
    latencies = []
    for _ in tqdm(range(args.num_iters), desc="Profiling iterations"):
        latencies.append(run_to_completion(profile_dir=None))

    cuda_profiler.stop() # Modification 3: inform nsys to stop profiling at this point

    ... # original code
```
