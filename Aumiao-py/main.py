from src import *  # noqa: F403


def login() -> None:
	try:
		identity = input("请输入用户名: ")
		password = input("请输入密码: ")
		# 登录并获取数据
		community.Login().login_token(identity=identity, password=password)  # noqa: F405
		_data = user.Obtain().get_data_details()  # noqa: F405
		# 使用 update 方法更新字典中的数据
		account_data_manager = data.DataManager()  # noqa: F405
		account_data_manager.update(
			{
				"ACCOUNT_DATA": {
					"identity": identity,
					"password": "******",  # 不建议存储密码
					"id": _data["id"],
					"nickname": _data["nickname"],
					"create_time": _data["create_time"],
					"description": _data["description"],
					"author_level": _data["author_level"],
				},
			},
		)
	except Exception as e:
		print(f"登录失败: {e}")


def clear_comments() -> None:
	try:
		source = input("请输入来源类型 (work/post): ")
		action_type = input("请输入操作类型 (ads/duplicates/blacklist): ")
		if source not in ["work", "post"] or action_type not in ["ads", "duplicates", "blacklist"]:
			print("无效的输入")
			return
		client.Motion().clear_comments(source=source, action_type=action_type)  # type: ignore  # noqa: F405, PGH003
	except Exception as e:
		print(f"清除评论失败: {e}")


def clear_red_point() -> None:
	try:
		method = input("请输入方法 (nemo/web): ")
		if method not in ["nemo", "web"]:
			print("无效的输入")
			return
		client.Motion().clear_red_point(method=method)  # type: ignore  # noqa: F405, PGH003
	except Exception as e:
		print(f"清除邮箱红点失败: {e}")


def reply_work() -> None:
	try:
		client.Motion().reply_work()  # noqa: F405
	except Exception as e:
		print(f"自动回复失败: {e}")


def logout() -> None:
	try:
		method = input("请输入方法 (web): ")
		if method != "web":
			print("无效的输入")
			return
		community.Login().logout(method=method)  # noqa: F405
	except Exception as e:
		print(f"登出失败: {e}")


def main() -> None:
	client.Index().index()  # noqa: F405
	while True:
		print("\n请选择操作:")
		print("1. 登录")
		print("2. 清除评论")
		print("3. 清除邮箱红点")
		print("4. 自动回复")
		print("5. 登出")
		print("6. 退出")
		choice = input("请输入选择 (1-6): ")
		print("*" * 50)
		if choice == "1":
			login()
		elif choice == "2":
			clear_comments()
		elif choice == "3":
			clear_red_point()
		elif choice == "4":
			reply_work()
		elif choice == "5":
			logout()
		elif choice == "6":
			break
		else:
			print("无效的选择, 请重新输入")


if __name__ == "__main__":
	main()
	input("按任意键退出")
