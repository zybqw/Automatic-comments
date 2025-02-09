"""显式导入所有模块,确保 Nuitka 能够识别"""

from typing import Any

# 显式导入所有 API 模块
from .api import community, edu, forum, library, pickduck, shop, user, work

# 显式导入核心模块和工具
from .core import client
from .utils import data

# 创建模块列表,确保导入不被优化掉
__modules__: list[Any] = [
	community,
	edu,
	forum,
	library,
	pickduck,
	shop,
	user,
	work,
	client,
	data,
]

__all__ = [
	"client",
	"community",
	"data",
	"edu",
	"forum",
	"library",
	"pickduck",
	"shop",
	"user",
	"work",
]
