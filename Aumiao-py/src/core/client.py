from collections import defaultdict
from collections.abc import Generator
from enum import Enum
from json import loads
from random import choice
from typing import Any, Literal, TypedDict, cast, overload

from src.api import community, edu, forum, shop, user, whale, work
from src.utils import acquire, data, decorator, file, tool


class FormattedAnswer(TypedDict):
	question: str
	responses: list[str] | str


class ReplyType(Enum):
	WORK_COMMENT = "WORK_COMMENT"
	WORK_REPLY = "WORK_REPLY"
	# 其他类型同理


VALID_REPLY_TYPES = {"WORK_COMMENT", "WORK_REPLY", "WORK_REPLY_REPLY", "POST_COMMENT", "POST_REPLY", "POST_REPLY_REPLY"}
OK_CODE = 200


@decorator.singleton
class Union:
	# 初始化Union类
	def __init__(self) -> None:
		# 获取CodeMaoClient对象
		self.acquire = acquire.CodeMaoClient()
		# 获取CacheManager对象
		self.cache = data.CacheManager().data
		# 获取Obtain对象
		self.community_obtain = community.Obtain()
		# 获取DataManager对象
		self.data = data.DataManager().data
		# 获取Obtain对象
		self.edu_obtain = edu.Obtain()
		# 获取CodeMaoFile对象
		self.file = file.CodeMaoFile()
		self.forum_motion = forum.Motion()
		self.forum_obtain = forum.Obtain()
		self.setting = data.SettingManager().data
		self.shop_motion = shop.Motion()
		self.shop_obtain = shop.Obtain()
		self.tool_process = tool.CodeMaoProcess()
		self.tool_routine = tool.CodeMaoRoutine()
		self.user_motion = user.Motion()
		self.user_obtain = user.Obtain()
		self.whale_obtain = whale.Obtain()
		self.whale_motion = whale.Motion()
		self.whale_routine = whale.Routine()
		self.work_motion = work.Motion()
		self.work_obtain = work.Obtain()


ClassUnion = Union().__class__


@decorator.singleton
class Tool(ClassUnion):
	def __init__(self) -> None:
		super().__init__()
		self.cache_manager = data.CacheManager()  # 添加这行

	def message_report(self, user_id: str) -> None:
		# 获取用户荣誉信息
		response = self.user_obtain.get_user_honor(user_id=user_id)
		# 获取当前时间戳
		timestamp = self.community_obtain.get_timestamp()["data"]
		# 构造用户数据字典
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
		# 获取缓存数据
		before_data = self.cache_manager.data
		# 如果缓存数据不为空,则显示数据变化
		if before_data != {}:
			self.tool_routine.display_data_changes(
				before_data=before_data,
				after_data=user_data,
				metrics={
					"fans": "粉丝",
					"collected": "被收藏",
					"liked": "被赞",
					"view": "被预览",
				},
				date_field="timestamp",
			)
		# 更新缓存数据
		self.cache_manager.update(user_data)  # 使用管理器的 update 方法

	# 猜测手机号码(暴力枚举)
	def guess_phonenum(self, phonenum: str) -> int | None:
		# 枚举10000个四位数
		for i in range(10000):
			guess = f"{i:04d}"  # 格式化为四位数,前面补零
			test_string = int(phonenum.replace("****", guess))
			print(test_string)
			if self.user_motion.verify_phone(test_string):
				return test_string
		return None


@decorator.singleton
class Index(ClassUnion):
	def __init__(self) -> None:
		super().__init__()

	# 打印slogan
	def index(self) -> None:
		# 打印slogan
		print(self.setting.PROGRAM.SLOGAN)
		# 打印版本号
		print(f"版本号: {self.setting.PROGRAM.VERSION}")
		# 打印公告标题
		print("*" * 22 + " 公告 " + "*" * 22)
		# 打印编程猫社区行为守则链接
		print("编程猫社区行为守则 https://shequ.codemao.cn/community/1619098")
		# 打印2025编程猫拜年祭活动链接
		print("2025编程猫拜年祭活动 https://shequ.codemao.cn/community/1619855")
		# 打印数据标题
		print("*" * 22 + " 数据 " + "*" * 22)
		# 调用Tool类的message_report方法,传入用户id
		Tool().message_report(user_id=self.data.ACCOUNT_DATA.id)
		# 打印分隔线
		print("*" * 50)


