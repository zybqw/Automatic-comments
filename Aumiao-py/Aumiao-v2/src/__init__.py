from .app import acquire, data, file, tool
from .client import community, post, shop, union, user, work

# 定义版本、作者和团队信息
version = "2.0.0"
author = "Aurzex"
team = "Aumiao Team"
team_members = "Aurzex, MoonLeaaaf, Nomen, MiTao"

# 实例化app模块中的类
app_acquire = acquire.CodeMaoClient()
app_data = data.CodeMaoData()
app_file = file.CodeMaoFile()
app_tool = tool.CodeMaoProcess()

# 实例化client模块中的类
client_community = community.Community()
client_post = post.Post()
client_shop = shop.Shop()
client_union_community = union.CommunityUnion()
client_union_work = union.WorkUnion()
client_user = user.User()
client_work = work.Work()
