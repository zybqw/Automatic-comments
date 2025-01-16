from json import loads
from random import choice
from typing import Literal, cast

from src.api import community, forum, shop, user, work
from src.base import acquire, data, decorator, file, tool


@decorator.singleton
class Union:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()
		self.cache = data.CodeMaoCache().cache
		self.community_obtain = community.Obtain()
		self.data = data.CodeMaoData().data
		self.file = file.CodeMaoFile()
		self.forum_motion = forum.Motion()
		self.forum_obtain = forum.Obtain()
		self.setting = data.CodeMaoSetting().setting
		self.shop_motion = shop.Motion()
		self.shop_obtain = shop.Obtain()
		self.tool_process = tool.CodeMaoProcess()
		self.tool_routine = tool.CodeMaoRoutine()
		self.user_motion = user.Motion()
		self.user_obtain = user.Obtain()
		self.work_motion = work.Motion()
		self.work_obtain = work.Obtain()


ClassUnion = Union().__class__


@decorator.singleton
class Tool(ClassUnion):
	def __init__(self) -> None:
		super().__init__()

	# 新增粉丝提醒
	def message_report(self, user_id: str):
		response = self.user_obtain.get_user_honor(user_id=user_id)
		timestamp = self.community_obtain.get_timestamp()["data"]
		user_data = {
			"user_id": response["user_id"],
			"nickname": response["nickname"],
			"level": response["author_level"],
			"fans": response["fans_total"],
			"collected": response["collected_total"],
			"liked": response["liked_total"],
			"view": response["view_times"],
			"timestamp": timestamp,
		}
		self.cache = cast(dict, self.cache)
		before_data = self.cache
		if before_data != {}:
			self.tool_routine.display_data_changes(
				before_data=before_data,
				after_data=user_data,
				data={
					"fans": "粉丝",
					"collected": "被收藏",
					"liked": "被赞",
					"view": "被预览",
				},
				date="timestamp",
			)
		self.cache.update(user_data)  # 使用 `update` 方法，确保同步

	# 猜测手机号码(暴力枚举)
	def guess_phonenum(self, phonenum: str) -> int | None:
		for i in range(10000):
			guess = f"{i:04d}"  # 格式化为四位数,前面补零
			test_string = int(phonenum.replace("****", guess))
			print(test_string)
			if self.user_motion.verify_phone(test_string):
				return test_string


@decorator.singleton
class Index(ClassUnion):
	def __init__(self) -> None:
		super().__init__()

	# 打印slogan
	def index(self):
		print(self.setting["PROGRAM"]["SLOGAN"])
		print(f"版本号: {self.setting['PROGRAM']['VERSION']}")
		print("*" * 22 + " 公告 " + "*" * 22)
		print("编程猫社区行为守则 https://shequ.codemao.cn/community/1619098")
		print("2025编程猫拜年祭活动 https://shequ.codemao.cn/community/1619855")
		print("*" * 22 + " 数据 " + "*" * 22)
		Tool().message_report(user_id=self.data["ACCOUNT_DATA"]["id"])
		print("*" * 50)


