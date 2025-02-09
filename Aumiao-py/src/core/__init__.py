# 使用 Python 3.7+ 的模块级别 __getattr__
import importlib
from types import ModuleType

# 模块白名单
_MODULE_NAMES: list[str] = ["client"]

# 模块缓存字典
_loaded_modules: dict[str, ModuleType] = {}

# 兼容 from module import *
__all__ = _MODULE_NAMES  # type: ignore  # noqa: PGH003, PLE0605


def __getattr__(name: str) -> ModuleType:
	"""实现模块的延迟加载"""
	# 只处理白名单内的模块
	if name not in _MODULE_NAMES:
		msg = f"module {__name__!r} has no attribute {name!r}"
		raise AttributeError(msg)

	# 检查缓存
	if name in _loaded_modules:
		return _loaded_modules[name]

	# 动态导入模块
	module = importlib.import_module(f".{name}", __package__)

	# 可选:执行模块初始化逻辑
	if hasattr(module, "__init_extension__"):
		module.__init_extension__()

	# 缓存并返回
	_loaded_modules[name] = module
	return module


def __dir__() -> list[str]:
	"""增强 IDE 自动补全支持"""
	return sorted(__all__ + list(_loaded_modules.keys()))
