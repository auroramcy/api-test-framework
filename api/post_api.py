# -*- coding: utf-8 -*-
"""文章 / 评论模块接口。

原先 create_post / delete_post 挂在 UserApi 上，接口和模块对不上；
按「一个模块一个类」拆出来，接口归属清晰，新增接口时不用回头改别的类。
"""
from utils.request_util import RequestUtil


class PostApi:
    def __init__(self, client: "RequestUtil | None" = None):
        self.client = client or RequestUtil()

    def list_posts(self, user_id: "int | None" = None):
        """按作者过滤文章；user_id 为 None 时取全量。"""
        params = {"userId": user_id} if user_id is not None else None
        return self.client.get("/posts", params=params)

    def get_post(self, post_id):
        return self.client.get(f"/posts/{post_id}")

    def create_post(self, payload: dict):
        return self.client.post("/posts", json=payload)

    def delete_post(self, post_id):
        return self.client.delete(f"/posts/{post_id}")

    def list_comments(self, post_id):
        return self.client.get("/comments", params={"postId": post_id})
