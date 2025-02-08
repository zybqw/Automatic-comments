import json
import time
from enum import Enum
from pathlib import Path
from typing import Literal, Protocol, TypeAlias, TypedDict, cast

import requests
from requests.cookies import RequestsCookieJar
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout

from . import data, file, tool
from .decorator import singleton

LOG_DIR: Path = Path.cwd() / "log"
LOG_FILE_PATH: Path = LOG_DIR / f"{int(time.time())}.txt"


class HTTPSTATUS(Enum):
	OK = 200
	CREATED = 201
	NO_CONTENT = 204


# 类型定义增强
class PaginationConfig(TypedDict, total=False):
	amount_key: Literal["limit", "page_size", "current_page"]
	offset_key: Literal["offset", "page", "current_page"]
	response_amount_key: Literal["limit", "page_size"]
	response_offset_key: Literal["offset", "page"]


class Loggable(Protocol):
	def file_write(self, path: Path, content: str, method: str) -> None: ...


HttpMethod: TypeAlias = Literal["GET", "POST", "DELETE", "PATCH", "PUT"]
FetchMethod: TypeAlias = Literal["GET", "POST"]


@singleton
class CodeMaoClient:
	def __init__(self) -> None:
		"""初始化客户端实例，增强配置管理"""
		self._session = requests.Session()
		self._config = data.SettingManager().data
		self._processor = tool.CodeMaoProcess()
		self._file: Loggable = file.CodeMaoFile()

		self.base_url = "https://api.codemao.cn"
		self.headers = self._config.PROGRAM.HEADERS.copy()
		self.tool_process = tool.CodeMaoProcess()
		LOG_DIR.mkdir(parents=True, exist_ok=True)

	def send_request(
		self,
		endpoint: str,
		method: HttpMethod,
		params: dict | None = None,
		payload: dict | None = None,
		headers: dict | None = None,
		retries: int = 3,
		backoff_factor: float = 0.3,
		timeout: float = 10.0,
		log: bool = True,
	) -> requests.Response:
		"""增强型请求方法，支持重试机制和更安全的超时处理"""
		url = endpoint if endpoint.startswith("http") else f"{self.base_url}{endpoint}"
		merged_headers = {**self.headers, **(headers or {})}

		for attempt in range(retries):
			try:
				response = self._session.request(method=method, url=url, headers=merged_headers, params=params, json=payload, timeout=timeout)
				response.raise_for_status()
				if log:
					self._log_request(response)
				return response
			except HTTPError as e:
				self._log_error(e.response, f"HTTP Error {e.response.status_code}")
				if e.response.status_code in (429, 503):
					time.sleep(2**attempt * backoff_factor)
					continue
				break
			except (ReqConnectionError, Timeout) as e:
				print(f"Network error ({type(e).__name__}): {e}")
				if attempt == retries - 1:
					raise
				time.sleep(2**attempt * backoff_factor)
			except RequestException as e:
				print(f"Request failed: {type(e).__name__} - {e}")
				break
		return cast(requests.Response, None)

	def fetch_data(
		self,
		endpoint: str,
		params: dict,
		payload: dict | None = None,
		limit: int | None = None,
		fetch_method: FetchMethod = "GET",
		total_key: str = "total",
		data_key: str = "items",
		pagination_method: Literal["offset", "page"] = "offset",
		args: dict[
			Literal["amount", "remove", "res_amount_key", "res_remove_key"],
			Literal["limit", "offset", "page", "current_page", "page_size"],
		] = {},
	) -> list[dict]:
		"""分页获取数据.
		:param endpoint: 请求的 URL.
		:param params: URL 参数.
		:param data: 请求体数据.
		:param limit: 获取数据的最大数量.
		:param fetch_method: 获取数据的方法,如 "get" 或 "post".
		:param total_key: 总数据量的键.
		:param data_key: 数据项的键.
		:param method: 分页方法,如 "offset" 或 "page".
		:param args: 分页参数的键.
		:return: 数据列表.
		"""

		# 设置默认分页参数
		args.setdefault("amount", "limit")
		args.setdefault("remove", "offset")
		args.setdefault("res_amount_key", "limit")
		args.setdefault("res_remove_key", "offset")

		# 第一次请求获取数据和总项数
		initial_response = self.send_request(endpoint=endpoint, method=fetch_method, params=params, payload=payload)
		if not initial_response:
			return []

		# 获取数据并解析总项数
		initial_json = initial_response.json()
		_data = self.tool_process.get_nested_value(initial_json, data_key)
		total_items = int(cast(str, self.tool_process.get_nested_value(initial_json, total_key)))

		# 每次获取多少个
		items_per_page = params.get(args["amount"], initial_json.get(args["res_amount_key"], 0))

		# 计算总页数
		total_pages = (total_items + items_per_page - 1) // items_per_page  # 向下取整
		all_data = []
		all_data.extend(_data)  # 已经包含第一页数据
		fetch_count = len(_data)  # 初始获取的数据数量

		# 如果有更多数据,继续分页请求
		for page in range(1, total_pages):  # 从第二页开始获取
			if pagination_method == "offset":
				params[args["remove"]] = page * items_per_page
			elif pagination_method == "page":
				params[args["remove"]] = page + 1

			# 请求分页数据
			response = self.send_request(endpoint=endpoint, method=fetch_method, params=params)
			if not response:
				continue

			_data = self.tool_process.get_nested_value(response.json(), data_key)
			all_data.extend(_data)
			fetch_count += len(_data)

			# 如果已经达到 limit,提前结束
			if limit and fetch_count >= limit:
				return all_data[:limit]

		return all_data

	def update_cookies(self, cookies: RequestsCookieJar | dict) -> None:
		"""类型安全的Cookie更新方法"""
		# if isinstance(cookies, str):
		# 	self._session.cookies.update(requests.utils.cookiejar_from_dict(self._processor.convert_cookie_to_str(cookies)))
		if isinstance(cookies, dict):
			self._session.cookies.update(cookies)
		elif isinstance(cookies, RequestsCookieJar):
			self._session.cookies = cookies
		else:
			raise TypeError(f"Unsupported cookie type: {type(cookies).__name__}")

	def _log_request(self, response: requests.Response) -> None:
		"""结构化日志记录"""
		log_entry = {
			"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
			"method": response.request.method,
			"url": response.url,
			"status": response.status_code,
			"request_headers": dict(response.request.headers),
			"response_headers": dict(response.headers),
			"response_size": len(response.content),
		}

		self._file.file_write(path=LOG_FILE_PATH, content=json.dumps(log_entry, ensure_ascii=False) + "\n", method="a")

	def _log_error(self, response: requests.Response | None, error_msg: str) -> None:
		"""统一错误日志处理"""
		error_info = {
			"error": error_msg,
			"url": response.url if response else "Unknown",
			"status": response.status_code if response else 0,
			"response": response.text[:200] + "..." if response else "",
		}
		print(f"API Error: {json.dumps(error_info, ensure_ascii=False)}")

	@staticmethod
	def _get_default_pagination_config(method: str) -> PaginationConfig:
		"""获取分页参数默认配置"""
		return {
			"amount_key": "limit" if method == "GET" else "page_size",
			"offset_key": "offset" if method == "GET" else "current_page",
			"response_amount_key": "limit",
			"response_offset_key": "offset",
		}
