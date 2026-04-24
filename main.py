"""
AstrBot plugin: print reasoning content extracted by AstrBot core.

目标：
1. 直接读取 AstrBot 已提取好的 resp.reasoning_content。
2. 不限定具体模型厂商，只要 provider 已把思考标准化到 LLMResponse 中就能打印。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import LLMResponse, ProviderRequest
from astrbot.api.star import Context, Star


class ThinkingExtractor(Star):
    """打印被框架过滤掉、但已提取到 LLMResponse 的思考内容。"""

    def __init__(self, context: Context):
        super().__init__(context)
        self._request_meta: dict[str, dict[str, Any]] = {}
        logger.info("=" * 72)
        logger.info("[ReasoningLogger] plugin loaded")
        logger.info("=" * 72)

    @filter.on_llm_request()
    async def capture_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """记录当前请求的基础信息，方便和响应日志对应。"""
        request_info = self._build_request_info(req)
        self._request_meta[self._event_key(event)] = request_info

        logger.info("=" * 72)
        logger.info("[ReasoningLogger][Request]")
        logger.info(f"time: {self._now()}")
        logger.info(f"user_message: {event.message_str}")
        for key, value in request_info.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 72)

    @filter.on_llm_response()
    async def extract_thinking(self, event: AstrMessageEvent, resp: LLMResponse):
        """从 LLMResponse 中读取 AstrBot 已提取好的 reasoning_content。"""
        event_key = self._event_key(event)
        request_info = self._request_meta.get(event_key, {})
        reasoning_content = getattr(resp, "reasoning_content", "") or ""
        reasoning_signature = getattr(resp, "reasoning_signature", None)
        raw_completion = getattr(resp, "raw_completion", None)
        usage_info = getattr(resp, "usage", None)
        completion_text = self._get_completion_text(resp)

        logger.info("=" * 72)
        logger.info("[ReasoningLogger][Response]")
        logger.info(f"time: {self._now()}")
        logger.info(f"user_message: {event.message_str}")
        if request_info:
            for key, value in request_info.items():
                logger.info(f"request_{key}: {value}")
        logger.info(f"completion_text_length: {len(completion_text)}")
        logger.info(f"reasoning_length: {len(reasoning_content)}")

        if usage_info is not None:
            logger.info(f"usage: {usage_info}")

        if reasoning_signature:
            logger.info(f"reasoning_signature: {reasoning_signature}")

        if reasoning_content.strip():
            logger.info("-" * 72)
            logger.info("[reasoning_content]")
            logger.info(reasoning_content)
        else:
            logger.info("reasoning_content is empty")

        if raw_completion is not None:
            raw_type = type(raw_completion).__name__
            logger.info(f"raw_completion_type: {raw_type}")

        logger.info("=" * 72)

    @filter.after_message_sent()
    async def cleanup(self, event: AstrMessageEvent):
        """消息完成后清理缓存。"""
        self._request_meta.pop(self._event_key(event), None)

    async def terminate(self):
        logger.info("=" * 72)
        logger.info("[ReasoningLogger] plugin unloaded")
        logger.info("=" * 72)

    def _build_request_info(self, req: ProviderRequest) -> dict[str, Any]:
        info: dict[str, Any] = {}

        for attr_name in ("model", "provider", "temperature", "max_tokens"):
            if hasattr(req, attr_name):
                try:
                    value = getattr(req, attr_name)
                except Exception:
                    continue
                if value not in (None, "", {}, []):
                    info[attr_name] = value

        for attr_name in ("metadata", "extra_body", "request_kwargs", "kwargs"):
            if hasattr(req, attr_name):
                try:
                    value = getattr(req, attr_name)
                except Exception:
                    continue
                if value not in (None, "", {}, []):
                    info[attr_name] = value

        return info

    def _get_completion_text(self, resp: LLMResponse) -> str:
        for attr_name in ("completion_text", "text", "response_text", "content"):
            value = getattr(resp, attr_name, None)
            if isinstance(value, str):
                return value
        return ""

    def _event_key(self, event: AstrMessageEvent) -> str:
        message_id = getattr(getattr(event, "message_obj", None), "message_id", None)
        if message_id:
            return str(message_id)
        return f"{event.unified_msg_origin}:{event.message_str}"

    def _now(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