@decorator.singleton
class Obtain(ClassUnion):
	def __init__(self) -> None:
		super().__init__()

	# 获取新回复(传入参数就获取前*个回复,若没传入就获取新回复数量, 再获取新回复数量个回复)
	def get_new_replies(
		self, limit: int = 0, type_item: Literal["LIKE_FORK", "COMMENT_REPLY", "SYSTEM"] = "COMMENT_REPLY"
	) -> list[dict[str, str | int | dict]]:
		_list = []
		reply_num = self.community_obtain.get_message_count(method="web")[0]["count"]
		if reply_num == limit == 0:
			return [{}]
		result_num = reply_num if limit == 0 else limit
		offset = 0
		while result_num >= 0:
			limit = sorted([5, result_num, 200])[1]
			response = self.community_obtain.get_replies(type=type_item, limit=limit, offset=offset)
			_list.extend(response["items"][:result_num])
			result_num -= limit
			offset += limit
		return _list

	# 获取评论区信息
	def get_comments_detail(  # noqa: PLR0912
		self,
		id: int,
		source: Literal["work", "post"],
		method: Literal["user_id", "comments", "comment_id"] = "user_id",
	) -> list[int | dict | str]:
		if source == "work":
			comments = self.work_obtain.get_work_comments(work_id=id, limit=200)
		elif source == "post":
			comments = self.forum_obtain.get_post_replies_posts(id=id, limit=200)
		else:
			raise ValueError("不支持的来源类型")

		if method == "user_id":
			user_ids = []
			user_ids.extend(comment["user"]["id"] for comment in comments)
			if source == "post":
				for comment in comments:
					replies = self.forum_obtain.get_reply_post_comments(post_id=comment["id"], limit=200)
					user_ids.extend(reply["user"]["id"] for reply in replies)
			else:
				user_ids.extend(
					reply["reply_user"]["id"]
					for comment in comments
					if "replies" in comment and "items" in comment["replies"]
					for reply in comment["replies"]["items"]
				)
			result = user_ids

		elif method == "comment_id":
			comment_ids = [comment["id"] for comment in comments]
			if source == "post":
				for comment in comments:
					replies = self.forum_obtain.get_reply_post_comments(post_id=comment["id"], limit=200)
					comment_ids.extend(f"{comment['id']}.{reply['id']}" for reply in replies)
			else:
				comment_ids.extend(
					f"{comment['id']}.{reply['id']}"
					for comment in comments
					if "replies" in comment and "items" in comment["replies"]
					for reply in comment["replies"]["items"]
				)
			result = comment_ids

		elif method == "comments":
			detailed_comments = []
			for comment in comments:
				comment_detail = {
					"user_id": comment["user"]["id"],
					"nickname": comment["user"]["nickname"],
					"id": comment["id"],
					"content": comment["content"],
					"created_at": comment["created_at"],
					"is_top": comment.get("is_top", False),
					"replies": [],
				}
				if source == "post":
					replies = self.forum_obtain.get_reply_post_comments(post_id=comment["id"], limit=200)
				else:
					replies = comment.get("replies", {}).get("items", [])
				for reply in replies:
					reply_detail = {"id": reply["id"], "content": reply["content"], "created_at": reply["created_at"]}
					if source == "post":
						reply_detail["user_id"] = reply["user"]["id"]
						reply_detail["nickname"] = reply["user"]["nickname"]
					else:
						reply_detail["user_id"] = reply["reply_user"]["id"]
						reply_detail["nickname"] = reply["reply_user"]["nickname"]
					comment_detail["replies"].append(reply_detail)
				detailed_comments.append(comment_detail)
			result = detailed_comments

		else:
			raise ValueError("不支持的请求方法")

		return [item for index, item in enumerate(result) if item not in result[:index]]


