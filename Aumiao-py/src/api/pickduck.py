import json

from src.base import acquire
from src.base.decorator import singleton

OK_CODE = 200


@singleton
class PickDuck:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	def cookie_out(self, cookies: str) -> bool:
		data = json.dumps({"cookie": cookies, "do": "apply"})
		response = self.acquire.send_request(url="https://shequ.pgaot.com/?mod=bcmcookieout", method="post", data=data)
		return response.status_code == OK_CODE
