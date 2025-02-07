from typing import Any, Literal, cast

from src.base import acquire
from src.base.decorator import singleton

OK_CODE = 200
NO_CONTENT_CODE = 204


@singleton
class Obtain:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	# 获取某人账号信息
	def get_user_details(self, user_id: str) -> dict:
		response = self.acquire.send_request(method="get", url=f"/api/user/info/detail/{user_id}")
		return response.json()

	# 获取用户荣誉
	def get_user_honor(self, user_id: str) -> dict:
		params = {"user_id": user_id}
		response = self.acquire.send_request(
			url="/creation-tools/v1/user/center/honor",
			method="get",
			params=params,
		)

		return response.json()

	# 获取用户精确数据
	def get_user_business(self, user_id: str) -> dict:
		params = {"user_id": user_id}
		response = self.acquire.send_request(url="/nemo/v2/works/business/total", method="get", params=params)
		return response.json()

	# 获取某人账号信息(简略)
	def get_user_info(self, user_id: str) -> dict:
		params = {"user_id": user_id}
		response = self.acquire.send_request(method="get", url="/nemo/v2/user/dynamic/info", params=params)
		return response.json()

	# 获取账户信息(详细)
	def get_data_details(self) -> dict:
		response = self.acquire.send_request(
			method="get",
			url="/web/users/details",
		)
		return response.json()

	# BUG 貌似api不起作用
	# 获取账户信息(简略)
	# def get_data_info(self) -> dict:
	# 	response = self.acquire.send_request(
	# 		method="get",
	# 		url="/web/user/info",
	# 	)

	# 	return response.json()

	# 获取账户信息
	def get_data_profile(self, method: Literal["web", "app"]) -> dict:
		response = self.acquire.send_request(method="get", url=f"/tiger/v3/{method}/accounts/profile")
		return response.json()

	# 获取账户安全信息
	def get_data_privacy(self) -> dict:
		response = self.acquire.send_request(method="get", url="/tiger/v3/web/accounts/privacy")
		return response.json()

	# 获取账户信息
	def get_data_tiger(self) -> dict:
		response = self.acquire.send_request(url="/tiger/user", method="get")
		return response.json()

	# 获取用户点赞,再创作,收藏分
	def get_data_score(self) -> dict:
		response = self.acquire.send_request(url="/nemo/v3/user/grade/details", method="get")
		return response.json()

	# 获取用户等级
	def get_data_level(self) -> dict:
		response = self.acquire.send_request(url="/nemo/v3/user/level/info", method="get")
		return response.json()

	# 获取用户姓名
	def get_data_name(self) -> dict:
		response = self.acquire.send_request(url="/api/v2/pc/lesson/user/info", method="get")
		print(response)
		return response.json()

	# 获取个人作品列表的函数
	def get_user_works_web(self, user_id: str, types: Literal["newest", "hot"] = "newest", limit: int | None = 5) -> list[dict[str, str | int]]:
		params = {
			"type": types,
			"user_id": user_id,
			"offset": 0,
			"limit": 5,
		}
		return self.acquire.fetch_data(
			url="/creation-tools/v2/user/center/work-list",
			params=params,
			total_key="total",
			data_key="items",
			limit=limit,
		)

	# 搜索用户作品
	def search_data_works_nemo(self, query: str, query_type: str = "name", page: int = 1, limit: int = 10) -> dict:
		params = {
			"query": query,
			"query_type": query_type,
			"page": page,
			"limit": limit,
		}
		response = self.acquire.send_request(url="tiger/nemo/user/works/search", method="get", params=params)
		return response.json()

	# 获取用户云端作品
	def get_works_cloud(self, types: Literal["nemo", "kitten"], limit: int = 10, offset: int = 0) -> dict:
		if types == "nemo":
			work_type = 8
		elif types == "kitten":
			work_type = 1
		params = {"limit": limit, "offset": offset, "work_type": work_type}
		response = self.acquire.send_request(url="/creation-tools/v1/works/list/user", params=params, method="get")
		return response.json()

	# 获取用户nemo作品
	def get_works_nemo_published(self, method: Literal["published"], limit: int | None = 15) -> list[dict[Any, Any]]:
		params = {"limit": 15, "offset": 0}
		return self.acquire.fetch_data(
			url=f"/nemo/v2/works/list/user/{method}",
			params=params,
			data_key="items",
			limit=limit,
		)

	# 获取用户KN作品
	def get_works_kn(
		self,
		method: Literal["published", "total"],
		extra_params: (
			dict[
				Literal["name", "limit", "offset", "status", "work_business_classify"],
				str | int,
			]
			| None
		) = None,
		limit: int | None = 15,
	) -> list[dict[Any, Any]]:
		# kn获取全部作品示例链接:https://api-creation.codemao.cn/neko/works/v2/list/user?name=&limit=24&offset=0&status=1&work_business_classify=1
		if method == "published":
			url = "https://api-creation.codemao.cn/neko/works/list/user/published"
		elif method == "total":
			url = "https://api-creation.codemao.cn/neko/works/v2/list/user"
		params = {"offset": 0, "limit": 15}
		params = cast(dict, params)
		params.update(extra_params or {})
		return self.acquire.fetch_data(url=url, params=params, data_key="items", limit=limit)

	# 获取用户kitten作品列表
	def get_works_kitten(
		self,
		version: Literal["KITTEN_V4", "KITTEN_V3"],
		status: Literal["PUBLISHED", "UNPUBLISHED", "all"],
		work_status: Literal["SHOW"] = "SHOW",
		limit: int | None = 30,
	) -> list[dict[Any, Any]]:
		params = {
			"offset": 0,
			"limit": 30,
			"version_no": version,
			"work_status": work_status,
			"published_status": status,
		}
		return self.acquire.fetch_data(
			url="https://api-creation.codemao.cn/kitten/common/work/list2",
			params=params,
			data_key="items",
			limit=limit,
		)

	# 获取用户nemo作品列表
	def get_works_nemo(self, status: Literal["PUBLISHED", "UNPUBLISHED", "all"], limit: int | None = 30) -> list[dict[Any, Any]]:
		params = {"offset": 0, "limit": 30, "published_status": status}
		return self.acquire.fetch_data(
			url="/creation-tools/v1/works/list",
			params=params,
			data_key="items",
			limit=limit,
		)

	# 获取用户海龟编辑器作品列表
	def get_works_wood(
		self,
		status: Literal["PUBLISHED", "UNPUBLISHED"],
		language_type: int = 0,
		work_status: Literal["SHOW"] = "SHOW",
		limit: int | None = 30,
	) -> list[dict[Any, Any]]:
		params = {
			"offset": 0,
			"limit": 30,
			"language_type": language_type,
			"work_status": work_status,
			"published_status": status,
		}
		return self.acquire.fetch_data(
			url="https://api-creation.codemao.cn/wood/comm/work/list",
			params=params,
			data_key="items",
			limit=limit,
		)

	# 获取用户box作品列表
	def get_works_box(self, status: Literal["all", "PUBLISHED", "UNPUBLISHED"], work_status: Literal["SHOW"] = "SHOW", limit: int | None = 30) -> list[dict[Any, Any]]:
		params = {
			"offset": 0,
			"limit": 30,
			"work_status": work_status,
			"published_status": status,
		}
		return self.acquire.fetch_data(
			url="https://api-creation.codemao.cn/box/v2/work/list",
			params=params,
			data_key="items",
			limit=limit,
		)

	# 获取用户小说列表
	def get_works_fanfic(self, fiction_status: Literal["SHOW"] = "SHOW", limit: int | None = 30) -> list[dict[Any, Any]]:
		params = {"offset": 0, "limit": 30, "fiction_status": fiction_status}
		return self.acquire.fetch_data(
			url="/web/fanfic/my/new",
			params=params,
			data_key="items",
			limit=limit,
		)

	# 获取用户coco作品列表
	# TODO@Aurzex: 参数不确定
	def get_works_coco(self, status: int = 1, *, published: bool = True, limit: int | None = 30) -> list[dict[Any, Any]]:
		params = {
			"offset": 0,
			"limit": 30,
			"status": status,
			"published": published,
		}
		return self.acquire.fetch_data(
			url="https://api-creation.codemao.cn/coconut/web/work/list",
			params=params,
			data_key="data.items",
			total_key="data.total",
			limit=limit,
		)

	# 获取粉丝列表
	def get_user_fans(self, user_id: str, limit: int = 15) -> list[dict[str, str]]:
		params = {
			"user_id": user_id,
			"offset": 0,
			"limit": 15,
		}
		return self.acquire.fetch_data(
			url="/creation-tools/v1/user/fans",
			params=params,
			total_key="total",
			data_key="items",
			limit=limit,
		)

	# 获取关注列表
	def get_user_follows(self, user_id: str, limit: int = 15) -> list[dict[str, str]]:
		params = {
			"user_id": user_id,
			"offset": 0,
			"limit": 15,
		}
		return self.acquire.fetch_data(
			url="/creation-tools/v1/user/followers",
			params=params,
			total_key="total",
			data_key="items",
			limit=limit,
		)

	# 获取用户收藏的作品的信息
	def get_user_collects(self, user_id: str, limit: int = 5) -> list[dict[str, str]]:
		params = {
			"user_id": user_id,
			"offset": 0,
			"limit": 5,
		}
		return self.acquire.fetch_data(
			url="/creation-tools/v1/user/center/collect/list",
			params=params,
			total_key="total",
			data_key="items",
			limit=limit,
		)

	# 获取用户头像框列表
	def get_user_avatar_frame(self) -> dict:
		response = self.acquire.send_request(
			url="/creation-tools/v1/user/avatar-frame/list",
			method="get",
		)
		return response.json()

	# 获取用户是否为新用户
	def get_is_new_user(self) -> dict:
		response = self.acquire.send_request(url="https://api-creation.codemao.cn/neko/works/isNewUser", method="get")
		return response.json()


