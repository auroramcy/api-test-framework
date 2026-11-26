# -*- coding: utf-8 -*-
"""用例层：只写业务断言，不写请求细节。"""
import logging
import os

import pytest
import yaml

from api.user_api import UserApi

logger = logging.getLogger(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "user.yaml")
with open(DATA_PATH, encoding="utf-8") as f:
    DATA = yaml.safe_load(f)


class TestUser:
    def setup_class(self):
        self.api = UserApi()

    @pytest.mark.smoke
    def test_list_users(self):
        resp = self.api.list_users()
        assert resp.status_code == 200
        assert len(resp.json()) == 10

    @pytest.mark.parametrize("case", DATA["users"], ids=lambda c: c["case_id"])
    def test_get_user(self, case):
        logger.info("用例 %s：%s", case["case_id"], case["title"])
        resp = self.api.get_user(case["user_id"])
        assert resp.status_code == 200
        assert resp.json()["name"] == case["expect_name"]

    def test_get_user_not_found(self):
        resp = self.api.get_user(9999)
        assert resp.status_code == 404

    def test_create_post(self):
        resp = self.api.create_post({"title": "qa", "body": "demo", "userId": 1})
        assert resp.status_code == 201
        assert resp.json()["title"] == "qa"
