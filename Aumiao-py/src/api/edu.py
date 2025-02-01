import json
from typing import Any, Literal

from src.base import acquire
from src.base.decorator import singleton

from . import community

OK_CODE = 200
NO_CONTENT_CODE = 204


# sb编程猫,params中的{"_": time_stamp}可以替换为{"TIME": time_stamp}
@singleton
class Motion:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	# 更改姓名
	def update_name(self, user_id: int, real_name: str) -> bool:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "userId": user_id, "realName": real_name}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/account/updateName",
			method="get",
			params=params,
		)
		return response.status_code == OK_CODE

	# 创建班级
	def create_class(self, name: str) -> dict:
		data = json.dumps({"name": name})
		response = self.acquire.send_request(url="https://eduzone.codemao.cn/edu/zone/class", method="post", data=data)
		return response.json()

	# 删除班级
	def delete_class(self, class_id: int) -> bool:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url=f"https://eduzone.codemao.cn/edu/zone/class/{class_id}",
			method="delete",
			params=params,
		)
		return response.status_code == NO_CONTENT_CODE

	# 班级内新建学生账号
	def create_student(self, name: list[str], class_id: int) -> bool:
		data = json.dumps({"student_names": name})
		response = self.acquire.send_request(
			url=f"https://eduzone.codemao.cn/edu/zone/class/{class_id}/students",
			method="post",
			data=data,
		)
		return response.status_code == OK_CODE

	# 重置密码
	def reset_password(self, stu_id: list[int]) -> bool:
		data = json.dumps({"student_id": stu_id})
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/students/password",
			method="patch",
			data=data,
		)
		return response.status_code == OK_CODE

	# 删除班级内学生
	def remove_student(self, stu_id: int) -> bool:
		data = json.dumps({})
		response = self.acquire.send_request(
			url=f"https://eduzone.codemao.cn/edu/zone/student/remove/{stu_id}",
			method="post",
			data=data,
		)
		return response.status_code == OK_CODE

	# 添加、修改自定义备课包
	# patch为修改信息,post用于创建备课包
	def add_customized_package(self, method: Literal["post", "patch"], avatar_url: str, description: str, name: str, *, return_data: bool = True) -> dict | bool:
		data = json.dumps({"avatar_url": avatar_url, "description": description, "name": name})
		response = self.acquire.send_request(url="https://eduzone.codemao.cn/edu/zone/lesson/customized/packages", method=method, data=data)
		return response.json() if return_data else response.status_code == OK_CODE


