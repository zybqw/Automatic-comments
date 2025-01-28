import json
from typing import Any, Literal

from src.base import acquire
from src.base.decorator import singleton

OK_CODE = 200
CREATED_CODE = 201
NO_CONTENT_CODE = 204


@singleton
class Obtain:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	# 获取工作室简介(简易,需登录工作室成员账号)
	# def get_shops_info(self):
	# 	response = self.acquire.send_request(url="/web/work_shops/simple", method="get")
	# 	# return response.json()["work_shop"]
	# 	return response.json()
	# 2025/1/22 发现api变为410错误代码

	# 获取工作室简介
	# 返回的值中id为常用的id,在函数中未特别注明均用该值,shop_id在引用中改为relation_id,label_id不变
	def get_shop_details(self, shop_id: str) -> dict:
		response = self.acquire.send_request(url=f"/web/shops/{shop_id}", method="get")
		return response.json()

	# 获取工作室列表的函数
	def get_shops(
		self,
		level: int = 4,
		limit: int = 14,
		works_limit: int = 4,
		offset: int = 0,
		sort: list[Literal["-latest_joined_at", "-created_at"]] = [
			"-created_at",
			"-latest_joined_at",
		],
	) -> dict:  # 不要问我limit默认值为啥是14,因为api默认获取14个
		if isinstance(sort, list):
			_sort = ",".join(sort)
		params = {
			"level": level,
			"works_limit": works_limit,
			"limit": limit,
			"offset": offset,
			"sort": _sort,
		}
		response = self.acquire.send_request(
			url="/web/work-shops/search",
			params=params,
			method="get",
		)
		return response.json()

	# 获取工作室成员
	def get_shops_members(
		self,
		shop_id: int,
	) -> list[dict[Any, Any]]:
		params = {"limit": 40, "offset": 0}
		return self.acquire.fetch_data(
			url=f"/web/shops/{shop_id}/users",
			params=params,
			total_key="total",
			data_key="items",
		)

	# 获取工作室列表,包括工作室成员,工作室作品
	def get_shops_details(
		self,
		levels: list[int] | int = [1, 2, 3, 4],
		max_number: int = 4,
		works_limit: int = 4,
		sort: list[str] | str = ["-ordinal,-updated_at"],
	) -> dict:
		_levels: str = ""
		_sort: str = ""
		if isinstance(levels, list):
			_levels = ",".join(map(str, levels))
		if isinstance(sort, list):
			_sort = ",".join(sort)
		params = {
			"levels": _levels,
			"max_number": max_number,
			"works_limit": works_limit,
			"sort": _sort,
		}
		response = self.acquire.send_request(url="/web/shops", method="get", params=params)
		return response.json()

	# 获取工作室讨论
	def get_shop_discussion(self, shop_id: int, source: Literal["WORK_SHOP"] = "WORK_SHOP", sort: Literal["-created_at"] = "-created_at", limit: int | None = 15) -> list[dict]:
		params = {"source": source, "sort": sort, "limit": 20, "offset": 0}
		return self.acquire.fetch_data(url=f"/web/discussions/{shop_id}/comments", params=params, limit=limit, data_key="items")

	# 获取工作室投稿作品
	def get_shop_works(self, shop_id: int, user_id: int, sort: str = "-created_at,-id") -> list[dict[Any, Any]]:
		params = {"limit": 20, "offset": 0, "sort": sort, "user_id": user_id, "work_subject_id": shop_id}
		return self.acquire.fetch_data(url=f"/web/works/subjects/{shop_id}/works", params=params, data_key="items")

	# 获取与工作室关系
	def get_shop_relation(self, relation_id: int) -> dict:
		params = {"id": relation_id}
		response = self.acquire.send_request(url="/web/work_shops/users/relation", method="get", params=params)
		return response.json()

	# 获取工作室讨论区的帖子
	def get_shop_posts(self, label_id: int) -> list[dict]:
		params = {"limit": 20, "offset": 0}
		return self.acquire.fetch_data(url=f"/web/works/subjects/labels/{label_id}/posts", params=params, data_key="items")


