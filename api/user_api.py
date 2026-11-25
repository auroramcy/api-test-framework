# -*- coding: utf-8 -*-
"""业务接口层：一个模块一个类，只写「哪个接口、要什么参数」。"""
from utils.request_util import RequestUtil


class UserApi:
    def __init__(self):
        self.client = RequestUtil()

    def list_users(self):
        return self.client.get("/users")

    def get_user(self, user_id):
        return self.client.get(f"/users/{user_id}")

    def create_post(self, payload):
        return self.client.post("/posts", json=payload)

    def delete_post(self, post_id):
        return self.client.delete(f"/posts/{post_id}")
