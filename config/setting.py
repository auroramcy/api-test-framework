# -*- coding: utf-8 -*-
"""环境配置：从 config/environments.yaml 读取，支持运行时切换环境。

切换方式（优先级从高到低）：
    pytest --env dev          # 命令行参数
    TEST_ENV=prod pytest      # 环境变量
    environments.yaml 里的 default
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml

_ENV_FILE = Path(__file__).with_name("environments.yaml")


@dataclass(frozen=True)
class Settings:
    """单个环境的全部配置。代码里只依赖这个对象，不依赖具体 URL。"""

    name: str
    base_url: str
    timeout: float = 10.0
    retries: int = 0
    verify_ssl: bool = True
    headers: Dict[str, Any] = field(default_factory=dict)


class _Holder:
    """进程内单例。conftest 在 session 启动时 configure()，用例通过 get() 读取。"""

    _current: "Settings | None" = None

    @classmethod
    def get(cls) -> Settings:
        if cls._current is None:
            cls._current = load()
        return cls._current

    @classmethod
    def configure(cls, env: "str | None" = None) -> Settings:
        cls._current = load(env)
        return cls._current

    @classmethod
    def reset(cls) -> None:
        cls._current = None


def load(env: "str | None" = None) -> Settings:
    """按优先级解析出最终生效的环境配置。"""
    raw = yaml.safe_load(_ENV_FILE.read_text(encoding="utf-8")) or {}
    name = env or os.getenv("TEST_ENV") or raw.get("default", "test")
    available = [k for k in raw if k != "default"]
    if name not in available:
        raise KeyError(f"未知环境 {name!r}，可选：{available}")
    return Settings(name=name, **raw[name])


def get_settings() -> Settings:
    return _Holder.get()


def configure(env: "str | None" = None) -> Settings:
    return _Holder.configure(env)
