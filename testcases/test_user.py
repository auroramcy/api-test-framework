# -*- coding: utf-8 -*-
"""用例层：只写业务断言，不写请求细节。

数据放在 data/user.yaml，用例通过 fixture 拿到 api 客户端，
参数化 ID 来自数据里的 case_id，失败时能直接看出是哪条数据。
"""
import logging
import os

import pytest
import yaml

from api.user_api import UserApi
from utils.assertions import assert_all, assert_fields, assert_match, assert_status

logger = logging.getLogger(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "user.yaml")
with open(DATA_PATH, encoding="utf-8") as f:
    DATA = yaml.safe_load(f)


class TestUser:
    @pytest.mark.smoke
    def test_list_users(self, user_api: UserApi):
        resp = user_api.list_users()
        assert_status(resp, 200, "用户列表")
        body = resp.json()
        assert isinstance(body, list), "用户列表应返回数组"
        # 不写死条数：条数是上游数据决定的，写死 10 会让用例随数据变化而假失败
        assert len(body) > 0, "用户列表不应为空"
        assert_all(body, lambda u: u.get("id") is not None, "每个用户都应带 id", "用户列表")

    @pytest.mark.parametrize("case", DATA["users"], ids=lambda c: c["case_id"])
    def test_get_user(self, user_api: UserApi, case):
        logger.info("用例 %s：%s", case["case_id"], case["title"])
        resp = user_api.get_user(case["user_id"])
        assert_status(resp, 200, case["case_id"])
        body = resp.json()
        assert_fields(
            body,
            {"id": int, "name": str, "username": str, "email": str,
             "phone": str, "website": str, "address": dict, "company": dict},
            case["case_id"],
        )
        assert body["id"] == case["user_id"], f"返回 id 与请求不符：{body['id']} ≠ {case['user_id']}"
        assert body["name"] == case["expect_name"], case["case_id"]
        assert_match(body["email"], r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$", "email", case["case_id"])

    def test_get_user_not_found(self, user_api: UserApi):
        resp = user_api.get_user(9999)
        assert_status(resp, 404, "不存在的用户")

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "case",
        DATA["boundary"] + DATA["abnormal"],
        ids=lambda c: c["case_id"],
    )
    def test_get_user_invalid_input(self, user_api: UserApi, case):
        """边界值与非法输入：接口必须挡住，而不是返回 500 或任何用户数据。

        这类用例最容易漏：只测正常 id 的话，越界和类型错误全靠运气。
        """
        logger.info("用例 %s：%s", case["case_id"], case["title"])
        resp = user_api.get_user(case["user_id"])
        assert_status(resp, case["expect_status"], case["case_id"])
        assert resp.text.strip() in ("{}", "[]"), (
            f"{case['case_id']} 非法 id 不应返回数据，实际：{resp.text[:200]!r}"
        )