@singleton
class Motion:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	# 更新工作室简介
	def update_shop_details(self, description: str, shop_id: str, name: str, preview_url: str) -> bool:
		response = self.acquire.send_request(
			url="/web/work_shops/update",
			method="post",
			data=json.dumps(
				{
					"description": description,
					"id": shop_id,
					"name": name,
					"preview_url": preview_url,
				},
			),
		)
		return response.status_code == OK_CODE

	# 创建工作室
	def create_shop(self, name: str, description: str, preview_url: str) -> dict:
		response = self.acquire.send_request(
			url="/web/work_shops/create",
			method="post",
			data=json.dumps(
				{
					"name": name,
					"description": description,
					"preview_url": preview_url,
				},
			),
		)
		return response.json()

	# 解散工作室
	def dissolve_shop(self, shop_id: int) -> bool:
		response = self.acquire.send_request(
			url="/web/work_shops/dissolve",
			method="post",
			data=json.dumps({"id": shop_id}),
		)
		return response.status_code == OK_CODE

	# 在指定工作室投稿作品
	def contribute_work(self, shop_id: int, work_id: int) -> bool:
		response = self.acquire.send_request(
			url="/web/work_shops/works/contribute",
			method="post",
			data=json.dumps({"id": shop_id, "work_id": work_id}),
		)
		return response.status_code == OK_CODE

	# 在指定工作室删除作品
	def remove_work(self, shop_id: int, work_id: int) -> bool:
		response = self.acquire.send_request(
			url="/web/work_shops/works/remove",
			method="post",
			data=json.dumps({"id": shop_id, "work_id": work_id}),
		)
		return response.status_code == OK_CODE

	# 申请加入工作室
	def apply_join(self, shop_id: int, qq: str | None = None) -> bool:
		response = self.acquire.send_request(
			url="/web/work_shops/users/apply/join",
			method="post",
			data=json.dumps({"id": shop_id, "qq": qq}),
		)
		return response.status_code == OK_CODE

	# 审核已经申请加入工作室的用户
	def audit_join(self, shop_id: int, status: Literal["UNACCEPTED", "ACCEPTED"], user_id: int) -> bool:
		response = self.acquire.send_request(
			url="/web/work_shops/users/audit",
			method="post",
			data=json.dumps({"id": shop_id, "status": status, "user_id": user_id}),
		)
		return response.status_code == OK_CODE

	# 举报讨论区下的评论
	def report_comment(
		self,
		comment_id: int,
		comment_parent_id: int,
		description: str,
		reason_content: str,
		reason_id: int,
		reporter_id: int,
		comment_source: Literal["WORK_SHOP"] = "WORK_SHOP",
	) -> bool:
		response = self.acquire.send_request(
			url="/web/reports/comments",
			method="post",
			data=json.dumps(
				{
					"comment_id": comment_id,
					"comment_parent_id": comment_parent_id,
					"description": description,
					"reason_content": reason_content,
					"reason_id": reason_id,
					"reporter_id": reporter_id,
					"comment_source": comment_source,
				},
			),
		)
		return response.status_code == CREATED_CODE

	# 回复评论
	# parent_id貌似只能为0
	def reply_work(self, shop_id: int, comment_id: int, content: str, source: Literal["WORK_SHOP"] = "WORK_SHOP", parent_id: int = 0, *, return_data: bool = False) -> bool:
		response = self.acquire.send_request(
			url=f"/web/discussions/{shop_id}/comments/{comment_id}/reply",
			method="post",
			data=json.dumps(
				{
					"parent_id": parent_id,
					"content": content,
					"source": source,
				},
			),
		)
		return response.json() if return_data else response.status_code == CREATED_CODE

	# 删除回复
	def delete_reply(self, comment_id: int, source: Literal["WORK_SHOP"] = "WORK_SHOP") -> bool:
		response = self.acquire.send_request(
			url=f"/web/discussions/replies/{comment_id}",
			method="delete",
			params={"source": source},
		)
		return response.status_code == NO_CONTENT_CODE

	# 评论
	def comment_work(self, shop_id: int, content: str, rich_content: str, source: Literal["WORK_SHOP"] = "WORK_SHOP", *, return_code: bool = False) -> bool:
		response = self.acquire.send_request(
			url=f"/web/discussions/{shop_id}/comment",
			method="post",
			data=json.dumps(
				{
					"content": content,
					"rich_content": rich_content,
					"source": source,
				},
			),
		)
		return response.json() if return_code else response.status_code == CREATED_CODE

	# 删除评论
	def delete_comment(self, comment_id: int, source: Literal["WORK_SHOP"] = "WORK_SHOP") -> bool:
		response = self.acquire.send_request(
			url=f"/web/discussions/comments/{comment_id}",
			method="delete",
			params={"source": source},
		)
		return response.status_code == NO_CONTENT_CODE
