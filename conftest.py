# -*- coding: utf-8 -*-
"""框架级钩子：环境切换、日志目录、公共 fixture、失败时附带 HTTP 往来。"""
import logging
import os
from pathlib import Path

import pytest

from config.setting import configure, get_settings

LOG_DIR_NAME = "logs"
logger = logging.getLogger(__name__)


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
