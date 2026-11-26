# -*- coding: utf-8 -*-
"""文章 / 评论模块用例：除了字段校验，补上「业务规则」类断言。

只断言 status_code 的用例说明不了问题——接口返回 200 但数据是错的，测试照样绿。
这里校验的是接口承诺的业务约束：按作者过滤后，每一条的 userId 都必须等于请求参数。
"""
import logging

import pytest

from api.post_api import PostApi
from utils.assertions import assert_all, assert_fields, assert_status

logger = logging.getLogger(__name__)


class TestPost:
    @pytest.mark.smoke
    def test_create_post(self, post_api: PostApi):
        payload = {"title": "qa", "body": "demo", "userId": 1}
        resp = post_api.create_post(payload)
        assert_status(resp, 201, "创建文章")
        body = resp.json()
        assert_fields(body, {"id": int, "title": str, "body": str, "userId": int}, "创建文章")
        assert body["title"] == payload["title"], "标题未按提交内容回显"
        assert body["userId"] == payload["userId"], "userId 未按提交内容回显"

    def test_list_posts_filtered_by_user(self, post_api: PostApi):
        """业务规则：按 userId 过滤，返回的每一条都必须属于该用户。"""
        resp = post_api.list_posts(user_id=1)
        assert_status(resp, 200, "按作者过滤文章")
        body = resp.json()
        assert_all(body, lambda p: p["userId"] == 1,
                   "过滤结果中每条文章都应以 userId=1 归属", "按作者过滤文章")

    def test_comments_belong_to_post(self, post_api: PostApi):
        """业务规则：按 postId 过滤评论，返回的每一条都必须挂在该文章下。"""
        resp = post_api.list_comments(post_id=1)
        assert_status(resp, 200, "按文章过滤评论")
        body = resp.json()
        assert_all(body, lambda c: c["postId"] == 1,
                   "过滤结果中每条评论都应归属于 postId=1", "按文章过滤评论")

    def test_delete_post(self, post_api: PostApi):
        """删除存在的文章应返回 200。"""
        assert_status(post_api.delete_post(1), 200, "删除存在文章")

    @pytest.mark.boundary
    def test_delete_non_existent_is_lenient(self, post_api: PostApi):
        """锁定演示接口的行为：删不存在的 id 也返回 200。

        真实系统这里应当是 404，否则「删除成功」和「根本没这条数据」无法区分。
        这条用例的作用是把这个差异写进代码：接口行为一旦变成 404，用例会立刻失败并提醒更新预期。
        """
        resp = post_api.delete_post(999999)
        assert_status(resp, 200, "删除不存在文章（演示接口当前行为）")
        logger.warning("演示接口对不存在的 id 也返回 200，真实系统应为 404")