@decorator.singleton
class Motion(ClassUnion):
	def __init__(self) -> None:
		super().__init__()

	# 由于编程猫社区命名极不规范,在本函数变量中，reply指work中comment的回复或者post中reply(回帖)中的回复
	# comment指work中的comment或者post中的reply
	# 但是delete_comment_post_reply函数reply指回帖,comment指回帖的回复
	# 将列表切片翻转是为了先删评论中的回复再删评论，防止在存在评论和回复都是待删项时，删除回复报错
	def clear_ads(self, source: Literal["work", "post"]) -> bool:
		def get_items_and_comments():
			if source == "work":
				return (
					self.user_obtain.get_user_works_web(self.data["ACCOUNT_DATA"]["id"]),
					lambda item_id: Obtain().get_comments_detail(id=item_id, source="work", method="comments"),
				)
			elif source == "post":
				return (
					self.forum_obtain.get_post_mine_all(method="created"),
					lambda item_id: Obtain().get_comments_detail(id=item_id, source="post", method="comments"),
				)
			raise ValueError("不支持的来源类型")

		def delete_comment(item_id, comment_id, is_reply=False):
			if source == "post":
				return self.forum_motion.delete_comment_post_reply(
					id=comment_id, type="comments" if is_reply else "replies"
				)
			return self.work_motion.del_comment_work(work_id=item_id, comment_id=comment_id)

		items_list, get_comments = get_items_and_comments()
		ads = self.data["USER_DATA"]["ads"]
		bad_users = self.data["USER_DATA"]["black_room"]["user"]
		ad_list, bad_list = [], []

		for item in items_list:
			item_id = int(item["id"])
			for comment in get_comments(item_id):
				comment = cast(dict, comment)
				comment_id, content, user_id = comment["id"], comment["content"].lower(), comment["user_id"]
				title = item["title" if source == "post" else "work_name"]

				if not comment.get("is_top", False):
					if any(ad in content for ad in ads):
						print(f"在{source} {title} 中发现广告: {content}")
						ad_list.append(f"{item_id}.{comment_id}:comment")
					elif str(user_id) in bad_users:  # 使用 elif 避免重复添加
						print(f"在{source} {title} 中发现黑名单: {comment['nickname']}发送的评论: {content}")
						bad_list.append(f"{item_id}.{comment_id}:comment")

				for reply in comment["replies"]:
					reply_id, reply_content, reply_user_id = reply["id"], reply["content"].lower(), reply["user_id"]
					if any(ad in reply_content for ad in ads):
						print(f"在{source} {title} 中 {content} 评论中发现广告: {reply_content}")
						ad_list.append(f"{item_id}.{reply_id}:reply")
					elif str(reply_user_id) in bad_users:  # 使用 elif 避免重复添加
						print(
							f"在{source} {title} 中 {content} 评论中发现黑名单: {reply['nickname']}发送的评论: {reply_content}"  # noqa: E501
						)
						bad_list.append(f"{item_id}.{reply_id}:reply")

		# 移除 bad_list 中与 ad_list 重复的项
		bad_list = [item for item in bad_list if item not in ad_list]

		def process_list(list_name, list_items):
			if list_items:
				print(f"发现以下{list_name}:")
				for item in list_items[::-1]:
					print(item)
				if input(f"是否删除所有{list_name}? (y/n): ").strip().lower() == "y":
					for item in list_items[::-1]:
						item_id, comment_id = map(int, item.split(":")[0].split("."))
						is_reply = item.split(":")[1] == "reply"  # 修正了这里的逻辑
						if not delete_comment(item_id, comment_id, is_reply):
							print(f"删除{list_name} {item} 失败")
							return False
						print(f"{list_name} {item} 已删除")
				else:
					print(f"未删除任何{list_name}")
			else:
				print(f"未发现{list_name}")
			return True

		return process_list("广告评论", ad_list) and process_list("黑名单评论", bad_list)

	# 清除邮箱红点
	def clear_red_point(self, method: Literal["nemo", "web"] = "web") -> bool:
		def get_message_counts(method: Literal["web", "nemo"]) -> dict:
			return self.community_obtain.get_message_count(method)

		def send_clear_request(url: str, params: dict) -> int:
			response = self.acquire.send_request(url=url, method="get", params=params)
			return response.status_code

		item = 0
		params: dict[str, int | str] = {
			"limit": 200,
			"offset": item,
		}

		if method == "web":
			while True:
				counts = get_message_counts(method)
				if len(set(counts[i]["count"] for i in range(3)) | {0}) == 1:
					return True

				query_types = self.setting["PARAMETER"]["CLIENT"]["all_read_type"]
				responses = {}
				for query_type in query_types:
					params["query_type"] = query_type
					responses[query_type] = send_clear_request(
						url="https://api.codemao.cn/web/message-record",
						params=params,
					)
				item += 200
				if len(set(responses.values()) | {200}) != 1:
					return False

		elif method == "nemo":
			while True:
				counts = get_message_counts("nemo")
				if (
					counts["like_collection_count"]
					+ counts["comment_count"]
					+ counts["re_create_count"]
					+ counts["system_count"]
					== 0
				):
					return True

				extra_items = [1, 3]
				# like为1,fork为3
				responses = {}
				for extra_url in extra_items:
					responses[extra_url] = send_clear_request(
						url=f"/nemo/v2/user/message/{extra_url}",
						params=params,
					)
				item += 200
				if len(set(responses.values()) | {200}) != 1:
					return False

		return False

	# 给某人作品全点赞
	def like_all_work(self, user_id: str):
		works_list = self.user_obtain.get_user_works_web(user_id)
		for item in works_list:
			item["id"] = cast(int, item["id"])
			if not self.work_motion.like_work(work_id=item["id"]):
				return False
		return True

	# 自动回复
	def reply_work(self) -> bool:
		new_replies = Obtain().get_new_replies()
		formatted_answers: list[dict[str, list[str] | str]] = [
			{
				question: (
					[resp.format(**self.data["INFO"]) for resp in response]  # 如果是列表，格式化列表中的每个元素
					if isinstance(response, list)
					else response.format(**self.data["INFO"])  # 如果是字符串，直接格式化字符串
				)
				for question, response in answer_dict.items()
			}
			for answer_dict in self.data["USER_DATA"]["answers"]
		]
		formatted_replies = [reply.format(**self.data["INFO"]) for reply in self.data["USER_DATA"]["replies"]]

		# 获取匹配的响应
		def get_response(comment: str, answers: list[dict[str, list[str] | str]]) -> str | None:
			for answer_dict in answers:
				for keyword, response in answer_dict.items():
					if keyword in comment:  # 如果关键词是字符串
						return response if isinstance(response, str) else choice(response)  # 同样处理响应类型
			return None

		filtered_replies = self.tool_process.filter_items_by_values(
			data=new_replies,
			id_path="type",
			values=["WORK_COMMENT", "WORK_REPLY", "WORK_REPLY_REPLY", "POST_COMMENT", "POST_REPLY", "POST_REPLY_REPLY"],
		)
		if not filtered_replies or filtered_replies == [{}]:
			return True

		for reply in filtered_replies:
			reply_type = reply["type"]
			content = loads(cast(str, reply["content"]))
			message = content["message"]
			comment_text = message["comment"] if reply_type in ["WORK_COMMENT", "POST_COMMENT"] else message["reply"]
			response_comment = get_response(comment=comment_text, answers=formatted_answers)
			comment = response_comment if response_comment else choice(formatted_replies)

			if reply_type.startswith("WORK"):
				business_id = message["business_id"]
				if reply_type == "WORK_COMMENT":
					comment_id = cast(int, reply.get("reference_id", message["comment_id"]))
					self.work_motion.reply_work(
						work_id=business_id,
						comment_id=comment_id,
						comment=comment,
						parent_id=0,
						return_data=True,
					)
				else:
					parent_id = cast(int, reply.get("reference_id", message["replied_id"]))
					comment_ids = Obtain().get_comments_detail(id=business_id, source="work", method="comment_id")
					comment_ids = cast(list[str], comment_ids)
					comment_id = cast(
						int, self.tool_routine.find_prefix_suffix(text=f".{message['reply_id']}", lst=comment_ids)[0]
					)
					self.work_motion.reply_work(
						work_id=business_id,
						comment_id=comment_id,
						comment=comment,
						parent_id=parent_id,
						return_data=True,
					)
			elif reply_type.startswith("POST"):
				business_id = message["business_id"]
				if reply_type == "POST_COMMENT":
					comment_id = cast(int, reply.get("reference_id", message["comment_id"]))
					self.forum_motion.reply_comment(
						reply_id=comment_id,
						parent_id=0,
						content=comment,
					)
				else:
					parent_id = cast(int, reply.get("reference_id", message["replied_id"]))
					comment_ids = Obtain().get_comments_detail(id=business_id, source="post", method="comment_id")
					comment_ids = cast(list[str], comment_ids)
					comment_id = cast(
						int, self.tool_routine.find_prefix_suffix(text=message["reply_id"], lst=comment_ids)[0]
					)
					self.forum_motion.reply_comment(
						reply_id=comment_id,
						parent_id=parent_id,
						content=comment,
					)
		return True

	# 工作室常驻置顶
	def top_work(self):
		detail = self.shop_obtain.get_shops_info()
		description = self.shop_obtain.get_shop_details(detail["work_subject_id"])["description"]
		self.shop_motion.update_shop_details(
			description=description,
			id=detail["id"],
			name=detail["name"],
			preview_url=detail["preview_url"],
		)


# "WORK_REPLY",路人a评论{user}在某个作品的评论
# "WORK_REPLY_REPLY_FEEDBACK",路人a回复{user}在某个作品下发布的评论的路人b/a的回复
# "WORK_COMMENT",路人a评论{user}的作品
# "WORK_REPLY_REPLY_AUTHOR",路人a回复{user}作品下路人b/a对某条评论的回复
# "WORK_REPLY_REPLY",路人a回复{user}作品下路人b/a的评论下{user}的回复
# "POST_REPLY",
# "POST_REPLY_REPLY_AUTHOR",
# "POST_REPLY_AUTHOR",
# "POST_COMMENT",
# "POST_REPLY_REPLY_FEEDBACK",
# "POST_REPLY_REPLY",
# "WORK_REPLY_AUTHOR",路人a回复{user}作品下路人b的某条评论
# "WORK_DISCUSSION_LIKED",
# "WORK_LIKE",
# "POST_DISCUSSION_LIKED",
# "POST_COMMENT_DELETE_FEEDBACK",
# "POST_DELETE_FEEDBACK",
# "WORK_SHOP_USER_LEAVE",
