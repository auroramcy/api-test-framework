# -*- coding: utf-8 -*-
"""请求封装层：统一 session、超时、日志，业务层不直接碰 requests。"""
import logging

import requests

from config.setting import BASE_URL, TIMEOUT

logger = logging.getLogger(__name__)


class RequestUtil:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", TIMEOUT)
        logger.info("REQ %s %s", method.upper(), url)
        resp = self.session.request(method, url, **kwargs)
        logger.info("RES %s %s", resp.status_code, resp.text[:200])
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