@singleton
class Obtain:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	# 获取个人信息
	def get_data_details(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(url="https://eduzone.codemao.cn/edu/zone", method="get", params=params)
		return response.json()

	# 猜测返回的role_id当值为20001时为学生账号,10002为教师账号
	# 获取账户状态
	def get_account_status(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/api/home/account",
			method="get",
			params=params,
		)
		return response.json()

	# 获取未读消息数
	def get_message_count(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/system/message/unread/num",
			method="get",
			params=params,
		)
		return response.json()

	# 获取学校分类列表
	def get_school_label(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/school/open/grade/list",
			method="get",
			params=params,
		)
		return response.json()

	# 获取所有班级
	def get_classes(self, method: Literal["detail", "simple"] = "simple", limit: int | None = 20) -> dict | list[dict]:
		if method == "simple":
			classes = self.acquire.send_request(
				url="https://eduzone.codemao.cn/edu/zone/classes/simple",
				method="get",
			).json()
		elif method == "detail":
			url = "https://eduzone.codemao.cn/edu/zone/classes/"
			time_stamp = community.Obtain().get_timestamp()["data"]
			params = {"page": 1, "TIME": time_stamp}

			classes = self.acquire.fetch_data(
				url=url,
				params=params,
				data_key="items",
				method="page",
				args={"remove": "page", "res_amount_key": "limit"},
				limit=limit,
			)
		return classes

	# 获取删除学生记录
	def get_record_del(self, limit: int | None = 20) -> list[dict[Any, Any]]:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"page": 1, "limit": 10, "TIME": time_stamp}
		return self.acquire.fetch_data(
			url="https://eduzone.codemao.cn/edu/zone/student/remove/record",
			params=params,
			data_key="items",
			method="page",
			args={"amount": "limit", "remove": "page"},
			limit=limit,
		)

	# 获取班级内全部学生
	def get_students(self, invalid: int = 1, limit: int | None = 50) -> list[dict[Any, Any]]:
		# invalid为1时为已加入班级学生,为0则反之
		data = json.dumps({"invalid": invalid})
		params = {"page": 1, "limit": 100}
		return self.acquire.fetch_data(
			url="https://eduzone.codemao.cn/edu/zone/students",
			params=params,
			data=data,
			fetch_method="post",
			data_key="items",
			method="page",
			args={"amount": "limit", "remove": "page"},
			limit=limit,
		)

	# 获取新闻
	def get_menus(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/api/home/eduzone/menus",
			method="get",
			params=params,
		)
		return response.json()

	# 获取banner
	def get_banner(self, type_id: int = 101) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "type_id": type_id}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/api/home/banners",
			method="get",
			params=params,
		)
		return response.json()

	# 获取服务器时间
	def get_sever_time(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/base/server/time",
			method="get",
			params=params,
		)
		return response.json()

	# 获取各部分开启状态
	def get_package_status(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/lessons/person/package/remind/status",
			method="get",
			params=params,
		)
		return response.json()

	# 获取conf
	def get_conf(self, tag: Literal["teacher_guided_wechat_link"]) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "tag": tag}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/base/general/conf",
			method="get",
			params=params,
		)
		return response.json()

	# 获取账户多余info
	def get_extend_info(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/user-extend/info",
			method="get",
			params=params,
		)
		return response.json()

	# 获取小黑板记录
	def get_board_record(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/operation/records",
			method="get",
			params=params,
		)
		return response.json()

	# 获取授课状态
	def get_teaching_status(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/teaching/class/remind",
			method="get",
			params=params,
		)
		return response.json()

	# 获取信息栏信息
	def get_homepage_info(self) -> dict:
		# "total_works": 作品数
		# "behavior_score": 课堂表现分
		# "average_score": 作品平均分
		# "high_score": 作品最高分
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/homepage/statistic",
			method="get",
			params=params,
		)
		return response.json()

	# 获取所有工具
	def get_homepage_menus(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/homepage/menus",
			method="get",
			params=params,
		)
		return response.json()

	# 获取云端存储的所有平台的作品
	# mark_status中1为已评分,2为未评分
	# updated_at_from&updated_at_to按字面意思,传参时为timestamp
	# max_score&min_score按字面意思,传参时值为0-100,且都为整十数
	# teachingRecordId为上课记录id
	# status为发布状态,100为已发布,1为未发布
	# name用于区分作品名
	# type为作品类型,源码编辑器为1,海龟编辑器2.0(c++)为16,代码岛2.0为5,海龟编辑器为7,nemo为8
	# version用于区分源码编辑器4.0和源码编辑器,在请求中,源码编辑器4.0的version为4,源码编辑器不填
	# 返回数据中的praise_times为点赞量
	# 返回数据中的language_type貌似用来区分海龟编辑器2.0(c++)与海龟编辑器,海龟编辑器的language_type为3
	def get_all_works(self, limit: int | None = 50) -> list[dict[Any, Any]]:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"page": 1, "TIME": time_stamp}
		return self.acquire.fetch_data(
			url="https://eduzone.codemao.cn/edu/zone/work/manager/student/works",
			params=params,
			data_key="items",
			method="page",
			args={"remove": "page", "res_amount_key": "limit"},
			limit=limit,
		)

	# 获取周作品统计数据
	# year传参示例:2024,class_id为None时返回全部班级的数据
	def get_work_statistics(self, class_id: int | None, year: int, month: int) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		formatted_month = f"{month:02d}"
		params = {"TIME": time_stamp, "year": year, "month": formatted_month, "class_id": class_id}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/work/manager/works/statistics",
			method="get",
			params=params,
		)
		return response.json()

	# 获取上课记录
	def get_teaching_record(self, limit: int | None = 10) -> list[dict[Any, Any]]:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"page": 1, "TIME": time_stamp, "limit": 10}
		return self.acquire.fetch_data(
			url="https://eduzone.codemao.cn/edu/zone/teaching/record/list",
			params=params,
			data_key="items",
			method="page",
			args={"remove": "page", "amount": "limit"},
			limit=limit,
		)

	# 获取教授班级(需要教师号)
	def get_teaching_classes(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/teaching/class/teacher/list",
			method="get",
			params=params,
		)
		return response.json()

	# 获取info(需要教师账号)
	def get_data_info(self, unit_id: int) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "unitId": unit_id}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/school/info",
			method="get",
			params=params,
		)
		return response.json()

	# 获取官方课程包
	def get_official_package(self, limit: int | None = 150) -> list[dict[Any, Any]]:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "pacakgeEntryType": 0, "topicType": "all", "topicId": "all", "tagId": "all", "page": 1, "limit": 150}
		return self.acquire.fetch_data(
			url="https://eduzone.codemao.cn/edu/zone/lesson/offical/packages",
			params=params,
			method="page",
			args={"amount": "limit", "remove": "page"},
			data_key="items",
			limit=limit,
		)

	## 获取官方课程包主题
	def get_official_package_topic(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "pacakgeEntryType": 0, "topicType": "all"}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/lessons/official/packages/topics",
			method="get",
			params=params,
		)
		return response.json()

	# 获取官方课程包tag
	def get_official_package_tags(self) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "pacakgeEntryType": 0, "topicType": "all"}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/lessons/official/packages/topics/all/tags",
			method="get",
			params=params,
		)
		return response.json()

	# 获取我的备课包(需要教师号)
	def get_customized_package(self, limit: int | None = 100) -> list[dict[Any, Any]]:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "page": 1, "limit": 100}
		return self.acquire.fetch_data(
			url="https://eduzone.codemao.cn/edu/zone/lesson/offical/packages",
			params=params,
			method="page",
			args={"amount": "limit", "remove": "page"},
			data_key="items",
			limit=limit,
		)

	# 获取自定义备课包信息/删除备课包
	def get_customized_package_info(self, package_id: int, method: Literal["get", "delete"]) -> dict | bool:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp}
		response = self.acquire.send_request(
			url=f"https://eduzone.codemao.cn/edu/zone/lesson/customized/packages/{package_id}",
			method=method,
			params=params,
		)
		return response.json() if method == "get" else response.status_code == OK_CODE

	# 获取自定义备课包内容
	def get_customized_package_lesson(self, package_id: int, limit: int) -> dict:
		time_stamp = community.Obtain().get_timestamp()["data"]
		params = {"TIME": time_stamp, "limit": limit, "package_id": package_id}
		response = self.acquire.send_request(
			url="https://eduzone.codemao.cn/edu/zone/lesson/customized/package/lessons",
			method="get",
			params=params,
		)
		return response.json()
