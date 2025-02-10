from collections.abc import Generator
from typing import Literal

from src.utils import acquire, tool
from src.utils.acquire import HTTPSTATUS
from src.utils.decorator import singleton


@singleton
class Routine:
	# 初始化方法，创建CodeMaoClient和CodeMaoProcess对象
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()
		self.tool_process = tool.CodeMaoProcess()

	# 登录方法，传入用户名、密码、key和code，发送POST请求，更新cookies
	def login(self, username: str, password: str, key: int, code: str) -> None:
		data = {"username": username, "password": password, "key": key, "code": code}
		response = self.acquire.send_request(endpoint="https://api-whale.codemao.cn/admins/login", method="POST", payload=data)
		self.acquire.update_cookies(response.cookies)

	# 登出方法，发送DELETE请求，返回状态码是否为204
	def logout(self) -> bool:
		response = self.acquire.send_request(endpoint="https://api-whale.codemao.cn/admins/logout", method="DELETE", payload={})
		return response.status_code == HTTPSTATUS.NO_CONTENT

	# 获取数据信息方法，发送GET请求，返回json数据
	def get_data_info(self) -> dict:
		response = self.acquire.send_request(endpoint="https://api-whale.codemao.cn/admins/info", method="GET")
		return response.json()


@singleton
class Obtain:
	def __init__(self) -> None:
		# 初始化获取数据客户端
		self.acquire = acquire.CodeMaoClient()
		# 初始化工具处理
		self.tool_process = tool.CodeMaoProcess()

	# 获取编程作品举报
	def get_work_report(
		self,
		types: Literal["KITTEN", "BOX2", "ALL"],
		status: Literal["TOBEDONE", "DONE", "ALL"],
		target_id: int,
		method: Literal["admin_id", "work_user_id", "work_id"],
		limit: int | None = 15,
	) -> Generator:
		# 构造请求参数
		params = {"type": types, "status": status, method: target_id, "offset": 0, "limit": limit}
		# 获取数据
		return self.acquire.fetch_data(endpoint="https://api-whale.codemao.cn/reports/works/search", params=params, limit=limit)

	# 获取评论举报
	def get_comment_report(
		self,
		types: Literal["ALL", "KITTEN", "BOX2", "FICTION", "COMIC", "WORK_SUBJECT"],
		status: Literal["TOBEDONE", "DONE", "ALL"],
		target_id: int,
		method: Literal["admin_id", "comment_user_id", "comment_id"],
		limit: int | None = 15,
	) -> Generator:
		params = {"source": types, "status": status, method: target_id, "offset": 0, "limit": limit}
		# url可以为https://api-whale.codemao.cn/reports/comments/search
		# 或者https://api-whale.codemao.cn/reports/comments
		return self.acquire.fetch_data(endpoint="https://api-whale.codemao.cn/reports/comments/search", params=params, limit=limit)

	# 获取帖子举报
	def get_post_report(
		self,
		status: Literal["TOBEDONE", "DONE", "ALL"],
		target_id: int,
		method: Literal["post_id"],
		limit: int | None = 15,
	) -> Generator:
		params = {"status": status, method: target_id, "offset": 0, "limit": limit}
		return self.acquire.fetch_data(endpoint="https://api-whale.codemao.cn/reports/posts", params=params, limit=limit)

	# 获取回复与评论举报
	def get_reply_report(
		self,
		status: Literal["TOBEDONE", "DONE", "ALL"],
		target_id: int,
		method: Literal["post_id"],
		limit: int | None = 15,
	) -> Generator:
		params = {"status": status, method: target_id, "offset": 0, "limit": limit}
		return self.acquire.fetch_data(endpoint="https://api-whale.codemao.cn/reports/posts/discussions", params=params, limit=limit)
