import sys
import logging
from .mstx_torch_plugin import apply_mstx_patch

logger = logging.getLogger()
requirements_module_list = ['torch', 'torch_npu']

enable_mstx_torch = True
for module_name in requirements_module_list:
    if module_name not in sys.modules:
        enable_mstx_torch = False
        logger.error(f"mstx_torch_plugin not enabled, please ensure that {module_name} has been installed.")

if enable_mstx_torch:
    apply_mstx_patch()
