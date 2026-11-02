"""Minimal Zabbix JSON-RPC client (standard library only).

Reads ../lab.env: ZBX_URL (default http://127.0.0.1:8080/api_jsonrpc.php), ZBX_USER, ZBX_ADMIN_PASSWORD.
Secrets are never printed.
"""
import json
import os
import pathlib
import urllib.request

ENV_FILE = pathlib.Path(__file__).resolve().parent.parent / "lab.env"


def load_env(path=ENV_FILE):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


class ZabbixError(RuntimeError):
    pass


class Zabbix:
    def __init__(self, url=None, token=None):
        env = load_env()
        self.url = url or env.get("ZBX_URL", "http://127.0.0.1:8080/api_jsonrpc.php")
        self.token = token
        self._id = 0

    def call(self, method, params=None, auth=True):
        self._id += 1
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": self._id}
        headers = {"Content-Type": "application/json-rpc"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(self.url, json.dumps(body).encode(), headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.load(resp)
        if "error" in out:
            err = out["error"]
            raise ZabbixError(f"{method}: {err.get('message')} {err.get('data')}")
        return out["result"]

    def login(self, user, password):
        self.token = self.call("user.login", {"username": user, "password": password}, auth=False)
        return self

    @classmethod
    def from_env(cls):
        env = load_env()
        return cls().login(env.get("ZBX_USER", "Admin"), env["ZBX_ADMIN_PASSWORD"])
