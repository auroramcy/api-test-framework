# -*- coding: utf-8 -*-
"""请求 / 响应记录器：用例失败时，把这次跑过的 HTTP 往来附到报告里。

为什么需要：
断言失败时报告里只有一行 AssertionError，看不到实际返回了什么，
要定位就得去翻日志、重新跑一遍。把本次请求响应直接挂在失败报告上，
「失败现场」和「报告」在同一处。

用法：RequestUtil 每次请求自动记录；conftest 在每条用例前清空、
失败时把快照写进 HTML 报告与终端输出。
"""
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Exchange:
    """一次 HTTP 往来的快照。"""

    method: str
    url: str
    request: Dict[str, Any] = field(default_factory=dict)
    status: Optional[int] = None
    elapsed_ms: Optional[float] = None
    response_text: str = ""
    error: Optional[str] = None

    def render(self) -> str:
        lines = [f"{self.method} {self.url}"]
        if self.request:
            lines.append(f"  请求参数: {self.request}")
        if self.error:
            lines.append(f"  异常: {self.error}")
        else:
            lines.append(f"  响应: {self.status}（{self.elapsed_ms or 0:.0f}ms）")
            lines.append(f"  响应体: {self.response_text}")
        return "\n".join(lines)


class Recorder:
    def __init__(self) -> None:
        self._items: List[Exchange] = []
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._items.clear()

    def add(self, exchange: Exchange) -> None:
        with self._lock:
            self._items.append(exchange)

    def snapshot(self) -> List[Exchange]:
        with self._lock:
            return list(self._items)

    def render(self) -> str:
        items = self.snapshot()
        if not items:
            return ""
        return "\n\n".join(f"#{index} {ex.render()}" for index, ex in enumerate(items, start=1))


recorder = Recorder()
