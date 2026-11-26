# -*- coding: utf-8 -*-
"""业务接口层：一个模块一个类，只写「哪个接口、要什么参数」。"""
from utils.request_util import RequestUtil


class UserApi:
    """用户模块接口。

    client 由 conftest 的 session 级 fixture 注入，复用同一个连接池；
    单独使用时也可以不传，内部会自己建一个。
    """

    def __init__(self, client: "RequestUtil | None" = None):
        self.client = client or RequestUtil()

    def list_users(self):
        return self.client.get("/users")

    def get_user(self, user_id):
        return self.client.get(f"/users/{user_id}")