@decorator.singleton
class Obtain(ClassUnion):
	def __init__(self) -> None:
		super().__init__()

	# 获取新回复(传入参数就获取前*个回复,若没传入就获取新回复数量, 再获取新回复数量个回复)
	def get_new_replies(
		self,
		limit: int = 0,
		type_item: Literal["LIKE_FORK", "COMMENT_REPLY", "SYSTEM"] = "COMMENT_REPLY",
	) -> list[dict[str, str | int | dict]]:
		_list = []
		# 获取新回复数量
		reply_num = self.community_obtain.get_message_count(method="web")[0]["count"]
		# 如果新回复数量为0且limit也为0,则返回空列表
		if reply_num == limit == 0:
			return [{}]
		# 如果limit为0,则获取新回复数量个回复,否则获取limit个回复
		result_num = reply_num if limit == 0 else limit
		offset = 0
		# 循环获取新回复
		while result_num >= 0:
			# 每次获取5个或剩余回复数量或200个回复
			limit = sorted([5, result_num, 200])[1]
			# 获取回复
			response = self.community_obtain.get_replies(types=type_item, limit=limit, offset=offset)
			# 将回复添加到列表中
			_list.extend(response["items"][:result_num])
			# 更新剩余回复数量
			result_num -= limit
			# 更新偏移量
			offset += limit
		return _list

	# 获取评论区信息
	def get_comments_detail_new(
		self,
		com_id: int,
		source: Literal["work", "post", "shop"],
		method: Literal["user_id", "comments", "comment_id"] = "user_id",
	) -> list[int | dict | str]:
		def _get_replies(source: str, comment: dict) -> Generator[dict]:
			"""统一获取评论的回复"""
			if source == "post":
				return self.forum_obtain.get_reply_post_comments(post_id=comment["id"], limit=None)
			return comment.get("replies", {}).get("items", [])

		def _extract_reply_user_id(reply: dict, source: str) -> int:
			"""统一提取回复用户ID"""
			return reply["user"]["id"] if source == "post" else reply["reply_user"]["id"]

		def _handle_user_id(comments: list[dict], source: str) -> list[int]:
			"""优化后的用户ID处理"""
			user_ids = []
			for comment in comments:
				user_ids.append(comment["user"]["id"])
				replies = _get_replies(source, comment)
				user_ids.extend(_extract_reply_user_id(reply, source) for reply in replies)
			return user_ids

		def _handle_comment_id(comments: list[dict], source: str) -> list[str]:
			"""优化后的评论ID处理"""
			comment_ids = []
			for comment in comments:
				comment_ids.append(str(comment["id"]))
				replies = _get_replies(source, comment)
				comment_ids.extend(f"{comment['id']}.{reply['id']}" for reply in replies)
			return comment_ids

		def _handle_detailed_comments(comments: list[dict], source: str) -> list[dict]:
			"""处理完整评论信息"""
			detailed_comments = []
			for comment in comments:
				comment_data = {
					"user_id": comment["user"]["id"],
					"nickname": comment["user"]["nickname"],
					"id": comment["id"],
					"content": comment["content"],
					"created_at": comment["created_at"],
					"is_top": comment.get("is_top", False),
					"replies": [],
				}
				for reply in _get_replies(source, comment):
					reply_data = {
						"id": reply["id"],
						"content": reply["content"],
						"created_at": reply["created_at"],
						"user_id": _extract_reply_user_id(reply, source),
						"nickname": reply["user" if source == "post" else "reply_user"]["nickname"],
					}
					comment_data["replies"].append(reply_data)
				detailed_comments.append(comment_data)
			return detailed_comments

		# 通过映射表处理不同来源的评论获取逻辑
		source_methods = {
			"work": (self.work_obtain.get_work_comments, "work_id"),
			"post": (self.forum_obtain.get_post_replies_posts, "ids"),
			"shop": (self.shop_obtain.get_shop_discussion, "shop_id"),
		}
		if source not in source_methods:
			msg = "不支持的来源类型"
			raise ValueError(msg)
		method_func, arg_key = source_methods[source]
		comments = method_func(**{arg_key: com_id, "limit": 500})

		# 处理方法映射表
		method_handlers = {
			"user_id": _handle_user_id,
			"comment_id": _handle_comment_id,
			"comments": _handle_detailed_comments,
		}
		if method not in method_handlers:
			msg = "不支持的请求方法"
			raise ValueError(msg)

		# 获取处理结果并去重
		result = method_handlers[method](comments, source)
		return self.tool_process.deduplicate(result) if method in ("user_id", "comment_id") else result


