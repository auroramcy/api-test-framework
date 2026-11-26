# -*- coding: utf-8 -*-
"""请求封装层：统一 session、超时、日志，业务层不直接碰 requests。"""
import logging
import re

import requests

from config.setting import BASE_URL, TIMEOUT

logger = logging.getLogger(__name__)

_WS = re.compile(r"\s+")
MAX_LOG_BODY = 300


def _brief(text: str) -> str:
    """把多行响应压成一行再截断，避免一条日志刷满整屏。"""
    flat = _WS.sub(" ", text or "").strip()
    if len(flat) > MAX_LOG_BODY:
        flat = flat[:MAX_LOG_BODY] + f"...(共 {len(text)} 字符)"
    return flat


class RequestUtil:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", TIMEOUT)
        logger.info("REQ %s %s params=%s body=%s",
                    method.upper(), url,
                    _brief(str(kwargs.get("params") or "")),
                    _brief(str(kwargs.get("json") or kwargs.get("data") or "")))
        resp = self.session.request(method, url, **kwargs)
        logger.info("RES %s %.0fms %s", resp.status_code,
                    resp.elapsed.total_seconds() * 1000, _brief(resp.text))
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
