import requests
import logging

logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %I:%M:%S'
                    )
MessagePusherLog = logging.getLogger('MessagePusherLOg')


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
        self.push_functions = {
            "server": self._push_server,
            "pushplus": self._push_pushplus
        }

    def push(self, title: str, content: str) -> None:
        """
        统一消息推送方法，根据初始化时指定的push_type调用对应的推送接口。

        :param title: 消息的标题。
        :type title: str
        :param content: 消息的内容。
        :type content: str
        """
        if self.push_type not in self.push_functions:
            MessagePusherLog.error(f"未知的推送类型: {self.push_type}")
            return

        self.push_functions[self.push_type](title, content)

    def _push_server(self, title: str, content: str) -> None:
        """
        使用Server酱推送消息。

        :param title: 消息的标题。
        :type title: str
        :param content: 消息的内容。
        :type content: str
        """
        url = f"https://sctapi.ftqq.com/{self.token}.send"
        params = {"text": title, "desp": content}
        response = requests.post(url=url, data=params)

        if response.status_code == 200:
            MessagePusherLog.info("Server酱推送成功")
        else:
            MessagePusherLog.info("Server酱推送失败")

    def _push_pushplus(self, title: str, content: str) -> None:
        """
        使用PushPlus推送消息。

        :param title: 消息的标题。
        :type title: str
        :param content: 消息的内容。
        :type content: str
        """
        url = "http://www.pushplus.plus/send"
        params = {"token": self.token, "title": title, "content": content}
        response = requests.post(url=url, data=params)

        if response.status_code == 200 and response.json().get("code") == 200:
            MessagePusherLog.info("PushPlus消息推送成功")
        else:
            MessagePusherLog.info(f"PushPlus消息推送失败：{response.json().get('msg')}")
