import time
from os import getcwd, path
from typing import Literal, cast

import requests
import requests.cookies
import requests.utils
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from . import data as Data
from . import file as File
from . import tool as Tool
from .decorator import singleton

session = requests.session()

LOG_FILE_PATH: str = path.join(getcwd(), "log", f"{int(time.time())}.txt")


@singleton
class CodeMaoClient:
	def __init__(self) -> None:
		"""初始化 CodeMaoClient 实例,设置基本的请求头和基础 URL."""
		self.data = Data.CodeMaoSetting()
		self.tool_process = Tool.CodeMaoProcess()
		self.file = File.CodeMaoFile()
		self.HEADERS: dict = self.data.setting["PROGRAM"]["HEADERS"]
		self.BASE_URL: str = "https://api.codemao.cn"
		global session  # noqa: PLW0602

	def send_request(
		self,
		url: str,
		method: Literal["post", "get", "delete", "patch", "put"],
		params=None,
		data=None,
		headers=None,
		sleep=0,
		log: Literal[True, False] = True,
	):
		"""
		发送 HTTP 请求.

		:param url: 请求的 URL.
		:param method: 请求的方法,如 "post", "get", "delete", "patch", "put".
		:param params: URL 参数.
		:param data: 请求体数据.
		:param headers: 请求头.
		:param sleep: 请求前的等待时间(秒).
		:return: 响应对象或 None(如果请求失败).
		"""
		headers = headers or self.HEADERS
		url = url if "http" in url else f"{self.BASE_URL}{url}"
		time.sleep(sleep)
		try:
			response = session.request(method=method, url=url, headers=headers, params=params, data=data)
			response.raise_for_status()
			if log:
				log_content = [
					"*" * 100,
					f"请求url: {response.url}",
					f"请求方法: {response.request.method}",
					f"状态码: {response.status_code}",
					f"请求头: {response.request.headers}",
					f"请求体: {response.request.body}",
					f"响应头: {response.headers}",
					f"响应体: {response.text}",
				]
				self.file.file_write(path=LOG_FILE_PATH, content=log_content, method="a")

			return response
		except (HTTPError, ConnectionError, Timeout, RequestException) as err:
			print(f"网络请求异常: {err}")
			response = cast(requests.Response, None)
			if response:
				print(f"错误码: {response.status_code} 错误原因: {response.reason} 错误信息: {response.text}")  # type: ignore
			return response

	def fetch_data(
		self,
		url: str,
		params: dict,
		data=None,
		limit: int | None = None,
		fetch_method: Literal["get", "post"] = "get",
		total_key: str = "total",
		data_key: str | None = "item",
		method: Literal["offset", "page"] = "offset",
		args: dict[Literal["amount", "remove", "res_amount_key", "res_remove_key"], str] = {
			"amount": "limit",
			"remove": "offset",
			"res_amount_key": "limit",
			"res_remove_key": "offset",
		},
	) -> list[dict]:
		"""
		分页获取数据.

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
		initial_response = self.send_request(url=url, method=fetch_method, params=params, data=data)
		if not initial_response:
			return []

		total_items = int(cast(str, self.tool_process.get_nested_value(initial_response.json(), total_key)))
		items_per_page = (
			params[args["amount"]] if args["amount"] in params else initial_response.json()[args["res_amount_key"]]
		)
		total_pages = (total_items + items_per_page - 1) // items_per_page  # 向上取整
		all_data = []
		fetch_count = 0

		for page in range(total_pages):
			if method == "offset":
				params[args["remove"]] = page * items_per_page
			elif method == "page":
				params[args["remove"]] = page + 1

			response = self.send_request(url=url, method=fetch_method, params=params)
			if not response:
				continue

			data = self.tool_process.get_nested_value(response.json(), data_key)
			all_data.extend(data)
			fetch_count += len(data)
			if limit and fetch_count >= limit:
				return all_data[:limit]

		return all_data

	def update_cookie(self, cookie: requests.cookies.RequestsCookieJar):
		"""
		更新会话的 Cookie.

		:param cookie: 要更新的 Cookie,可以是 RequestsCookieJar、字典或字符串.
		:return: True 如果更新成功.
		:raises ValueError: 如果 cookie 类型不支持.
		"""
		cookie_dict: dict = requests.utils.dict_from_cookiejar(cookie)
		cookie_str: str = self.tool_process.convert_cookie_to_str(cookie_dict)
		self.HEADERS.update({"Cookie": cookie_str})
		session.cookies.update(cookie)
		return True
