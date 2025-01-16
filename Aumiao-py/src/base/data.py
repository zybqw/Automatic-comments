import json
from os import getcwd, path
from typing import Any, TypedDict, cast

from . import file as File
from .decorator import singleton

# 定义常量
DATA_FILE_PATH: str = path.join(getcwd(), "data", "data.json")
CACHE_FILE_PATH: str = path.join(getcwd(), "data", "cache.json")
SETTING_FILE_PATH: str = path.join(getcwd(), "data", "setting.json")


# 自定义字典类，用于自动同步到文件
class SyncDict(dict[str, Any]):
	"""
	自定义字典类，用于在修改内容时自动同步到文件中。
	"""

	def __init__(self, file_path: str, parent_ref: dict[str, Any], key: str | None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.file_path = file_path
		self.parent_ref = parent_ref  # 父级字典的引用
		self.key = key  # 当前 SyncDict 在父字典中的键

	def _sync_to_file(self):
		if self.key is None:
			self.parent_ref = self
		else:
			self.parent_ref[self.key] = self
			self.parent_ref[self.key] = self
		with open(self.file_path, "w", encoding="utf-8") as f:
			json.dump(self.parent_ref, f, ensure_ascii=False, indent=4)

	def __setitem__(self, key, value):
		super().__setitem__(key, value)
		self._sync_to_file()

	def __delitem__(self, key):
		super().__delitem__(key)
		self._sync_to_file()

	def update(self, *args, **kwargs):
		super().update(*args, **kwargs)
		self._sync_to_file()

	def clear(self):
		super().clear()
		self._sync_to_file()


# 定义 TypedDict 数据结构
class AccountData(TypedDict):
	author_level: str
	create_time: str
	description: str
	id: str
	identity: str
	nickname: str
	password: str


class InfoData(TypedDict):
	e_mail: str
	nickname: str
	qq_number: int


class BlackRoomData(TypedDict):
	post: list[str]
	user: list[str]
	work: list[str]


class UserData(TypedDict):
	ads: list[str]
	answers: list[dict[str, str | list[str]]]
	black_room: BlackRoomData
	comments: list[str]
	emojis: list[str]
	replies: list[str]


class _CodeMaoData(TypedDict):
	ACCOUNT_DATA: AccountData
	INFO: InfoData
	USER_DATA: UserData


class DefaultAction(TypedDict):
	action: str
	name: str


class ClientParameter(TypedDict):
	all_read_type: list[str]
	clear_ad_exclude_top: bool
	cookie_check_url: str
	get_works_method: str
	password_login_method: str


class Parameter(TypedDict):
	CLIENT: ClientParameter


class ExtraBody(TypedDict):
	enable_search: bool


class More(TypedDict):
	extra_body: ExtraBody
	stream: bool


class DashscopePlugin(TypedDict):
	model: str
	more: More


class Plugin(TypedDict):
	DASHSCOPE: DashscopePlugin
	prompt: str


class Program(TypedDict):
	AUTHOR: str
	HEADERS: dict
	MEMBER: str
	SLOGAN: str
	TEAM: str
	VERSION: str


class _CodeMaoSetting(TypedDict):
	DEFAULT: list[DefaultAction]
	PARAMETER: Parameter
	PLUGIN: Plugin
	PROGRAM: Program


class _CodeMaoCache(TypedDict):
	collected: int
	fans: int
	level: int
	liked: int
	nickname: str
	timestamp: int
	user_id: int
	view: int


# 单例类定义
@singleton
class CodeMaoData:
	def __init__(self) -> None:
		_data = File.CodeMaoFile().file_load(path=DATA_FILE_PATH, type="json")
		_data = cast(dict[str, Any], _data)
		self.data: _CodeMaoData = cast(
			_CodeMaoData, SyncDict(file_path=DATA_FILE_PATH, parent_ref=_data, key=None, **_data)
		)


@singleton
class CodeMaoCache:
	def __init__(self) -> None:
		_cache = File.CodeMaoFile().file_load(path=CACHE_FILE_PATH, type="json")
		_cache = cast(dict[str, Any], _cache)
		self.cache: _CodeMaoCache = cast(
			_CodeMaoCache, SyncDict(file_path=CACHE_FILE_PATH, parent_ref=_cache, key=None, **_cache)
		)


@singleton
class CodeMaoSetting:
	def __init__(self) -> None:
		_setting = File.CodeMaoFile().file_load(path=SETTING_FILE_PATH, type="json")
		self.setting: _CodeMaoSetting = cast(_CodeMaoSetting, _setting)
