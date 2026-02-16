"""AI 网关：为未来接入不同大模型提供统一接口。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class AIConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


def load_ai_config() -> Optional[AIConfig]:
    """从环境变量读取 AI 配置。"""
    provider = os.getenv("CRUSHCOURT_AI_PROVIDER", "").strip().lower()
    if not provider:
        return None

    api_key = os.getenv("CRUSHCOURT_AI_API_KEY", "").strip()
    base_url = os.getenv("CRUSHCOURT_AI_BASE_URL", "").strip()
    model = os.getenv("CRUSHCOURT_AI_MODEL", "").strip()

    if not (api_key and base_url and model):
        return None

    return AIConfig(provider=provider, base_url=base_url.rstrip("/"), api_key=api_key, model=model)


def generate_task_suggestion(user_input: str) -> str:
    """生成任务建议。支持 OpenAI-compatible 接口（DeepSeek/Kimi 开放平台等）。"""
    config = load_ai_config()
    if config is None:
        return (
            "AI 未配置。请设置环境变量：CRUSHCOURT_AI_PROVIDER / CRUSHCOURT_AI_BASE_URL / "
            "CRUSHCOURT_AI_API_KEY / CRUSHCOURT_AI_MODEL。"
        )

    # 当前统一走 OpenAI-compatible chat completions，便于接入 DeepSeek/Kimi 等平台
    url = f"{config.base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是情侣协作任务助手。请基于输入输出："
                    "1) 今日优先级任务清单（不超过5条）；"
                    "2) 健康提醒建议（2条）；"
                    "3) 赛事/约会安排建议（2条）；"
                    "4) 可执行的最小下一步。"
                ),
            },
            {"role": "user", "content": user_input},
        ],
        "temperature": 0.7,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
