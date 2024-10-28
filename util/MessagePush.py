import logging
import random
from typing import Dict, List, Any
from collections import Counter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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
                        content = self._generate_markdown_message(results)
                        self._pushplus_push(service_config, title, content)
                    elif service_type == "AnPush":
                        content = self._generate_markdown_message(results)
                        self._anpush_push(service_config, title, content)
                    elif service_type == "WxPusher":
                        content = self._generate_markdown_message(results)
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
        pass

    def _pushplus_push(self, config: dict[str, Any], title: str, content: str):
        """PushPlus 推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        pass

    def _anpush_push(self, config: dict[str, Any], title: str, content: str):
        """AnPush 推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        pass

    def _wxpusher_push(self, config: dict[str, Any], title: str, content: str):
        """WxPusher 推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        pass

    def _smtp_push(self, config: dict[str, Any], title: str, content: str):
        """SMTP 邮件推送

        :param config: 配置
        :type config: dict[str, Any]
        :param title: 标题
        :type title: str
        :param content: 内容
        :type content: str
        """
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = f"{config['from']} <{config['username']}>"
        msg['To'] = config['to']
        msg['Subject'] = title

        # 添加邮件内容
        msg.attach(MIMEText(content, 'plain'))

        try:
            with smtplib.SMTP_SSL(config["host"], config["port"]) as server:
                server.login(config["username"], config["password"])
                server.send_message(msg)
                self._logger.info(f"邮件已发送： {config['to']}")
        except Exception as e:
            self._logger.error(f"邮件发送失败： {str(e)}")

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

        html = f"""
           <!DOCTYPE html>
           <html lang="zh-CN">
           <head>
               <meta charset="UTF-8">
               <meta name="viewport" content="width=device-width, initial-scale=1.0">
               <title>工学云任务执行报告</title>
               <style>
                   body {{
                       font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                       line-height: 1.6;
                       color: #333;
                       max-width: 800px;
                       margin: 0 auto;
                       padding: 20px;
                       background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                   }}
                   h1, h2, h3 {{
                       color: #2c3e50;
                   }}
                   h1 {{
                       text-align: center;
                       font-size: 2.5em;
                       margin-bottom: 30px;
                   }}
                   .stats {{
                       display: flex;
                       justify-content: space-around;
                       flex-wrap: wrap;
                       margin-bottom: 30px;
                   }}
                   .stat-item {{
                       background-color: rgba(255, 255, 255, 0.8);
                       border-radius: 10px;
                       padding: 15px;
                       text-align: center;
                       box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                       margin: 10px;
                       flex: 1;
                       min-width: 120px;
                   }}
                   .task {{
                       background-color: rgba(255, 255, 255, 0.8);
                       border-radius: 10px;
                       padding: 20px;
                       margin-bottom: 20px;
                       box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                   }}
                   .task h3 {{
                       margin-top: 0;
                   }}
                   .details {{
                       background-color: rgba(240, 240, 240, 0.5);
                       border-radius: 5px;
                       padding: 10px;
                       margin-top: 10px;
                   }}
                   .report-preview {{
                       background-color: rgba(240, 240, 240, 0.5);
                       border-radius: 5px;
                       padding: 10px;
                       margin-top: 10px;
                       font-style: italic;
                   }}
                   .full-report {{
                       display: none;
                   }}
                   .show-report:checked + .full-report {{
                       display: block;
                   }}
                   @media (max-width: 600px) {{
                       .stats {{
                           flex-direction: column;
                       }}
                   }}
               </style>
           </head>
           <body>
               <h1>工学云任务执行报告</h1>

               <div class="stats">
                   <div class="stat-item">
                       <h3>总任务数</h3>
                       <p>{total_tasks}</p>
                   </div>
                   <div class="stat-item">
                       <h3>成功</h3>
                       <p>{status_counts['success']}</p>
                   </div>
                   <div class="stat-item">
                       <h3>失败</h3>
                       <p>{status_counts['fail']}</p>
                   </div>
                   <div class="stat-item">
                       <h3>跳过</h3>
                       <p>{status_counts['skip']}</p>
                   </div>
               </div>

               <h2>详细任务报告</h2>
           """

        for result in results:
            task_type = result.get("task_type", "未知任务")
            status = result.get("status", "unknown")
            status_emoji = MessagePusher.STATUS_EMOJIS.get(status, MessagePusher.STATUS_EMOJIS["unknown"])

            html += f"""
               <div class="task">
                   <h3>{status_emoji} {task_type}</h3>
                   <p><strong>状态：</strong>{status}</p>
                   <p><strong>结果：</strong>{result.get('message', '无消息')}</p>
               """

            details = result.get("details")
            if status == "success" and isinstance(details, dict):
                html += '<div class="details">'
                for key, value in details.items():
                    html += f'<p><strong>{key}：</strong>{value}</p>'
                html += '</div>'

            if status == "success" and task_type in ["日报提交", "周报提交", "月报提交"]:
                report_content = result.get("report_content", "")
                if report_content:
                    preview = f"{report_content[:50]}..." if len(report_content) > 50 else report_content
                    html += f"""
                       <div class="report-preview">
                           <p><strong>报告预览：</strong>{preview}</p>
                       </div>
                       <input type="checkbox" id="report-{random.randint(1000, 9999)}" class="show-report">
                       <label for="report-{random.randint(1000, 9999)}">查看完整报告</label>
                       <div class="full-report">
                           <pre>{report_content}</pre>
                       </div>
                       """

            html += '</div>'

        html += """
           </body>
           </html>
           """

        return html
