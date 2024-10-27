import logging
import time
from typing import Callable, Dict, Optional
import requests

logging.basicConfig(
    format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %I:%M:%S'
)
logger = logging.getLogger('MessagePush')


class MessagePusher:
    def __init__(self, token: str, push_type: str = "server"):
        """
        初始化MessagePusher实例。

        :param token: 用于消息推送的认证Token。
        :type token: str
        :param push_type: 消息推送的类型，默认为"server"。
        :type push_type: str
        """
        self.token = token
        self.push_type = push_type.lower()
        self.push_functions: Dict[str, Callable[[str, str], None]] = {
            "server": self._push_server,
            "pushplus": self._push_pushplus,
            "anpush": self._push_anpush
        }

    def push(self, title: str, content: str) -> None:
        """
        统一消息推送方法，根据初始化时指定的push_type调用对应的推送接口。

        :param title: 消息的标题。
        :type title: str
        :param content: 消息的内容。
        :type content: str
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
        self._send_request(url=url, json=params, service="Server酱")

    def _push_pushplus(self, title: str, content: str) -> None:
        """
        使用PushPlus推送消息。

        :param title: 消息的标题。
        :type title: str
        :param content: 消息的内容。
        :type content: str
        """
        url = "https://www.pushplus.plus/send"
        params = {
            "token": self.token,
            "title": title,
            "template": "markdown",
            "content": content
        }
        self._send_request(url=url, json=params, service="PushPlus")

    def _push_anpush(self, title: str, content: str) -> None:
        """
        使用AnPush推送消息。

        :param title: 消息的标题。
        :type title: str
        :param content: 消息的内容。
        :type content: str
        """
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
        self._send_request(url=url, data=params, service="AnPush")

    @staticmethod
    def _send_request(
            url: str,
            data: Optional[dict] = None,
            json: Optional[dict] = None,
            service: str = "Service",
            max_retries: int = 3,
            initial_delay: float = 0.5
    ) -> None:
        """
        发送HTTP请求并处理响应，包含重试机制。

        :param url: 请求的URL。
        :type url: str
        :param data: 请求的数据。
        :type data: dict
        :param json: 请求的JSON数据。
        :type json: dict
        :param service: 服务名称。
        :type service: str
        :param max_retries: 最大重试次数。
        :type max_retries: int
        :param initial_delay: 初始等待时间。
        :type initial_delay: float
        """
        retries = 0
        while retries <= max_retries:
            try:
                response = requests.post(url=url, data=data, json=json, timeout=10)
                response.raise_for_status()
                result = response.json()
                if result.get("code") == 200 or result.get("code") == 0:
                    logger.info(f"{service}消息推送成功")
                    return  # 成功时直接返回
                else:
                    logger.warning(f"{service}消息推送失败：{result.get('msg')}")
                    # 推送失败但服务器正常响应，不进行重试
                    return
            except requests.RequestException as e:
                retries += 1
                if retries > max_retries:
                    logger.error(f"{service}请求失败，已达到最大重试次数：{str(e)}")
                    return
                wait_time = initial_delay * (2 ** retries)
                logger.warning(f"{service}请求失败，正在进行第 {retries} 次重试，等待时间：{wait_time:.2f}秒")
                time.sleep(wait_time)
