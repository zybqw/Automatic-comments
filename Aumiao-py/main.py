import src


def login() -> None:
	identity = input("请输入用户名: ")
	password = input("请输入密码: ")

	# 登录并获取数据
	src.community.Login().login_token(identity=identity, password=password)
	data = src.user.Obtain().get_data_details()

	# 使用 update 方法更新字典中的数据
	account_data = src.data.CodeMaoData().data
	account_data.update(
		{
			"ACCOUNT_DATA": {
				"identity": "identity",
				"password": "password",
				"id": data["id"],
				"nickname": data["nickname"],
				"create_time": data["create_time"],
				"description": data["description"],
				"author_level": data["author_level"],
			},
		},
	)


def clear_comments() -> None:
	source = input("请输入来源类型 (work/post): ")
	action_type = input("请输入操作类型 (ads/duplicates/blacklist): ")
	if source not in ["work", "post"] or action_type not in ["ads", "duplicates", "blacklist"]:
		print("无效的输入")
		return
	src.client.Motion().clear_comments(source=source, action_type=action_type)  # type: ignore  # noqa: PGH003


def clear_red_point() -> None:
	method = input("请输入方法 (nemo/web): ")
	if method not in ["nemo", "web"]:
		print("无效的输入")
		return
	src.client.Motion().clear_red_point(method=method)  # type: ignore  # noqa: PGH003


def reply_work() -> None:
	src.client.Motion().reply_work()


def logout() -> None:
	method = input("请输入方法 (web): ")
	if method != "web":
		print("无效的输入")
		return
	src.community.Login().logout(method=method)


def main() -> None:
	src.client.Index().index()
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
