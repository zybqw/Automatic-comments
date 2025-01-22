from collections.abc import Callable
from functools import wraps
from locale import Error
from time import sleep
from typing import Any


def singleton(cls: Any) -> Callable[..., Any]:  # noqa: ANN401
	_instance = {}

	def _singleton(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
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
