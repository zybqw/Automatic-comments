import json
from typing import Any, Literal

from src.base import acquire, data, tool
from src.base.decorator import singleton

OK_CODE = 200
NO_CONTENT_CODE = 204


# 编程猫所有api中若包含v2等字样,表示第几版本,同样比它低的版本也可使用
@singleton
class Login:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()
		self.tool_process = tool.CodeMaoProcess()
		self.setting = data.CodeMaoSetting().setting

	# 密码登录函数
	def login_password(
		self,
		identity: str,
		password: str,
		pid: str = "65edCTyg",
	) -> str | None:
		# cookies = utils.dict_from_cookiejar(response.cookies)

		#   soup = BeautifulSoup(
		#       send_request("https://shequ.codemao.cn", "get").text,
		#       "html.parser",
		#   )
		#   见https://api.docs.codemao.work/user/login?id=pid
		#   pid = loads(soup.find_all("script")[0].string.split("=")[1])["pid"]
		response = self.acquire.send_request(
			url="/tiger/v3/web/accounts/login",
			method="post",
			data=json.dumps(
				{
					"identity": identity,
					"password": password,
					"pid": pid,
				},
			),
		)
		self.acquire.update_cookie(response.cookies)

	# cookie登录
	def login_cookie(self, cookies: str) -> None | bool:
		try:
			dict([item.split("=", 1) for item in cookies.split("; ")])
			# 检查是否合规,不能放到headers中
		except (KeyError, ValueError) as err:
			print(f"表达式输入不合法 {err}")
			return False
		self.acquire.send_request(
			url=self.setting["PARAMETER"]["cookie_check_url"],
			method="post",
			data=json.dumps({}),
			headers={**self.acquire.HEADERS, "cookie": cookies},
		)
		self.acquire.update_cookie(cookies)
		return None

	# token登录(毛毡最新登录方式)
	def login_token(self, identity: str, password: str, pid: str = "65edCTyg") -> None:
		timestamp = Obtain().get_timestamp()["data"]
		response = self.get_login_ticket(identity=identity, timestamp=timestamp, pid=pid)
		ticket = response["ticket"]
		response = self.get_login_security(identity=identity, password=password, ticket=ticket, pid=pid)

	# 返回完整cookie
	def get_login_auth(self, token: str) -> dict[str, Any]:
		# response = self.acquire.send_request(
		# 	url="https://shequ.codemao.cn/",
		# 	method="get",
		# )
		# aliyungf_tc = response.cookies.get_dict()["aliyungf_tc"]
		# 上面这句会自己生成
		# uuid_ca = uuid.uuid1()
		# token_ca = {"authorization": token, "__ca_uid_key__": str(uuid_ca)}
		# 无上面这两句会缺少__ca_uid_key__
		token_ca = {"authorization": token}
		cookie_str = self.tool_process.convert_cookie_to_str(token_ca)
		headers = {**self.acquire.HEADERS, "cookie": cookie_str}
		response = self.acquire.send_request(method="get", url="/web/users/details", headers=headers)
		_auth = response.cookies.get_dict()
		return {**token_ca, **_auth}

	# 退出登录
	def logout(self, method: Literal["web", "app"]) -> bool:
		response = self.acquire.send_request(
			url=f"/tiger/v3/{method}/accounts/logout",
			method="post",
			data=json.dumps({}),
		)
		return response.status_code == NO_CONTENT_CODE

	# 登录信息
	def get_login_security(
		self,
		identity: str,
		password: str,
		ticket: str,
		pid: str = "65edCTyg",
		agreement_ids: list = [-1],
	) -> dict:
		data = json.dumps(
			{
				"identity": identity,
				"password": password,
				"pid": pid,
				"agreement_ids": agreement_ids,
			},
		)
		response = self.acquire.send_request(
			url="/tiger/v3/web/accounts/login/security",
			method="post",
			data=data,
			headers={**self.acquire.HEADERS, "x-captcha-ticket": ticket},
		)
		self.acquire.update_cookie(response.cookies)
		return response.json()

	# 登录ticket获取
	def get_login_ticket(
		self,
		identity: str | int,
		timestamp: int,
		scene: str | None = None,
		pid: str = "65edCTyg",
		deviced: str | None = None,
	) -> dict:
		# 可填可不填
		# uuid_ca = uuid.uuid1()
		# _ca = {"__ca_uid_key__": str(uuid_ca)}
		# cookie_str = self.tool_process.convert_cookie_to_str(_ca)
		# headers = {**self.acquire.HEADERS, "cookie": cookie_str}
		data = json.dumps(
			{
				"identity": identity,
				"scene": scene,
				"pid": pid,
				"deviceId": deviced,
				"timestamp": timestamp,
			},
		)
		response = self.acquire.send_request(
			url="https://open-service.codemao.cn/captcha/rule/v3",
			method="post",
			data=data,
			# headers=headers,
		)
		self.acquire.update_cookie(response.cookies)
		return response.json()


