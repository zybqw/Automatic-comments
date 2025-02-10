import time
from dataclasses import asdict, is_dataclass
from typing import Any, TypeVar, cast

from .decorator import singleton

Data = list[dict] | dict
Nested_dict = dict[str, Any]
T = TypeVar("T")


@singleton
class CodeMaoProcess:
	def filter_data(
		self,
		data: Data,
		reserve: list[str] | None = None,
		exclude: list[str] | None = None,
	) -> Data:
		"""
		处理输入数据,根据 `reserve` 或 `exclude` 进行键筛选

		:param data: 输入数据(列表或字典)
		:param reserve: 保留的键列表
		:param exclude: 排除的键列表
		:return: 筛选后的数据,保持原数据结构
		:raises ValueError: 参数冲突或数据类型错误
		"""
		if reserve and exclude:
			msg = "请仅提供 'reserve' 或 'exclude' 中的一个参数"
			raise ValueError(msg)

		def filter_item(item: dict) -> dict:
			"""键过滤核心逻辑"""
			if reserve:
				return {k: v for k, v in item.items() if k in reserve}
			if exclude:
				return {k: v for k, v in item.items() if k not in exclude}
			return dict(item)  # 无过滤条件返回副本

		if isinstance(data, list):
			return [filter_item(item) for item in data if isinstance(item, dict)]
		if isinstance(data, dict):
			return filter_item(data)
		msg = f"不支持的数据类型: {type(data)}"
		raise ValueError(msg)

	@staticmethod
	def insert_zero_width_chars(content: str) -> str:
		"""插入零宽字符优化实现"""
		return "\u200b".join(content)

	@staticmethod
	def format_timestamp(timestamp: int) -> str:
		"""时间格式化优化实现"""
		return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

	def get_nested_value(self, data: Nested_dict, path: str | None) -> Any:  # noqa: ANN401
		"""安全的嵌套值获取"""
		if not path:
			return data

		value = data
		for key in path.split("."):
			if not isinstance(value, dict):
				return None
			value = value.get(key)
		return value

	@staticmethod
	def convert_cookie_to_str(cookie: dict[str, str]) -> str:
		"""Cookie转换优化"""
		return "; ".join(f"{k}={v}" for k, v in cookie.items())

	def filter_items_by_values(self, data: Data, id_path: str, values: list[Any]) -> list[dict]:
		"""增强型数据过滤"""
		items = data.get("items", []) if isinstance(data, dict) else data if isinstance(data, list) else []

		return [item for item in items if self.get_nested_value(item, id_path) in values]

	@staticmethod
	def deduplicate(sequence: list[Any]) -> list[Any]:
		"""高效顺序去重"""
		seen = set()
		return [x for x in sequence if not (x in seen or seen.add(x))]


class CodeMaoRoutine:
	def __init__(self) -> None:
		# 初始化CodeMaoProcess类
		self.process = CodeMaoProcess()

	@staticmethod
	def get_timestamp() -> float:
		"""获取当前时间戳"""
		return time.time()

	def display_data_changes(
		self,
		before_data: dict[str, Any] | T,
		after_data: dict[str, Any] | T,
		metrics: dict[str, str],
		date_field: str | None = None,
	) -> None:
		"""改进的数据变化展示"""

		def to_dict(data: dict[str, Any] | T) -> dict[str, Any]:
			# 将数据转换为字典
			if isinstance(data, dict):
				return data
			if hasattr(data, "__dict__"):
				return vars(data)
			if is_dataclass(data):
				return asdict(cast(Any, data))
			msg = f"Unsupported data type: {type(data)}"
			raise TypeError(msg)

		try:
			before_dict = to_dict(before_data)
			after_dict = to_dict(after_data)
		except TypeError as e:
			print(f"Error converting data to dictionary: {e}")
			return

		if date_field:
			fmt = self.process.format_timestamp
			print(f"时间段: {fmt(before_dict[date_field])} → {fmt(after_dict[date_field])}")

		for field, label in metrics.items():
			before = before_dict.get(field, 0)
			after = after_dict.get(field, 0)
			print(f"{label}: {after - before:+} (当前: {after}, 初始: {before})")

	def find_prefix_suffix(self, text: str | int, candidates: list[str]) -> tuple[int | None, int | None]:
		"""元组返回优化实现"""
		target = str(text)
		for item in candidates:
			if isinstance(item, str) and target in item:
				parts = item.split(".", 1)
				try:
					return int(parts[0]), int(parts[1]) if len(parts) > 1 else None
				except ValueError:
					continue
		return (None, None)

	def merge_user_data(self, data_list: list[dict]) -> dict:
		"""改进的深度合并算法"""
		merged = {}
		counter = {}

		for item in filter(None, data_list):
			for key, value in item.items():
				# 字段计数
				counter[key] = counter.get(key, 0) + 1

				# 深度合并逻辑
				if isinstance(value, dict):
					merged.setdefault(key, {}).update(value)
				else:
					merged[key] = value

		# 保留出现多次的字段
		return {k: v for k, v in merged.items() if counter[k] > 1}
