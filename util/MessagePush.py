import logging
import random
from typing import Dict, List, Any
from collections import Counter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

import requests


class MessagePusher:
    STATUS_EMOJIS = {
        "success": "✅",
        "fail": "❌",
        "skip": "⏭️",
        "unknown": "❓"
    }

    def __init__(self, push_config: list):
        """
        初始化 MessagePusher 实例。

        :param push_config: 配置列表
        :type push_config: list
        """
        self._logger = logging.getLogger(__name__)
        self.push_config = push_config

    def push(self, results: List[Dict[str, Any]]):
        """推送消息

        :param results: 任务执行结果列表
        :type results: List[Dict[str, Any]]

        :return: 是否推送成功
        :rtype: bool
        """
        success_count = sum(r.get("status") == "success" for r in results)
        status_emoji = "🎉" if success_count == len(results) else "📊"
        title = f"{status_emoji} 工学云报告 ({success_count}/{len(results)})"

        for service_config in self.push_config:
            if service_config.get("enabled", False):
                service_type = service_config["type"]
                try:
                    if service_type == "Server":
                        content = self._generate_markdown_message(results)
                        self._server_push(service_config, title, content)
                    elif service_type == "PushPlus":
                        content = self._generate_html_message(results)
                        self._pushplus_push(service_config, title, content)
                    elif service_type == "AnPush":
                        content = self._generate_markdown_message(results)
                        self._anpush_push(service_config, title, content)
                    elif service_type == "WxPusher":
                        content = self._generate_html_message(results)
                        self._wxpusher_push(service_config, title, content)
                    elif service_type == "SMTP":
                        content = self._generate_html_message(results)
                        self._smtp_push(service_config, title, content)
                    else:
                        self._logger.warning(f"不支持的推送服务类型: {service_type}")

                except Exception as e:
                    self._logger.error(f"{service_type} 消息推送失败: {str(e)}")

    def _server_push(self, config: dict[str, Any], title: str, content: str):
        """Server酱 推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        url = f'https://sctapi.ftqq.com/{config['sendKey']}.send'
        data = {
            "title": title,
            "desp": content
        }

        try:
            rsp = requests.post(url, data=data).json()
            if rsp.get("code") == 0:
                self._logger.info("Server酱推送成功")
            else:
                raise Exception(rsp.get("message"))
        except Exception as e:
            self._logger.error(f"Server酱推送失败: {str(e)}")

    def _pushplus_push(self, config: dict[str, Any], title: str, content: str):
        """PushPlus 推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        url = f'https://www.pushplus.plus/send/{config["token"]}'
        data = {
            "title": title,
            "content": content
        }

        try:
            rsp = requests.post(url, data=data).json()
            if rsp.get("code") == 200:
                self._logger.info("PushPlus推送成功")
            else:
                raise Exception(rsp.get("msg"))
        except Exception as e:
            self._logger.error(f"PushPlus推送失败: {str(e)}")

    def _anpush_push(self, config: dict[str, Any], title: str, content: str):
        """AnPush 推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        url = f'https://api.anpush.com/push/{config["token"]}'
        data = {
            "title": title,
            "content": content,
            "channel": config["channel"],
            "to": config["to"]
        }

        try:
            rsp = requests.post(url, data=data).json()
            if rsp.get("code") == 200:
                self._logger.info("AnPush推送成功")
            else:
                raise Exception(rsp.get("msg"))
        except Exception as e:
            self._logger.error(f"AnPush推送失败: {str(e)}")

    def _wxpusher_push(self, config: dict[str, Any], title: str, content: str):
        """WxPusher 推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        url = f'https://wxpusher.zjiecode.com/api/send/message/simple-push'
        data = {
            "content": content,
            "summary": title,
            "contentType": 2,
            "spt": config["spt"],
        }

        try:
            rsp = requests.post(url, json=data).json()
            if rsp.get("code") == 1000:
                self._logger.info("WxPusher推送成功")
            else:
                raise Exception(rsp.get("msg"))
        except Exception as e:
            self._logger.error(f"WxPusher推送失败: {str(e)}")

    def _smtp_push(self, config: dict[str, Any], title: str, content: str):
        """SMTP 邮件推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        msg = MIMEMultipart()
        msg['From'] = formataddr((Header(config['from'], 'utf-8').encode(), config['username']))
        msg['To'] = Header(config['to'], 'utf-8')
        msg['Subject'] = Header(title, 'utf-8')

        # 添加邮件内容
        msg.attach(MIMEText(content, 'html', 'utf-8'))

        try:
            with smtplib.SMTP_SSL(config["host"], config["port"]) as server:
                server.login(config["username"], config["password"])
                server.send_message(msg)
                self._logger.info(f"邮件已发送至： {config['to']}")
                server.quit()
        except Exception as e:
            self._logger.error(f"邮件发送失败：{str(e)}")

    @staticmethod
    def _generate_markdown_message(results: List[Dict[str, Any]]) -> str:
        """
        生成 Markdown 格式的报告。

        :param results: 任务执行结果列表
        :type results: List[Dict[str, Any]]
        :return: Markdown 格式的消息
        :rtype: str
        """
        message_parts = ["# 工学云任务执行报告\n\n"]

        # 任务执行统计
        status_counts = Counter(result.get("status", "unknown") for result in results)
        total_tasks = len(results)

        message_parts.append("## 📊 执行统计\n\n")
        message_parts.append(f"- 总任务数：{total_tasks}\n")
        message_parts.append(f"- 成功：{status_counts['success']}\n")
        message_parts.append(f"- 失败：{status_counts['fail']}\n")
        message_parts.append(f"- 跳过：{status_counts['skip']}\n\n")

        # 详细任务报告
        message_parts.append("## 📝 详细任务报告\n\n")

        for result in results:
            task_type = result.get("task_type", "未知任务")
            status = result.get("status", "unknown")
            status_emoji = MessagePusher.STATUS_EMOJIS.get(status, MessagePusher.STATUS_EMOJIS["unknown"])

            message_parts.extend([
                f"### {status_emoji} {task_type}\n\n",
                f"**状态**：{status}\n\n",
                f"**结果**：{result.get('message', '无消息')}\n\n"
            ])

            details = result.get("details")
            if status == "success" and isinstance(details, dict):
                message_parts.append("**详细信息**：\n\n")
                message_parts.extend(f"- **{key}**：{value}\n" for key, value in details.items())
                message_parts.append("\n")

            # 添加报告内容（如果有）
            if status == "success" and task_type in ["日报提交", "周报提交", "月报提交"]:
                report_content = result.get("report_content", "")
                if report_content:
                    preview = f"{report_content[:50]}..." if len(report_content) > 50 else report_content
                    message_parts.extend([
                        f"**报告预览**：\n\n{preview}\n\n",
                        "<details>\n",
                        "<summary>点击查看完整报告</summary>\n\n",
                        f"```\n{report_content}\n```\n",
                        "</details>\n\n"
                    ])

            message_parts.append("---\n\n")

        return "".join(message_parts)

    @staticmethod
    def _generate_html_message(results: List[Dict[str, Any]]) -> str:
        """
        生成美观的HTML格式报告。

        :param results: 任务执行结果列表
        :type results: List[Dict[str, Any]]
        :return: HTML格式的消息
        :rtype: str
        """
        status_counts = Counter(result.get("status", "unknown") for result in results)
        total_tasks = len(results)

        html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>工学云任务执行报告</title><style>*{{margin:0;}}:root{{--bg-color:#f8f9fa;--text-color:#212529;--card-bg:#fff;--card-border:#dee2e6;--success-color:#28a745;--danger-color:#dc3545;--warning-color:#ffc107;--secondary-color:#6c757d}}@media(prefers-color-scheme:dark){{:root{{--bg-color:#343a40;--text-color:#f8f9fa;--card-bg:#495057;--card-border:#6c757d;--success-color:#5cb85c;--danger-color:#d9534f;--warning-color:#f0ad4e;--secondary-color:#a9a9a9}}}}body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;line-height:1.5;color:var(--text-color);background-color:var(--bg-color);margin:0;padding:20px;transition:background-color .3s}}h1,h2,h3{{margin-top:0}}h1{{text-align:center;margin-bottom:30px}}h2{{margin-bottom:20px}}.row{{display:flex;flex-wrap:wrap;margin:0 -15px}}.col{{flex:1;padding:0 15px;min-width:250px}}.card{{background-color:var(--card-bg);border:1px solid var(--card-border);border-radius:5px;padding:20px;margin-bottom:20px;transition:background-color .3s}}.card-title{{margin-top:0}}.text-center{{text-align:center}}.text-success{{color:var(--success-color)}}.text-danger{{color:var(--danger-color)}}.text-warning{{color:var(--warning-color)}}.text-secondary{{color:var(--secondary-color)}}.bg-light{{background-color:rgba(0,0,0,.05);border-radius:5px;padding:10px}}.report-preview{{font-style:italic;margin-top:10px}}.full-report{{display:none}}.show-report:checked+.full-report{{display:block}}pre{{white-space:pre-wrap;word-wrap:break-word;background-color:rgba(0,0,0,.05);padding:10px;border-radius:5px}}@media(max-width:768px){{.row{{flex-direction:column}}}}</style></head><body><div class="container"><h1>工学云任务执行报告</h1><div class="row"><div class="col"><div class="card text-center"><h3 class="card-title">总任务数</h3><p class="card-text" style="font-size:2em">{total_tasks}</p></div></div><div class="col"><div class="card text-center"><h3 class="card-title">成功</h3><p class="card-text text-success" style="font-size:2em">{status_counts['success']}</p></div></div><div class="col"><div class="card text-center"><h3 class="card-title">失败</h3><p class="card-text text-danger" style="font-size:2em">{status_counts['fail']}</p></div></div><div class="col"><div class="card text-center"><h3 class="card-title">跳过</h3><p class="card-text text-warning" style="font-size:2em">{status_counts['skip']}</p></div></div></div><h2>详细任务报告</h2>"""

        for result in results:
            task_type = result.get("task_type", "未知任务")
            status = result.get("status", "unknown")
            status_emoji = MessagePusher.STATUS_EMOJIS.get(status, MessagePusher.STATUS_EMOJIS["unknown"])
            status_class = {
                "success": "text-success",
                "fail": "text-danger",
                "skip": "text-warning",
                "unknown": "text-secondary"
            }.get(status, "text-secondary")

            html += f"""<div class="card"><h3 class="card-title">{status_emoji} {task_type}</h3><p><strong>状态：</strong><span class="{status_class}">{status}</span></p><p><strong>结果：</strong>{result.get('message', '无消息')}</p>"""

            details = result.get("details")
            if status == "success" and isinstance(details, dict):
                html += '<div class="bg-light"><h4>详细信息</h4>'
                for key, value in details.items():
                    html += f'<p><strong>{key}：</strong>{value}</p>'
                html += '</div>'

            if status == "success" and task_type in ["日报提交", "周报提交", "月报提交"]:
                report_content = result.get("report_content", "")
                if report_content:
                    preview = f"{report_content[:50]}..." if len(report_content) > 50 else report_content
                    report_id = random.randint(1000, 9999)
                    html += f"""<div class="report-preview"><p><strong>报告预览：</strong>{preview}</p></div><input type="checkbox" id="report-{report_id}" class="show-report"><label for="report-{report_id}">查看完整报告</label><div class="full-report"><pre>{report_content}</pre></div>"""

            html += '</div>'

        html += """</div></body></html>"""

        return html
