from src.utils import acquire
from src.utils.acquire import HTTPSTATUS
from src.utils.decorator import singleton


@singleton
class PickDuck:
	def __init__(self) -> None:
		self.acquire = acquire.CodeMaoClient()

	def cookie_out(self, cookies: str) -> bool:
		data = {"cookie": cookies, "do": "apply"}
		response = self.acquire.send_request(endpoint="https://shequ.pgaot.com/?mod=bcmcookieout", method="POST", payload=data)
		return response.status_code == HTTPSTATUS.OK