@singleton
class Motion:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	# 设置正在做的事
	def set_data_doing(self, doing: str) -> bool:
		response = self.acquire.send_request(url="/nemo/v2/user/basic", method="put", data={"doing": doing})
		return response.status_code == OK_CODE

	# 设置登录用户名(实验性功能)
	def set_data_username(self, username: str) -> bool:
		response = self.acquire.send_request(
			url="/tiger/v3/web/accounts/username",
			method="patch",
			data={"username": username},
		)
		return response.status_code == NO_CONTENT_CODE

	# 验证手机号
	def verify_phone(self, phone_num: int) -> dict:
		params = {"phone_number": phone_num}
		response = self.acquire.send_request(url="/web/users/phone_number/is_consistent", method="get", params=params)
		return response.json()

	# 修改密码
	def modify_password(self, old_password: str, new_password: str) -> bool:
		data = {
			"old_password": old_password,
			"password": new_password,
			"confirm_password": new_password,
		}
		response = self.acquire.send_request(
			url="/tiger/v3/web/accounts/password",
			method="patch",
			data=data,
		)
		return response.status_code == NO_CONTENT_CODE

	# 修改手机号(获取验证码)
	def modify_phonenum_captcha(self, old_phonenum: int, new_phonenum: int) -> bool:
		data = {"phone_number": new_phonenum, "old_phone_number": old_phonenum}
		response = self.acquire.send_request(
			url="/tiger/v3/web/accounts/captcha/phone/change",
			method="post",
			data=data,
		)
		return response.status_code == NO_CONTENT_CODE

	# 修改手机号
	def modify_phonenum(self, captcha: int, phonenum: int) -> bool:
		data = {"phone_number": phonenum, "captcha": captcha}
		response = self.acquire.send_request(
			url="/tiger/v3/web/accounts/phone/change",
			method="patch",
			data=data,
		)
		return response.json()

	# 设置nemo头像,昵称,个性签名
	def set_nemo_basic(self, nickname: str, description: str) -> bool:
		data = {key: value for key, value in [("nickname", nickname), ("description", description)] if value is not None}
		if not data:
			msg = "至少需要传入一个参数"
			raise ValueError(msg)
		response = self.acquire.send_request(url="/nemo/v2/user/basic", method="put", data=data)
		return response.status_code == OK_CODE

	# 取消设置头像框
	def cancel_avatar_frame(self) -> bool:
		response = self.acquire.send_request(
			url="/creation-tools/v1/user/avatar-frame/cancel",
			method="put",
		)
		return response.status_code == OK_CODE

	# 设置头像框
	# id 2,3,4 代表Lv2,3,4头像框
	def set_avatar_frame(self, frame_id: Literal[2, 3, 4]) -> bool:
		response = self.acquire.send_request(
			url=f"/creation-tools/v1/user/avatar-frame/{frame_id}",
			method="put",
		)
		return response.status_code == OK_CODE

	# 设置info
	# birthday值为timestamp
	# sex中0为女,1为男
	# /tiger/v3/web/accounts/info
	def set_data_info(
		self,
		avatar_url: str,
		nickname: str,
		birthday: int,
		description: str,
		fullname: str,
		qq: str,
		sex: Literal[0, 1],
	) -> bool:
		data = {
			"avatar_url": avatar_url,
			"nickname": nickname,
			"birthday": birthday,
			"description": description,
			"fullname": fullname,
			"qq": qq,
			"sex": sex,
		}
		response = self.acquire.send_request(
			url="/tiger/v3/web/accounts/info",
			method="patch",
			data=data,
		)
		return response.status_code == NO_CONTENT_CODE
