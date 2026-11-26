# -*- coding: utf-8 -*-
"""框架级钩子：环境切换、日志目录、公共 fixture。

设计取舍：
- fixture 全部 session 级：一个 session 复用一个 requests.Session，
  连接池复用、headers 只注入一次；用例只声明需要什么，不关心怎么造。
- 用例里不再出现 UserApi() 这种直接实例化，避免每个测试类各自建连接。
"""
import logging
import os
from pathlib import Path

import pytest

from api.post_api import PostApi
from api.user_api import UserApi
from config.setting import Settings, configure, get_settings
from utils.recorder import recorder
from utils.request_util import RequestUtil

LOG_DIR_NAME = "logs"
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------- 启动钩子

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="运行环境：dev / test / prod，默认取环境变量 TEST_ENV，再退回 environments.yaml 的 default",
    )


def pytest_configure(config: pytest.Config) -> None:
    # pytest 的 log_file 会创建文件但不会创建父目录
    Path(config.rootpath, LOG_DIR_NAME).mkdir(exist_ok=True)
    # 环境切换：--env > TEST_ENV > yaml 的 default
    configure(config.getoption("--env") or os.getenv("TEST_ENV"))


def pytest_sessionstart(session: pytest.Session) -> None:
    # 放在 sessionstart：pytest 的日志 handler 在 configure 阶段之后才就绪，
    # 在 pytest_configure 里打的日志会被直接丢掉。
    settings = get_settings()
    logger.info("当前环境：%s → %s（timeout=%ss, retries=%s）",
                settings.name, settings.base_url, settings.timeout, settings.retries)


# ------------------------------------------------------------------ fixture

@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def http(settings: Settings):
    """全 session 共用一个 HTTP 客户端，结束时关闭连接池。"""
    client = RequestUtil(settings=settings)
    yield client
    client.close()


@pytest.fixture(scope="session")
def user_api(http: RequestUtil) -> UserApi:
    return UserApi(http)


@pytest.fixture(scope="session")
def post_api(http: RequestUtil) -> PostApi:
    return PostApi(http)


# ------------------------------------------------------- 失败时挂 HTTP 往来

@pytest.fixture(autouse=True)
def _reset_recorder():
    """每条用例开始前清空记录，保证失败报告里只有本次的请求。"""
    recorder.reset()
    yield


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    if not (report.when == "call" and report.failed):
        return

    traffic = recorder.render()
    if not traffic:
        return

    # 终端：失败详情里多一节，不用再翻日志
    report.sections.append(("HTTP 往来（本次用例）", traffic))

    # HTML 报告：挂成可折叠的文本附件
    try:
        from pytest_html import extras
    except ImportError:  # 没装 pytest-html 时只保留终端输出
        return
    report.extras = list(getattr(report, "extras", [])) + [
        extras.text(traffic, name="HTTP 往来")
    ]