@singleton
class Obtain:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	# 获取随机昵称
	def get_name_random(self) -> str:
		response = self.acquire.send_request(
			method="get",
			url="/api/user/random/nickname",
		)
		return response.json()["data"]["nickname"]

	# 获取新消息数量
	def get_message_count(self, method: Literal["web", "nemo"]) -> dict:
		if method == "web":
			url = "/web/message-record/count"
		elif method == "nemo":
			url = "/nemo/v2/user/message/count"
		else:
			msg = "不支持的方法"
			raise ValueError(msg)
		record = self.acquire.send_request(
			url=url,
			method="get",
		)
		return record.json()

	# 获取回复
	def get_replies(
		self,
		types: Literal["LIKE_FORK", "COMMENT_REPLY", "SYSTEM"],
		limit: int = 15,
		offset: int = 0,
	) -> dict:
		params = {"query_type": types, "limit": limit, "offset": offset}
		# 获取前*个回复
		response = self.acquire.send_request(
			url="/web/message-record",
			method="get",
			params=params,
		)
		return response.json()

	# 获取nemo消息
	def get_nemo_message(self, types: Literal["fork", "like"]) -> dict:
		extra_url = 1 if types == "like" else 3
		url = f"/nemo/v2/user/message/{extra_url}"
		response = self.acquire.send_request(url=url, method="get")
		return response.json()

	# 获取点个猫更新
	def get_update_pickcat(self) -> dict:
		response = self.acquire.send_request(url="https://update.codemao.cn/updatev2/appsdk", method="get")
		return response.json()

	# 获取kitten4更新
	def get_update_kitten4(self) -> dict:
		time_stamp = self.get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(url="https://kn-cdn.codemao.cn/kitten4/application/kitten4_update_info.json", method="get", params=params)
		return response.json()

	# 获取kitten更新
	def get_update_kitten(self) -> dict:
		time_stamp = self.get_timestamp()["data"]
		params = {"timeStamp": time_stamp}
		response = self.acquire.send_request(url="https://kn-cdn.codemao.cn/application/kitten_update_info.json", method="get", params=params)
		return response.json()

	# 获取海龟编辑器更新
	def get_update_wood(self) -> dict:
		time_stamp = self.get_timestamp()["data"]
		params = {"timeStamp": time_stamp}
		response = self.acquire.send_request(url="https://static-am.codemao.cn/wood/client/xp/prod/package.json", method="get", params=params)
		return response.json()

	# 获取源码智造编辑器更新
	def get_update_matrix(self) -> dict:
		time_stamp = self.get_timestamp()["data"]
		params = {"timeStamp": time_stamp}
		response = self.acquire.send_request(url="https://public-static-edu.codemao.cn/matrix/publish/desktop_matrix.json", method="get", params=params)
		return response.json()

	# 获取时间戳
	def get_timestamp(self) -> dict:
		response = self.acquire.send_request(url="/coconut/clouddb/currentTime", method="get")
		return response.json()

	# 获取推荐头图
	def get_banner_web(
		self,
		types: (None | Literal["FLOAT_BANNER", "OFFICIAL", "CODE_TV", "WOKE_SHOP", "MATERIAL_NORMAL"]) = None,
	) -> dict:
		# 所有:不设置type,首页:OFFICIAL, 工作室页:WORK_SHOP
		# 素材页:MATERIAL_NORMAL, 右下角浮动区域:FLOAT_BANNER, 编程TV:CODE_TV
		params = {"type": types}
		response = self.acquire.send_request(url="/web/banners/all", method="get", params=params)
		return response.json()

	# 获取推荐头图
	def get_banner_nemo(self, types: Literal[1, 2, 3]) -> dict:
		# 1:点个猫推荐页 2:点个猫主题页 3:点个猫课程页
		params = {"banner_type": types}
		response = self.acquire.send_request(url="/nemo/v2/home/banners", method="get", params=params)
		return response.json()

	# 获取举报类型
	def get_report_reason(self) -> dict:
		response = self.acquire.send_request(url="/web/reports/reasons/all", method="get")
		return response.json()

	# 获取nemo配置
	# TODO@Aurzex: 待完善
	def get_nemo_config(self) -> str:
		response = self.acquire.send_request(url="https://nemo.codemao.cn/config", method="get")
		return response.json()

	# 获取社区网络服务
	def get_community_config(self) -> dict:
		response = self.acquire.send_request(url="https://c.codemao.cn/config", method="get")
		return response.json()

	# 获取编程猫网络服务
	def get_client_config(self) -> dict:
		response = self.acquire.send_request(url="https://player.codemao.cn/new/client_config.json", method="get")
		return response.json()

	# 获取编程猫首页作品
	def discover_works_recommended_home(self, types: Literal[1, 2]) -> dict:
		# 1为点猫精选,2为新作喵喵看
		params = {"type": types}
		response = self.acquire.send_request(
			url="/creation-tools/v1/pc/home/recommend-work",
			method="get",
			params=params,
		)
		return response.json()

	# 获取编程猫首页推荐channel
	def get_channels_list(self, types: Literal["KITTEN", "NEMO"]) -> dict:
		params = {"type": types}
		response = self.acquire.send_request(
			url="/web/works/channels/list",
			method="get",
			params=params,
		)
		return response.json()

	# 获取指定channel
	def get_channel(self, channel_id: int, types: Literal["KITTEN", "NEMO"], limit: int = 5, page: int = 1) -> dict:
		params = {"type": types, "page": page, "limit": limit}
		response = self.acquire.send_request(
			url=f"/web/works/channels/{channel_id}/works",
			method="get",
			params=params,
		)
		return response.json()

	# 获取推荐作者
	def get_user_recommended(self) -> dict:
		response = self.acquire.send_request(url="/web/users/recommended", method="get")
		return response.json()

	# 获取训练师小课堂
	def get_post_lesion(self) -> dict:
		response = self.acquire.send_request(url="https://backend.box3.fun/diversion/codemao/post", method="get")
		return response.json()

	# 获取KN课程
	def get_kn_course(self) -> dict:
		response = self.acquire.send_request(url="/creation-tools/v1/home/especially/course", method="get")
		return response.json()

	# 获取KN公开课
	# https://api-creation.codemao.cn/neko/course/publish/list?limit=10&offset=0
	def get_kn_publish_course(self, limit: int = 10) -> list[dict]:
		params = {"limit": 10, "offset": 0}
		return self.acquire.fetch_data(
			url="https://api-creation.codemao.cn/neko/course/publish/list",
			params=params,
			limit=limit,
			total_key="total_course",
			# total_key也可设置为"course_page.total",
			data_key="course_page.items",
		)

	# 获取社区各个部分开启状态
	# TODO@Aurzex: 待完善
	def get_community_status(self, types: Literal["WEB_FORUM_STATUS", "WEB_FICTION_STATUS"]) -> dict:
		response = self.acquire.send_request(url=f"/web/config/tab/on-off/status?config_type={types}", method="get")
		return response.json()

	# 获取kitten编辑页面精选活动
	def get_kitten_activity(self) -> dict:
		response = self.acquire.send_request(
			url="https://api-creation.codemao.cn/kitten/activity/choiceness/list",
			method="get",
		)
		return response.json()

	# 获取nemo端教程合集
	def get_nemo_course_package(self, platform: int = 1) -> list[dict[Any, Any]]:
		params = {"limit": 50, "offset": 0, "platform": platform}
		return self.acquire.fetch_data(
			url="/creation-tools/v1/course/package/list",
			params=params,
			data_key="items",
		)

	# 获取nemo教程
	def get_nemo_package(self, course_package_id: int, limit: int = 50, offset: int = 0) -> list[dict[Any, Any]]:
		# course_package_id由get_nemo_course_package中获取
		params = {
			"course_package_id": course_package_id,
			"limit": limit,
			"offset": offset,
		}
		return self.acquire.fetch_data(
			url="/creation-tools/v1/course/list/search",
			params=params,
			data_key="course_page.items",
			# 参数中total_key也可用total_course
		)


@singleton
class Motion:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	# 签订友好协议
	def sign_nature(self) -> bool:
		response = self.acquire.send_request(url="/nemo/v3/user/level/signature", method="post")
		return response.status_code == OK_CODE

	# 获取用户协议
	def get_nature(self) -> dict:
		response = self.acquire.send_request(url="/tiger/v3/web/accounts/agreements", method="get")
		return response.json()

	# 注册
	def register(
		self,
		identity: str,
		password: str,
		captcha: str,
		pid: str = "65edCTyg",
		agreement_ids: list = [186, 13],
	) -> dict:
		data = json.dumps(
			{
				"identity": identity,
				"password": password,
				"captcha": captcha,
				"pid": pid,
				"agreement_ids": agreement_ids,
			},
		)

		response = self.acquire.send_request(
			url="/tiger/v3/web/accounts/register/phone/with-agreement",
			method="post",
			data=data,
		)

		return response.json()

	# 删除消息
	def delete_message(self, message_id: int) -> bool:
		response = self.acquire.send_request(
			url=f"/web/message-record/{message_id}",
			method="delete",
		)
		return response.status_code == NO_CONTENT_CODE
