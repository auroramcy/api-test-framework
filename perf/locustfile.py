# -*- coding: utf-8 -*-
"""Locust 性能场景：与接口自动化共用同一份环境配置。

设计取舍：
- 不重复写一套 URL：host 从 config/environments.yaml 取，和接口用例同源，
  避免「功能测试改了环境、性能测试忘了改」这类问题。
- 请求路径与 api/*_api.py 保持一致，功能场景和压测场景测的是同一批接口。
- 用 name= 给每条请求打标签，Locust 统计里按业务接口聚合，而不是按 URL 里的随机 id 散开。

用法：
    # 无界面快速验证（CI / 本地冒烟）
    locust -f perf/locustfile.py --headless -u 10 -r 2 -t 30s --only-summary

    # 打开 Web UI 调参
    locust -f perf/locustfile.py

    # 导出报告
    locust -f perf/locustfile.py --headless -u 20 -r 5 -t 60s --html reports/perf.html
"""
import os
import random
import sys
from pathlib import Path

# 允许直接 `locust -f perf/locustfile.py` 时导入项目内的 config 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from locust import HttpUser, between, task  # noqa: E402

from config.setting import load  # noqa: E402

PERF_ENV = os.getenv("PERF_ENV", "test")
_settings = load(PERF_ENV)


class ApiUser(HttpUser):
    """模拟一个普通调用方：读多写少，权重按真实业务比例给。"""

    host = _settings.base_url
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        self.client.headers.update(_settings.headers)
        self.client.verify = _settings.verify_ssl
        self.client.timeout = _settings.timeout

    @task(5)
    def list_users(self) -> None:
        with self.client.get("/users", name="GET /users", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"期望 200，实际 {resp.status_code}")

    @task(3)
    def get_user_detail(self) -> None:
        user_id = random.randint(1, 10)
        with self.client.get(f"/users/{user_id}", name="GET /users/{id}",
                             catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"期望 200，实际 {resp.status_code}")
            elif not resp.json().get("id"):
                resp.failure("响应缺少 id 字段")

    @task(2)
    def list_posts_by_user(self) -> None:
        user_id = random.randint(1, 10)
        with self.client.get("/posts", params={"userId": user_id},
                             name="GET /posts?userId=", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"期望 200，实际 {resp.status_code}")
            elif not all(post.get("userId") == user_id for post in resp.json()):
                resp.failure("过滤结果包含其他作者的文章（业务规则被破坏）")

    @task(1)
    def create_post(self) -> None:
        payload = {"title": "perf", "body": "locust", "userId": 1}
        with self.client.post("/posts", json=payload, name="POST /posts",
                              catch_response=True) as resp:
            if resp.status_code != 201:
                resp.failure(f"期望 201，实际 {resp.status_code}")
