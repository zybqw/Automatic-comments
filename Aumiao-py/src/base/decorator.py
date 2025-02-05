from collections.abc import Callable
from functools import wraps
from locale import Error
from time import sleep
from typing import Any


def singleton(cls):  # noqa: ANN001, ANN201
	_instance = {}

	def _singleton(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
		if cls not in _instance:
			_instance[cls] = cls(*args, **kwargs)
		return _instance[cls]

	return _singleton


def retry(retries: int = 3, delay: float = 1) -> Callable:
	if retries < 1 or delay <= 0:
		msg = "Are you high, mate?"
		raise ValueError(msg)

	def decorator(func: Callable) -> Callable:
		@wraps(func)
		def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
			for i in range(1, retries + 1):
				try:
					return func(*args, **kwargs)
				except Exception as e:
					if i == retries:
						print(f"Error: {e!r}.")
						print(f'"{func.__name__}()" failed after {retries} retries.')
						break
					print(f"Error: {e!r} -> Retrying...")
					sleep(delay)
			raise Error

		return wrapper

	return decorator


def skip_on_error(func):  # noqa: ANN001, ANN201
	"""捕获异常并跳过当前循环"""

	@wraps(func)
	def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
		try:
			return func(*args, **kwargs)
		except Exception as e:
			print(f"Error occurred: {e}. Skipping this iteration.")
			return None  # 继续执行下一个循环

	return wrapper
