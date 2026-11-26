# -*- coding: utf-8 -*-
"""框架级钩子：日志目录准备。

日志本身由 pytest.ini 的 log_cli / log_file 接管；这里只负责补一件事——
pytest 的 log_file 会自己创建文件，但不会创建父目录，目录不存在时首次运行会直接报错。
"""
from pathlib import Path

import pytest

LOG_DIR_NAME = "logs"


def pytest_configure(config: pytest.Config) -> None:
    Path(config.rootpath, LOG_DIR_NAME).mkdir(exist_ok=True)
