import json
from pathlib import Path
from typing import Literal

from .decorator import singleton


@singleton
class CodeMaoFile:
	# 检查文件
	def check_file(self, path: Path) -> bool:
		try:
			with Path.open(path):
				return True
		except OSError as err:
			print(err)
			return False

	def validate_json(self, json_string: str | bytes) -> str | Literal[False]:
		try:
			return json.loads(json_string)
		except ValueError as err:
			print(err)
			return False

	# 从配置文件加载账户信息
	def file_load(self, path: Path, _type: Literal["txt", "json"]) -> dict | str:
		self.check_file(path=path)
		with Path.open(self=path, encoding="utf-8") as file:
			data: str = file.read()
			if _type == "json":
				return json.loads(data) if data else {}
			if _type == "txt":
				return data
			msg = "不支持的读取方法"
			raise ValueError(msg)

	# 将文本写入到指定文件
	def file_write(
		self,
		path: Path,
		content: str | dict | list[str],
		method: str = "w",
	) -> None:
		# self.check_file(path=path)
		with Path.open(self=path, mode=method, encoding="utf-8") as file:
			if isinstance(content, str):
				file.write(content + "\n")
			elif isinstance(content, dict):
				file.write(json.dumps(obj=content, ensure_ascii=False, indent=4, sort_keys=True))
			elif isinstance(content, list):
				for line in content:
					file.write(line + "\n")
			else:
				msg = "不支持的写入方法"
				raise TypeError(msg)
