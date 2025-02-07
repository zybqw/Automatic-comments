import json
import time
from pathlib import Path
from typing import Literal, TypedDict, cast

import requests
import requests.cookies
from requests.exceptions import ConnectionError as req_ConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout

from . import data, file, tool
from .decorator import singleton

LOG_DIR: Path = Path().cwd() / "log"
LOG_FILE_PATH: Path = LOG_DIR / f"{int(time.time())}.txt"


class PaginationArgs(TypedDict, total=False):
	amount: Literal["limit", "page_size", "current_page"]
	remove: Literal["offset", "page", "current_page", "page_size"]
	res_amount_key: Literal["limit", "page_size"]
	res_remove_key: Literal["offset", "page", "current_page"]


@singleton
class CodeMaoClient:
	def __init__(self) -> None:
		"""初始化 CodeMaoClient 实例,设置基本的请求头和基础 URL."""
		self.session = requests.Session()
		self.data = data.CodeMaoSettingManager().get_data()
		self.tool_process = tool.CodeMaoProcess()
		self.file = file.CodeMaoFile()
		self.HEADERS: dict = self.data.PROGRAM.HEADERS.copy()
		self.BASE_URL: str = "https://api.codemao.cn"

		# Ensure log directory exists
		LOG_DIR.mkdir(parents=True, exist_ok=True)

	def send_request(
		self,
		url: str,
		method: Literal["post", "get", "delete", "patch", "put"],
		params: dict | None = None,
		data: dict | None = None,
		headers: dict | None = None,
		sleep: float = 0.1,
		*,
		log: bool = True,
	) -> requests.Response:
		"""发送 HTTP 请求.

		:param url: 请求的 URL.
		:param method: 请求的方法,如 "post", "get", "delete", "patch", "put".
		:param params: URL 参数.
		:param data: 请求体数据.
		:param headers: 请求头.
		:param sleep: 请求前的等待时间(秒).
		:return: 响应对象或 None(如果请求失败).
		"""
		final_url = url if url.startswith("http") else f"{self.BASE_URL}{url}"
		final_headers = {**self.HEADERS, **(headers or {})}
		# final_headers = headers if headers else self.HEADERS
		time.sleep(sleep)
		response = None
		try:
			response = self.session.request(
				method=method.upper(),
				url=final_url,
				headers=final_headers,
				params=params,
				data=json.dumps(data) if data else None,
				# 如果 data 参数为 None,这会导致整个请求体变成 "null" 字符串
			)
			response.raise_for_status()
		except HTTPError as err:
			self._log_error(err.response, "HTTP Error")
		except req_ConnectionError as err:
			print(f"Connection failed: {err}")
		except Timeout as err:
			print(f"Request timed out: {err}")
		except RequestException as err:
			print(f"Request failed: {err}")
		else:
			if log and response is not None:
				self._log_request(response)
			return cast(requests.Response, response)
		return cast(requests.Response, None)

	def _log_request(self, response: requests.Response) -> None:
		"""Log request details to file."""
		log_content = [
			"*" * 100,
			f"Request URL: {response.url}",
			f"Method: {response.request.method}",
			f"Status Code: {response.status_code}",
			f"Request Headers: {response.request.headers}",
			f"Request Body: {response.request.body}",
			f"Response Headers: {response.headers}",
			f"Response Body: {response.text}",
			"\n",
		]
		self.file.file_write(
			path=LOG_FILE_PATH,
			content="\n".join(log_content),
			method="a",
		)

	def _log_error(self, response: requests.Response | None, error_type: str) -> None:
		"""Log error details."""
		if response is not None:
			print(f"{error_type}: [{response.status_code}] {response.reason} - {response.text}")
			print(response.request.headers)
			print(response.request.body)
		else:
			print(f"{error_type}: No response received")

	def fetch_data(
		self,
		url: str,
		params: dict,
		data: dict | None = None,
		limit: int | None = None,
		fetch_method: Literal["get", "post"] = "get",
		total_key: str = "total",
		data_key: str = "items",
		pagination_method: Literal["offset", "page"] = "offset",
		args: dict[
			Literal["amount", "remove", "res_amount_key", "res_remove_key"],
			Literal["limit", "offset", "page", "current_page", "page_size"],
		] = {},
	) -> list[dict]:
		"""分页获取数据.
		:param url: 请求的 URL.
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
		initial_response = self.send_request(url=url, method=fetch_method, params=params, data=data)
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
			response = self.send_request(url=url, method=fetch_method, params=params)
			if not response:
				continue

			_data = self.tool_process.get_nested_value(response.json(), data_key)
			all_data.extend(_data)
			fetch_count += len(_data)

			# 如果已经达到 limit,提前结束
			if limit and fetch_count >= limit:
				return all_data[:limit]

		return all_data

	def update_cookie(self, cookie: requests.cookies.RequestsCookieJar | dict | str) -> bool:
		"""Update session cookies.

		Args:
			cookie: Cookies to add to the session

		Returns:
			True if cookies were updated successfully
		"""

		if isinstance(cookie, dict | requests.cookies.RequestsCookieJar):
			self.session.cookies.update(cookie)
		else:
			msg = "Unsupported cookie type"
			raise TypeError(msg)
		# match cookie:
		# 	case requests.cookies.RequestsCookieJar():
		# 		cookie_dict = requests.utils.dict_from_cookiejar(cookie)
		# 		cookie_str = self.tool_process.convert_cookie_to_str(cookie_dict)
		# 	case dict():
		# 		cookie_dict = cookie
		# 		cookie_str = self.tool_process.convert_cookie_to_str(cookie_dict)
		# 	case str():
		# 		cookie_str = cookie
		# 	case _:
		# 		msg = "不支持的cookie类型"
		# 		raise ValueError(msg)
		# self.HEADERS.update({"Cookie": cookie_str})
		return True
