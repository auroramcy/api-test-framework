# -*- coding: utf-8 -*-
"""请求封装层：统一 session、超时、重试、日志，业务层不直接碰 requests。"""
import logging
import re
import time

import requests

from config.setting import Settings, get_settings
from utils.recorder import Exchange, recorder

logger = logging.getLogger(__name__)

_WS = re.compile(r"\s+")
MAX_LOG_BODY = 300
# 只有幂等方法才自动重试，避免重复下单这类副作用
IDEMPOTENT = {"GET", "HEAD", "PUT", "DELETE", "OPTIONS"}


def _brief(text: str) -> str:
    """把多行响应压成一行再截断，避免一条日志刷满整屏。"""
    flat = _WS.sub(" ", text or "").strip()
    if len(flat) > MAX_LOG_BODY:
        flat = flat[:MAX_LOG_BODY] + f"...(共 {len(text)} 字符)"
    return flat


class RequestUtil:
    def __init__(
        self,
        base_url: "str | None" = None,
        timeout: "float | None" = None,
        retries: "int | None" = None,
        headers: "dict | None" = None,
        settings: "Settings | None" = None,
    ):
        conf = settings or get_settings()
        self.settings = conf
        self.base_url = (base_url or conf.base_url).rstrip("/")
        self.timeout = conf.timeout if timeout is None else timeout
        self.retries = conf.retries if retries is None else retries
        self.session = requests.Session()
        self.session.headers.update(headers if headers is not None else conf.headers)
        self.session.verify = conf.verify_ssl

    def _send(self, method: str, url: str, **kwargs) -> requests.Response:
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self.session.request(method, url, **kwargs)
            except requests.RequestException as exc:
                if attempt > self.retries or method not in IDEMPOTENT:
                    logger.error("请求异常（已试 %d 次）%s %s: %s", attempt, method, url, exc)
                    recorder.add(Exchange(method=method, url=url,
                                          request=self._request_brief(kwargs), error=str(exc)))
                    raise
                logger.warning("请求异常，第 %d 次重试：%s %s", attempt, method, url)
                time.sleep(0.5 * attempt)
                continue

            # 5xx 视为服务端临时故障，幂等方法重试
            if resp.status_code >= 500 and attempt <= self.retries and method in IDEMPOTENT:
                logger.warning("服务端 %d，第 %d 次重试：%s %s",
                               resp.status_code, attempt, method, url)
                time.sleep(0.5 * attempt)
                continue
            return resp

    @staticmethod
    def _request_brief(kwargs: dict) -> dict:
        """只留可读的部分，避免把整个 session 对象塞进报告。"""
        return {
            key: kwargs[key]
            for key in ("params", "json", "data", "headers")
            if kwargs.get(key)
        }

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        method = method.upper()
        logger.info("REQ %s %s params=%s body=%s",
                    method, url,
                    _brief(str(kwargs.get("params") or "")),
                    _brief(str(kwargs.get("json") or kwargs.get("data") or "")))
        resp = self._send(method, url, **kwargs)
        logger.info("RES %s %.0fms %s", resp.status_code,
                    resp.elapsed.total_seconds() * 1000, _brief(resp.text))
        # 记录完整响应体（不截断）：失败时要看的就是它
        recorder.add(Exchange(
            method=method, url=url,
            request=self._request_brief(kwargs),
            status=resp.status_code,
            elapsed_ms=resp.elapsed.total_seconds() * 1000,
            response_text=resp.text[:4000],
        ))
        return resp

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def close(self):
        self.session.close()
