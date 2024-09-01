import logging
import requests
from typing import Callable, Dict
from enum import Enum, auto

logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %I:%M:%S'
                    )
logger = logging.getLogger('MessagePush')

class PushType(Enum):
    SERVER = auto()
    PUSHPLUS = auto()
    ANPUSH = auto()

class MessagePusher:
    def __init__(self, token: str, push_type: PushType = PushType.SERVER):
        """
        初始化MessagePusher实例。

        :param token: 用于消息推送的认证Token。
        :param push_type: 消息推送的类型，默认为PushType.SERVER。
        """
        self.token = token
        self.push_type = push_type
        self.push_functions: Dict[PushType, Callable[[str, str], None]] = {
            PushType.SERVER: self._push_server,
            PushType.PUSHPLUS: self._push_pushplus,
            PushType.ANPUSH: self._push_anpush
        }

    def push(self, title: str, content: str) -> None:
        """
        统一消息推送方法，根据初始化时指定的push_type调用对应的推送接口。

        :param title: 消息的标题。
        :param content: 消息的内容。
        """
        try:
            push_function = self.push_functions.get(self.push_type)
            if push_function is None:
                raise ValueError(f"未知的推送类型: {self.push_type}")
            push_function(title, content)
        except Exception as e:
            logger.error(f"消息推送失败: {str(e)}")

    def _push_server(self, title: str, content: str) -> None:
        """使用Server酱推送消息。"""
        url = f"https://sctapi.ftqq.com/{self.token}.send"
        params = {
            "title": title,
            "desp": content,
            "noip": 1
        }
        self._send_request(url, params, "Server酱")

    def _push_pushplus(self, title: str, content: str) -> None:
        """使用PushPlus推送消息。"""
        url = "https://www.pushplus.plus/send"
        params = {
            "token": self.token,
            "title": title,
            "template": "markdown",
            "content": content
        }
        self._send_request(url, params, "PushPlus")

    def _push_anpush(self, title: str, content: str) -> None:
        """使用AnPush推送消息。"""
        if not self.token:
            raise ValueError("Token 不能为空")

        token_parts = self.token.split('&')
        if len(token_parts) < 3:
            raise ValueError("Token 必须包含三个部分")

        url = f"https://api.anpush.com/push/{token_parts[0]}"
        params = {
            "title": title,
            "content": content,
            "channel": token_parts[1],
            "to": token_parts[2]
        }
        self._send_request(url, params, "AnPush")

    @staticmethod
    def _send_request(url: str, params: dict, service_name: str) -> None:
        """发送HTTP请求并处理响应。"""
        try:
            response = requests.post(url=url, json=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 200:
                logger.info(f"{service_name}消息推送成功")
            else:
                logger.warning(f"{service_name}消息推送失败：{result.get('msg')}")
        except requests.RequestException as e:
            logger.error(f"{service_name}请求失败：{str(e)}")

