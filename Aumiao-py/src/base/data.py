import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from pathlib import Path
from typing import Generic, TypeVar, cast, get_args, get_origin, get_type_hints

from src.base.decorator import singleton

T = TypeVar("T")

# 定义常量
DATA_DIR = Path.cwd() / "data"
DATA_FILE_PATH = DATA_DIR / "data.json"
CACHE_FILE_PATH = DATA_DIR / "cache.json"
SETTING_FILE_PATH = DATA_DIR / "setting.json"

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------
# 数据类定义 (保持与之前相同)
# --------------------------
@dataclass
class AccountData:
	author_level: str = ""
	create_time: str = ""
	description: str = ""
	id: str = ""
	identity: str = ""
	nickname: str = ""
	password: str = ""


@dataclass
class BlackRoomData:
	post: list[str] = field(default_factory=list)
	user: list[str] = field(default_factory=list)
	work: list[str] = field(default_factory=list)


@dataclass
class UserData:
	ads: list[str] = field(default_factory=list)
	answers: list[dict[str, str | list[str]]] = field(default_factory=list)
	black_room: BlackRoomData = field(default_factory=BlackRoomData)
	comments: list[str] = field(default_factory=list)
	emojis: list[str] = field(default_factory=list)
	replies: list[str] = field(default_factory=list)


@dataclass
class CodeMaoData:
	INFO: dict[str, str]
	ACCOUNT_DATA: AccountData = field(default_factory=AccountData)
	USER_DATA: UserData = field(default_factory=UserData)


@dataclass
class DefaultAction:
	action: str
	name: str


@dataclass
class Parameter:
	all_read_type: list[str]
	clear_ad_exclude_top: bool
	cookie_check_url: str
	get_works_method: str
	password_login_method: str
	spam_max: int


@dataclass
class ExtraBody:
	enable_search: bool


@dataclass
class More:
	extra_body: ExtraBody
	stream: bool


@dataclass
class DashscopePlugin:
	model: str
	more: More


@dataclass
class Plugin:
	DASHSCOPE: DashscopePlugin
	prompt: str


@dataclass
class Program:
	AUTHOR: str
	HEADERS: dict[str, str]
	MEMBER: str
	SLOGAN: str
	TEAM: str
	VERSION: str


@dataclass
class CodeMaoCache:
	collected: int
	fans: int
	level: int
	liked: int
	nickname: str
	timestamp: int
	user_id: int
	view: int


@dataclass
class CodeMaoSetting:
	DEFAULT: list[DefaultAction] = field(default_factory=list)
	PARAMETER: Parameter = field(default_factory=cast(Callable[[], Parameter], Parameter))
	PLUGIN: Plugin = field(default_factory=cast(Callable[[], Plugin], Plugin))
	PROGRAM: Program = field(default_factory=cast(Callable[[], Program], Program))


# ... 其他数据类定义保持与之前相同 ...


# --------------------------
# 核心转换工具函数
# --------------------------
# 修改后的核心工具函数
def dict_to_dataclass(cls: type[T], data: dict) -> T:
	"""类型安全的字典到数据类转换"""
	if not (is_dataclass(cls) and isinstance(cls, type)):
		msg = f"{cls.__name__} must be a dataclass type"
		raise ValueError(msg)

	field_types = get_type_hints(cls)
	kwargs = {}

	for field_name, field_type in field_types.items():
		value = data.get(field_name)
		if value is None:
			continue

		# 处理嵌套数据类(显式类型断言)
		if is_dataclass(field_type):
			field_type = cast(type, field_type)
			kwargs[field_name] = dict_to_dataclass(field_type, value)

		# 处理列表中的嵌套数据类(精确类型解析)
		elif (_origin := get_origin(field_type)) is list:
			item_type = get_args(field_type)[0]
			if is_dataclass(item_type):
				item_type = cast(type, item_type)
				kwargs[field_name] = [dict_to_dataclass(item_type, item) for item in value]
			else:
				kwargs[field_name] = value

		else:
			kwargs[field_name] = value

	return cls(**kwargs)


# --------------------------
# 文件操作工具函数
# --------------------------
def load_json_file(path: Path, data_class: type[T]) -> T:
	"""加载JSON文件并转换为指定数据类"""
	if not path.exists():
		return data_class()  # 返回默认实例

	try:
		data = json.loads(path.read_text(encoding="utf-8"))
		return dict_to_dataclass(data_class, data)
	except (json.JSONDecodeError, KeyError, TypeError) as e:
		print(f"Error loading {path.name}: {e!s}")
		return data_class()


def save_json_file(path: Path, data: object) -> None:
	"""将数据类实例保存为JSON文件"""
	if not (is_dataclass(data) and not isinstance(data, type)):  # 严格检查是实例不是类
		msg = "Only dataclass instances can be saved"
		raise ValueError(msg)

	path.parent.mkdir(parents=True, exist_ok=True)
	serialized = asdict(data)  # type: ignore[arg-type]
	path.write_text(json.dumps(serialized, ensure_ascii=False, indent=4), encoding="utf-8")


# --------------------------
# 单例管理器(修改加载方式)
# --------------------------


class BaseManager(Generic[T]):
	_data: T
	_file_path: Path

	def __init__(self, file_path: Path, data_class: type[T]) -> None:
		self._data = load_json_file(file_path, data_class)
		self._file_path = file_path

	def get_data(self) -> T:
		return self._data

	def update(self, new_data: dict[str, object]) -> None:
		for key, value in new_data.items():
			if hasattr(self._data, key):
				current_value = getattr(self._data, key)
				if is_dataclass(current_value) or (isinstance(current_value, type) and is_dataclass(current_value)):
					if isinstance(value, dict):
						updated_value = current_value(**value) if isinstance(current_value, type) else replace(current_value, **value)
						setattr(self._data, key, updated_value)
					else:
						print(f"Warning: Expected a dict for {key}, got {type(value).__name__}.")
				else:
					setattr(self._data, key, value)
		self.save_data()

	def delete(self, *keys: str) -> None:
		for key in keys:
			if hasattr(self._data, key):
				current_value = getattr(self._data, key)
				if is_dataclass(current_value):
					setattr(self._data, key, type(current_value)())
				elif isinstance(current_value, type) and is_dataclass(current_value):
					setattr(self._data, key, current_value())
				else:
					setattr(self._data, key, None)
		self.save_data()

	def save_data(self) -> None:
		save_json_file(self._file_path, self._data)


@singleton
class CodeMaoDataManager(BaseManager[CodeMaoData]):
	def __init__(self) -> None:
		super().__init__(DATA_FILE_PATH, CodeMaoData)


@singleton
class CodeMaoCacheManager(BaseManager[CodeMaoCache]):
	def __init__(self) -> None:
		super().__init__(CACHE_FILE_PATH, CodeMaoCache)


@singleton
class CodeMaoSettingManager(BaseManager[CodeMaoSetting]):
	def __init__(self) -> None:
		super().__init__(SETTING_FILE_PATH, CodeMaoSetting)
