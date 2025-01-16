import json
from typing import Literal

from .decorator import singleton


@singleton
class CodeMaoFile:
	# 检查文件
	def check_file(self, path: str) -> bool:
		try:
			with open(path):
				return True
		except OSError as err:
			print(err)
			return False

	def validate_json(self, json_string):
		try:
			data = json.loads(json_string)
			return data
		except ValueError as err:
			print(err)
			return False

	# 从配置文件加载账户信息
	def file_load(self, path, type: Literal["txt", "json"]) -> dict | str:
		self.check_file(path=path)
		with open(file=path, encoding="utf-8") as file:
			data: str = file.read()
			if type == "json":
				return json.loads(data) if data else {}
			if type == "txt":
				return data
			else:
				raise ValueError("不支持的读取方法")

	# 将文本写入到指定文件
	def file_write(
		self,
		path: str,
		content: str | dict | list[str],
		method: str = "w",
	) -> None:
		# self.check_file(path=path)
		with open(file=path, mode=method, encoding="utf-8") as file:
			if isinstance(content, str):
				file.write(content + "\n")
			elif isinstance(content, dict):
				file.write(json.dumps(obj=content, ensure_ascii=False, indent=4, sort_keys=True))
			elif isinstance(content, list):
				for line in content:
					file.write(line + "\n")
			else:
				raise ValueError("不支持的写入方法")
