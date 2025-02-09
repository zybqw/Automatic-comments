import importlib
from types import ModuleType
from typing import Any

from . import import_all

__all__ = [import_all]  # type: ignore  # noqa: PGH003, PLE0604
# 导入显式导入模块

# 定义需要延迟加载的模块
_API_MODULES: list[str] = ["community", "edu", "forum", "library", "pickduck", "shop", "user", "work"]

# 定义直接导入的核心模块和工具
_CORE_MODULES = {"client": ".core.client", "data": ".utils.data"}

# 模块缓存
_loaded_modules: dict[str, ModuleType] = {}

# 导出的属性列表
__all__: list[str] = _API_MODULES + list(_CORE_MODULES.keys())  # type: ignore  # noqa: PGH003, PLE0605

# 版本信息
__version__ = "2.0.0"
__author__ = "Aurzex"
__team__ = "Aumiao Team"
__team_members__ = "Aurzex, MoonLeaaaf, Nomen, MiTao"


def __getattr__(name: str) -> ModuleType | Any:  # noqa: ANN401
	"""实现模块的延迟加载"""
	# 处理 API 模块
	if name in _API_MODULES:
		if name not in _loaded_modules:
			module = importlib.import_module(f".api.{name}", __package__)
			# 可选:执行模块初始化
			if hasattr(module, "__init_extension__"):
				module.__init_extension__()
			_loaded_modules[name] = module
		return _loaded_modules[name]

	# 处理核心模块和工具
	if name in _CORE_MODULES:
		if name not in _loaded_modules:
			module = importlib.import_module(_CORE_MODULES[name], __package__)
			_loaded_modules[name] = module
		return _loaded_modules[name]

	msg = f"module {__name__!r} has no attribute {name!r}"
	raise AttributeError(msg)


def __dir__() -> list[str]:
	"""增强 IDE 自动补全支持"""
	return sorted([*list(__all__), "__version__", "__author__", "__team__", "__team_members__"])


# 可选:预加载所有模块
def preload_all() -> None:
	"""预加载所有模块"""
	for module_name in _API_MODULES:
		if module_name not in _loaded_modules:
			__getattr__(module_name)

	for module_name in _CORE_MODULES:
		if module_name not in _loaded_modules:
			__getattr__(module_name)
