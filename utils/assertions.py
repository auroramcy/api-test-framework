# -*- coding: utf-8 -*-
"""通用断言：把「期望什么、实际是什么」写进失败信息里。

裸 assert 失败时只有一行 AssertionError，看不到响应内容，
定位还得回去翻日志。这里统一把关键信息拼进断言消息。
"""
import re
from typing import Callable, Dict, Iterable, Sequence, Union

TypeSpec = Union[type, Sequence[type]]


def assert_status(resp, expected: int, note: str = "") -> None:
    """校验状态码，失败时带上响应体片段。"""
    prefix = f"{note} " if note else ""
    assert resp.status_code == expected, (
        f"{prefix}期望状态码 {expected}，实际 {resp.status_code}；"
        f"url={resp.url} body={resp.text[:300]!r}"
    )


def assert_fields(payload: dict, expected: Dict[str, TypeSpec], note: str = "") -> None:
    """校验字段存在性与类型。expected 形如 {"id": int, "name": str}。"""
    prefix = f"{note} " if note else ""
    assert isinstance(payload, dict), f"{prefix}期望返回对象，实际 {type(payload).__name__}"
    missing = [key for key in expected if key not in payload]
    assert not missing, f"{prefix}缺少字段 {missing}，实际字段 {sorted(payload)}"

    wrong = {
        key: f"{type(payload[key]).__name__} ≠ {spec}"
        for key, spec in expected.items()
        if not isinstance(payload[key], spec)
    }
    assert not wrong, f"{prefix}字段类型不符：{wrong}"


def assert_all(items: Iterable[dict], predicate: Callable[[dict], bool],
               desc: str, note: str = "") -> None:
    """校验集合里每一条都满足业务规则，失败时给出首个反例。"""
    prefix = f"{note} " if note else ""
    items = list(items)
    for index, item in enumerate(items):
        if not predicate(item):
            raise AssertionError(
                f"{prefix}{desc} 不成立；首个反例 index={index} item={item}"
            )
    assert items, f"{prefix}{desc} 无数据可校验（集合为空）"


def assert_match(value, pattern: str, desc: str, note: str = "") -> None:
    """正则校验单个字段，用于邮箱、域名这类格式约束。"""
    prefix = f"{note} " if note else ""
    assert re.search(pattern, str(value)), f"{prefix}{desc} 格式不符：{value!r} 不匹配 {pattern}"