@decorator.singleton
class Motion(ClassUnion):
	def __init__(self) -> None:
		super().__init__()

	# 由于编程猫社区命名极不规范,在本函数变量中,reply指work中comment的回复或者post中reply(回帖)中的回复
	# comment指work中的comment或者post中的reply
	# 但是delete_comment_post_reply函数reply指回帖,comment指回帖的回复
	# 将列表切片翻转是为了先删评论中的回复再删评论,防止在存在评论和回复都是待删项时,删除回复报错
	def clear_comments(
		self,
		source: Literal["work", "post"],
		action_type: Literal["ads", "duplicates", "blacklist"],
	) -> bool:
		"""清理指定来源的评论(广告/黑名单/刷屏)"""

		# 获取数据源和对应方法
		def get_source_data() -> ...:
			if source == "work":
				return (
					self.user_obtain.get_user_works_web(self.data.ACCOUNT_DATA.id, limit=None),
					lambda _id: Obtain().get_comments_detail_new(_id, "work", "comments"),
					self.work_motion.del_comment_work,
				)
			if source == "post":
				return (
					self.forum_obtain.get_post_mine_all("created", limit=None),
					lambda _id: Obtain().get_comments_detail_new(_id, "post", "comments"),
					lambda _id, comment_id, **_: self.forum_motion.delete_comment_post_reply(
						comment_id,
						"comments" if _.get("is_reply") else "replies",
					),
				)
			msg = "不支持的来源类型"
			raise ValueError(msg)

		items, get_comments, delete_handler = get_source_data()
		lists = {"ads": [], "blacklist": [], "duplicates": []}
		params = {
			"ads": self.data.USER_DATA.ads,
			"blacklist": self.data.USER_DATA.black_room.user,
			"spam_max": self.setting.PARAMETER.spam_max,
		}

		# 主处理逻辑
		for item in items:
			item_id = int(item["id"])
			title = item["title" if source == "post" else "work_name"]
			comments = get_comments(item_id)

			# 处理广告/黑名单
			if action_type in ("ads", "blacklist"):
				for comment in comments:
					if comment.get("is_top"):
						continue
					self._process_comment(
						comment,
						item_id,
						title,
						action_type,
						params,
						lists,
						delete_handler,
					)
					for reply in comment["replies"]:
						self._process_reply(
							reply,
							comment["content"],
							item_id,
							title,
							action_type,
							params,
							lists,
							delete_handler,
						)

			# 处理刷屏评论
			elif action_type == "duplicates":
				content_map = defaultdict(list)
				for comment in comments:
					self._track_duplicates(comment, item_id, content_map)
					for reply in comment["replies"]:
						self._track_duplicates(reply, item_id, content_map, is_reply=True)

				for (_uid, content), ids in content_map.items():
					if len(ids) >= params["spam_max"]:
						print(f"发现刷屏评论:{content}")
						lists["duplicates"].extend(ids)

		# 执行删除操作
		@decorator.skip_on_error
		def execute_deletion(target_list: list, label: str) -> bool:
			if not target_list:
				print(f"未发现{label}")
				return True

			print(f"发现以下{label}:")
			for item in reversed(target_list):
				print(f" - {item.split(':')[0]}")

			if input(f"删除所有{label}?(y/n)").lower() != "y":
				print("取消删除操作")
				return True

			for entry in reversed(target_list):
				item_id, comment_id = entry.split(":")[0].split(".")
				is_reply = ":reply" in entry
				if not delete_handler(int(item_id), int(comment_id), is_reply=is_reply):
					print(f"删除失败:{entry}")
					return False
				print(f"已删除:{entry}")
			return True

		return execute_deletion(
			lists[action_type],
			{
				"ads": "广告评论",
				"blacklist": "黑名单评论",
				"duplicates": "刷屏评论",
			}[action_type],
		)

	# 辅助方法(类内部其他位置定义)
	def _process_comment(self, data: dict, item_id: int, title: str, action_type: Literal["ads", "blacklist"], params: dict, lists: dict, _: object) -> None:
		content = data["content"].lower()
		identifier = f"{item_id}.{data['id']}:comment"

		if action_type == "ads" and any(ad in content for ad in params["ads"]):
			print(f"广告评论 [{title}]: {content}")
			lists["ads"].append(identifier)

		elif action_type == "blacklist" and str(data["user_id"]) in params["blacklist"]:
			print(f"黑名单用户 [{title}]: {data['nickname']}")
			lists["blacklist"].append(identifier)

	def _process_reply(self, data: dict, parent_content: str, item_id: int, title: str, action_type: Literal["ads", "blacklist"], params: dict, lists: dict, _: object) -> None:
		content = data["content"].lower()
		identifier = f"{item_id}.{data['id']}:reply"

		if action_type == "ads" and any(ad in content for ad in params["ads"]):
			print(f"广告回复 [{title}] ({parent_content}): {content}")
			lists["ads"].append(identifier)

		elif action_type == "blacklist" and str(data["user_id"]) in params["blacklist"]:
			print(f"黑名单回复 [{title}] ({parent_content}): {data['nickname']}")
			lists["blacklist"].append(identifier)

	def _track_duplicates(self, data: dict, item_id: int, content_map: dict, *, is_reply: bool = False) -> None:
		key = (data["user_id"], data["content"].lower())
		content_map[key].append(
			f"{item_id}.{data['id']}:{'reply' if is_reply else 'comment'}",
		)

	def clear_red_point(self, method: Literal["nemo", "web"] = "web") -> bool:
		def get_message_counts(method: Literal["web", "nemo"]) -> dict:
			"""获取各类型消息未读数"""
			return self.community_obtain.get_message_count(method)

		def send_clear_request(url: str, params: dict) -> int:
			"""发送标记已读请求"""
			response = self.acquire.send_request(endpoint=url, method="GET", params=params)
			return response.status_code

		offset = 0  # 分页偏移量
		page_size = 200
		params: dict[str, int | str] = {"limit": page_size, "offset": offset}

		if method == "web":
			query_types = self.setting.PARAMETER.all_read_type
			while True:
				# 检查所有指定类型消息是否均已读
				counts = get_message_counts("web")
				if all(count["count"] == 0 for count in counts[:3]):
					return True

				# 更新当前分页偏移量
				params["offset"] = offset

				# 批量发送标记已读请求
				responses = {}
				for q_type in query_types:
					params["query_type"] = q_type
					responses[q_type] = send_clear_request(
						url="/web/message-record",
						params=params,
					)

				# 校验请求结果
				if any(status != OK_CODE for status in responses.values()):
					return False

				offset += page_size

		elif method == "nemo":
			message_types = [1, 3]  # 1:点赞收藏 3:fork
			while True:
				# 检查所有类型消息总数
				counts = get_message_counts("nemo")
				total_unread = sum(
					counts[key]
					for key in [
						"like_collection_count",
						"comment_count",
						"re_create_count",
						"system_count",
					]
				)
				if total_unread == 0:
					return True

				# 更新当前分页偏移量
				params["offset"] = offset

				# 批量发送标记已读请求
				responses = {}
				for m_type in message_types:
					responses[m_type] = send_clear_request(
						url=f"/nemo/v2/user/message/{m_type}",
						params=params,
					)

				# 校验请求结果
				if any(status != OK_CODE for status in responses.values()):
					return False

				offset += page_size

		return False

	# 给某人作品全点赞
	def like_all_work(self, user_id: str) -> bool:
		works_list = self.user_obtain.get_user_works_web(user_id, limit=None)
		for item in works_list:
			item["id"] = cast(int, item["id"])
			if not self.work_motion.like_work(work_id=item["id"]):
				return False
		return True

	def reply_work(self) -> bool:
		"""自动回复工作流"""
		new_replies: list[dict] = Obtain().get_new_replies()

		@overload
		def _preprocess_data(data_type: Literal["answers"]) -> dict[str, list[str] | str]: ...

		@overload
		def _preprocess_data(data_type: Literal["replies"]) -> list[str]: ...
		# 合并预处理逻辑
		def _preprocess_data(data_type: Literal["answers", "replies"]) -> dict[str, list[str] | str] | list[str]:
			"""统一预处理数据"""
			if data_type == "answers":
				result: dict[str, list[str] | str] = {}
				for answer_dict in self.data.USER_DATA.answers:
					for keyword, response in answer_dict.items():
						# 内联格式化逻辑
						formatted = [resp.format(**self.data.INFO) for resp in response] if isinstance(response, list) else response.format(**self.data.INFO)
						result[keyword] = formatted
				return result
			return [reply.format(**self.data.INFO) for reply in self.data.USER_DATA.replies]

		formatted_answers = _preprocess_data("answers")
		formatted_replies = _preprocess_data("replies")

		# 合并过滤逻辑到主流程
		filtered_replies = self.tool_process.filter_items_by_values(
			data=new_replies,
			id_path="type",
			values=list(VALID_REPLY_TYPES),
		)
		if not filtered_replies:
			return True

		# 合并单条回复处理逻辑
		for reply in filtered_replies:
			try:
				content = loads(reply["content"])
				message = content["message"]
				reply_type = reply["type"]

				# 合并文本提取和响应匹配逻辑
				comment_text = message["comment"] if reply_type in {"WORK_COMMENT", "POST_COMMENT"} else message["reply"]

				# 优化匹配逻辑
				chosen_comment = None
				for keyword, resp in formatted_answers.items():  # 明确 formatted_answers 是 dict
					if keyword in comment_text:
						chosen_comment = choice(resp) if isinstance(resp, list) else resp  # noqa: S311
						break
				if chosen_comment is None:  # 如果没有匹配的答案,则随机选择一个回复
					chosen_comment = choice(formatted_replies)  # noqa: S311

				# 统一处理回复操作
				self._execute_reply(
					reply_type=reply_type,
					message=message,
					raw_reply=reply,
					comment=chosen_comment,
				)
			except Exception as e:
				print(f"处理回复时发生错误: {e}")
				continue

		return True

	@decorator.skip_on_error
	def _execute_reply(
		self,
		reply_type: str,
		message: dict,
		raw_reply: dict,
		comment: str,
	) -> None:
		"""统一执行回复操作(合并work/post处理逻辑)"""
		business_id = message["business_id"]
		source_type = "work" if reply_type.startswith("WORK") else "post"

		# 合并标识获取逻辑
		if reply_type.endswith("_COMMENT"):
			comment_id = raw_reply.get("reference_id", message["comment_id"])
			parent_id = 0
		else:
			parent_id = raw_reply.get("reference_id", message.get("replied_id", 0))
			comment_ids = [
				str(item)
				for item in Obtain().get_comments_detail_new(
					com_id=business_id,
					source=source_type,
					method="comment_id",
				)
				if isinstance(item, int | str)
			]
			target_id = message.get("reply_id", "")
			search_pattern = f".{target_id}" if source_type == "work" else target_id
			if (found_id := self.tool_routine.find_prefix_suffix(search_pattern, comment_ids)[0]) is None:
				msg = "未找到匹配的评论ID"
				raise ValueError(msg)
			comment_id = int(found_id)

		# 合并API调用逻辑
		params = (
			{
				"work_id": business_id,
				"comment_id": comment_id,
				"comment": comment,
				"parent_id": parent_id,
				"return_data": True,
			}
			if source_type == "work"
			else {
				"reply_id": comment_id,
				"parent_id": parent_id,
				"content": comment,
			}
		)

		(self.work_motion.reply_work if source_type == "work" else self.forum_motion.reply_comment)(**params)

	# 工作室常驻置顶
	def top_work(self) -> None:
		detail = self.shop_obtain.get_shops_details()
		description = self.shop_obtain.get_shop_details(detail["work_subject_id"])["description"]
		self.shop_motion.update_shop_details(
			description=description,
			shop_id=detail["id"],
			name=detail["name"],
			preview_url=detail["preview_url"],
		)

	# 查看账户所有信息综合
	def get_account_all_data(self) -> dict[Any, Any]:
		s = self.user_obtain.get_data_details()
		# 创建一个空列表来存储所有字典
		all_data: list[dict] = []
		# 调用每个函数并将结果添加到列表中
		s = self.user_obtain.get_data_details()
		all_data.append(s)
		s = self.user_obtain.get_data_level()
		all_data.append(s)
		s = self.user_obtain.get_data_name()
		all_data.append(s)
		s = self.user_obtain.get_data_privacy()
		all_data.append(s)
		s = self.user_obtain.get_data_score()
		all_data.append(s)
		s = self.user_obtain.get_data_profile("web")
		all_data.append(s)
		s = self.user_obtain.get_data_tiger()
		all_data.append(s)
		s = self.edu_obtain.get_data_details()
		all_data.append(s)
		return self.tool_routine.merge_user_data(data_list=all_data)

	# 查看账户状态
	def get_account_status(self) -> str:
		status = self.user_obtain.get_data_details()
		return f"禁言状态{status['voice_forbidden']},签订友好条约{status['has_signed']}"

	# 处理举报
	# 需要风纪权限
	def handle_report(self, admin_id: int) -> None:  # noqa: PLR0915
		comments_list = self.whale_obtain.get_comment_report(types="ALL", status="TOBEDONE", limit=None)
		posts_list = self.whale_obtain.get_post_report(status="TOBEDONE", limit=None)
		discussions_list = self.whale_obtain.get_discussion_report(status="TOBEDONE", limit=None)
		for item in comments_list:
			print("=" * 50)
			print(f"举报ID:{item['id']}")
			print(f"举报内容:{item['comment_content']}")
			print(f"所属板块:{item['comment_source_object_name']}")
			print(f"被举报人:{item['comment_user_nickname']}")
			print(f"举报原因:{item['reason_content']}")
			print(f"举报时间:{item['created_at']}")
			print("-" * 50)
			while True:
				choice = input("选择操作: D:删除评论, S:禁言7天, P:通过")
				if choice == "D":
					self.whale_motion.handle_comment_report(report_id=item["id"], status="DELETE", admin_id=admin_id)
					break
				if choice == "S":
					self.whale_motion.handle_comment_report(report_id=item["id"], status="MUTE_SEVEN_DAYS", admin_id=admin_id)
					break
				if choice == "P":
					self.whale_motion.handle_comment_report(report_id=item["id"], status="PASS", admin_id=admin_id)
					break
				print("无效输入")
		for item in posts_list:
			print("=" * 50)
			print(f"举报ID:{item['report_id']}")
			print(f"举报内容:{item['post_title']}")
			print(f"所属板块:{item['board_name']}")
			print(f"被举报人:{item['post_user_nick_name']}")
			print(f"举报原因:{item['reason_content']}")
			print(f"举报线索:{item['description']}")
			print(f"举报时间:{item['created_at']}")
			print("-" * 50)
			while True:
				choice = input("选择操作: D:删除评论, S:禁言7天, P:通过")
				if choice == "D":
					self.whale_motion.handle_post_report(report_id=item["report_id"], status="DELETE", admin_id=admin_id)
					break
				if choice == "S":
					self.whale_motion.handle_post_report(report_id=item["report_id"], status="MUTE_SEVEN_DAYS", admin_id=admin_id)
					break
				if choice == "P":
					self.whale_motion.handle_post_report(report_id=item["report_id"], status="PASS", admin_id=admin_id)
					break
				print("无效输入")
		for item in discussions_list:
			print("=" * 50)
			print(f"举报ID:{item['report_id']}")
			print(f"举报内容:{item['discussion_content']}")
			print(f"所属板块:{item['board_name']}")
			print(f"被举报人:{item['discussion_user_nickname']}")
			print(f"举报原因:{item['reason_content']}")
			print(f"举报时间:{item['created_at']}")
			print("-" * 50)
			while True:
				choice = input("选择操作: D:删除评论, S:禁言7天, P:通过")
				if choice == "D":
					self.whale_motion.handle_discussion_report(report_id=item["report_id"], status="DELETE", admin_id=admin_id)
					break
				if choice == "S":
					self.whale_motion.handle_discussion_report(report_id=item["report_id"], status="MUTE_SEVEN_DAYS", admin_id=admin_id)
					break
				if choice == "P":
					self.whale_motion.handle_discussion_report(report_id=item["report_id"], status="PASS", admin_id=admin_id)
					break
				print("无效输入")


# "POST_COMMENT",
# "POST_COMMENT_DELETE_FEEDBACK",
# "POST_DELETE_FEEDBACK",
# "POST_DISCUSSION_LIKED",
# "POST_REPLY",
# "POST_REPLY_AUTHOR",
# "POST_REPLY_REPLY",
# "POST_REPLY_REPLY_AUTHOR",
# "POST_REPLY_REPLY_FEEDBACK",
# "WORK_COMMENT",路人a评论{user}的作品
# "WORK_DISCUSSION_LIKED",
# "WORK_LIKE",
# "WORK_REPLY",路人a评论{user}在某个作品的评论
# "WORK_REPLY_AUTHOR",路人a回复{user}作品下路人b的某条评论
# "WORK_REPLY_REPLY",路人a回复{user}作品下路人b/a的评论下{user}的回复
# "WORK_REPLY_REPLY_AUTHOR",路人a回复{user}作品下路人b/a对某条评论的回复
# "WORK_REPLY_REPLY_FEEDBACK",路人a回复{user}在某个作品下发布的评论的路人b/a的回复
# "WORK_SHOP_REPL"
# "WORK_SHOP_USER_LEAVE",
