#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦当劳 MCP Streamable HTTP 客户端（零依赖，仅标准库）。
仅做传输层封装：initialize / tools/list / tools/call。
安全约定：本文件只负责"发请求、收响应"，绝不在此处自动触发任何写操作；
是否允许写操作由调用方依据环境变量 MCD_READ_ONLY / MCD_ALLOW_WRITE 决定。
"""
import json
import urllib.request
import urllib.error


class McdMcpError(Exception):
    pass


def _parse_body(raw: bytes):
    text = raw.decode("utf-8", errors="replace")
    if "data:" in text:
        out = None
        for part in text.split("\n"):
            part = part.strip()
            if part.startswith("data:"):
                payload = part[len("data:"):].strip()
                if payload and payload != "[DONE]":
                    try:
                        out = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
        return out
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class McdMCP:
    def __init__(self, endpoint: str, token: str, timeout: int = 30):
        self.endpoint = endpoint
        self.token = token
        self.timeout = timeout
        self.session_id = None
        self._tools_cache = None

    def _post(self, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.token}",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(
            self.endpoint, data=data, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
                new_sid = resp.headers.get("Mcp-Session-Id")
                if new_sid:
                    self.session_id = new_sid
                return _parse_body(body)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise McdMcpError(f"HTTP {e.code}: {detail[:300]}") from e
        except urllib.error.URLError as e:
            raise McdMcpError(f"网络不可达: {e.reason}") from e

    def connect(self):
        init = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcd-points-advisor", "version": "0.1.0"},
            },
        }
        res = self._post(init)
        if not res or res.get("error"):
            raise McdMcpError(f"initialize 失败: {res}")
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        return res

    def list_tools(self):
        if self._tools_cache is None:
            res = self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            self._tools_cache = (res or {}).get("result", {}).get("tools", [])
        return self._tools_cache

    def has_tool(self, name: str) -> bool:
        return any(t.get("name") == name for t in self.list_tools())

    def call_tool(self, name: str, arguments: dict = None):
        payload = {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        res = self._post(payload)
        if not res or res.get("error"):
            raise McdMcpError(f"tools/call {name} 失败: {res}")
        return res.get("result", {})


def extract_text(result: dict) -> str:
    """从 tools/call 的 result 中抽取合并文本内容。"""
    parts = []
    for c in result.get("content", []):
        if isinstance(c, dict) and c.get("type") == "text":
            parts.append(c.get("text", ""))
    return "\n".join(parts)


def _try_parse_slice(s: str, i: int, j: int):
    try:
        return json.loads(s[i:j + 1])
    except (json.JSONDecodeError, ValueError):
        return None


def extract_json(text: str):
    """尽力从返回文本中抽取最大的合法 JSON 对象/数组。
    兼容三种形态：纯 JSON、```json 围栏、JSON 前带大段说明文字。"""
    if not text:
        return None
    s = text.strip()
    import re
    # 1) ```json ... ``` 围栏
    m = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # 2) 整体可解析
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # 3) 在所有 {…} / […] 切片里找体积最大、能解析者
    best = None
    best_len = 0
    for opener, closer in (("{", "}"), ("[", "]")):
        opens = [k for k, c in enumerate(s) if c == opener]
        closes = [k for k, c in enumerate(s) if c == closer]
        for i in opens:
            # 从最远的闭合括号往前试，命中即记录
            for j in reversed(closes):
                if j > i:
                    obj = _try_parse_slice(s, i, j)
                    if obj is not None and (j - i + 1) > best_len:
                        best = obj
                        best_len = j - i + 1
                    break
    return best
