import requests
import logging

logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %I:%M:%S'
                    )
MessagePusher = logging.getLogger('MessagePusher')


def push_message(push_type: str, title: str, content: str, token: str) -> None:
    def push_server(server_title: str, server_content: str, server_token: str) -> None:
        url = f"https://sctapi.ftqq.com/{server_token}.send"
        params = {"text": server_title, "desp": server_content}
        response = requests.post(url=url, data=params)

        if response.status_code == 200:
            MessagePusher.info("Server酱推送成功")
        else:
            MessagePusher.info("Server酱推送失败")

    def push_pushplus(pushplus_title: str, pushplus_content: str, pushplus_token: str) -> None:
        url = "http://www.pushplus.plus/send"
        params = {"token": pushplus_token, "title": pushplus_title, "content": pushplus_content}
        response = requests.post(url=url, data=params)

        if response.status_code == 200 and response.json().get("code") == 200:
            MessagePusher.info("消息推送成功")
        else:
            MessagePusher.info(f"消息推送失败：{response.json().get('msg')}")

    push_functions = {
        "server": push_server,
        "pushplus": push_pushplus
    }

    if push_type not in push_functions:
        MessagePusher.error(f"未知的推送类型: {push_type}")
        return

    push_functions[push_type](title, content, token)
