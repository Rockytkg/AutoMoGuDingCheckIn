import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

from util.Api import ApiClient, generate_article
from util.Config import ConfigManager
from util.MessagePush import MessagePusher

# 配置日志
logging.basicConfig(
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MainModule")

USER_DIR = os.path.join(os.path.dirname(__file__), "user")


def get_api_client(config: ConfigManager) -> ApiClient:
    """获取配置好的ApiClient实例。"""
    api_client = ApiClient(config)
    if not config.get_user_info('token'):
        api_client.login()
    if not config.get_plan_info('planId'):
        api_client.fetch_internship_plan()
    else:
        logger.info("使用本地数据")
    return api_client


def perform_clock_in(api_client: ApiClient, config: ConfigManager) -> Dict[str, Any]:
    """执行打卡操作"""
    try:
        user_name = config.get_user_info('nikeName')
        current_time = datetime.now()
        current_hour = current_time.hour

        # 定义打卡时间范围
        morning_start, morning_end = 8, 12
        afternoon_start, afternoon_end = 17, 20

        # 判断当前是否在打卡时间范围内
        if morning_start <= current_hour < morning_end:
            checkin_type = 'START'
        elif afternoon_start <= current_hour < afternoon_end:
            checkin_type = 'END'
        else:
            return {
                "status": "skip",
                "message": "当前不在打卡时间范围内",
                "task_type": "打卡"
            }

        # 获取上次打卡信息
        last_checkin_info = api_client.get_checkin_info()

        # 检查是否已经打过卡
        last_checkin_time = datetime.strptime(last_checkin_info['createTime'], "%Y-%m-%d %H:%M:%S")
        if last_checkin_info['type'] == checkin_type and last_checkin_time.date() == current_time.date():
            return {
                "status": "skip",
                "message": f"今日{'上班' if checkin_type == 'START' else '下班'}卡已打，无需重复打卡",
                "task_type": "打卡"
            }

        logger.info(f'用户 {user_name} 开始{("上班" if checkin_type == "START" else "下班")}打卡')

        # 更新打卡信息
        checkin_info = last_checkin_info.copy()
        checkin_info['type'] = checkin_type

        api_client.submit_clock_in(checkin_info)

        return {
            "status": "success",
            "message": f"{'上班' if checkin_type == 'START' else '下班'}打卡成功",
            "task_type": "打卡",
            "details": {
                "姓名": user_name,
                "打卡类型": '上班' if checkin_type == 'START' else '下班',
                "打卡时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "打卡地点": config.get_config('address')
            }
        }
    except Exception as e:
        logger.error(f"打卡失败: {e}")
        return {
            "status": "fail",
            "message": f"打卡失败: {str(e)}",
            "task_type": "打卡"
        }


def submit_daily_report(api_client: ApiClient, config: ConfigManager) -> Dict[str, Any]:
    """提交日报"""
    if not config.get_config("isSubmittedDaily"):
        return {
            "status": "skip",
            "message": "用户未开启日报提交功能",
            "task_type": "日报提交"
        }

    current_time = datetime.now()
    if current_time.hour < 12:
        return {
            "status": "skip",
            "message": "未到日报提交时间（需12点后）",
            "task_type": "日报提交"
        }

    try:
        job_info = api_client.get_job_info()
        report_count = api_client.get_submitted_reports_count("day") + 1
        content = generate_article(config, f"第{report_count}天日报", job_info)
        report_info = {
            'title': f'第{report_count}天日报',
            'content': content,
            'attachments': '',
            'reportType': 'day',
            'jobId': job_info.get('jobId'),
            'reportTime': current_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        api_client.submit_report(report_info)
        return {
            "status": "success",
            "message": f"第{report_count}天日报已提交",
            "task_type": "日报提交",
            "details": {
                "日报标题": f'第{report_count}天日报',
                "提交时间": current_time.strftime('%Y-%m-%d %H:%M:%S')
            },
            "report_content": content
        }
    except Exception as e:
        logger.error(f"日报提交失败: {e}")
        return {
            "status": "fail",
            "message": f"日报提交失败: {str(e)}",
            "task_type": "日报提交"
        }


def submit_weekly_report(config: ConfigManager, api_client: ApiClient) -> Dict[str, Any]:
    """提交周报"""
    if not config.get_config("isSubmittedWeekly"):
        return {
            "status": "skip",
            "message": "用户未开启周报提交功能",
            "task_type": "周报提交"
        }

    current_time = datetime.now()
    submit_day = int(config.get_config("submitWeeklyTime"))

    if current_time.weekday() + 1 != submit_day or current_time.hour < 12:
        return {
            "status": "skip",
            "message": "未到周报提交时间（需指定日期12点后）",
            "task_type": "周报提交"
        }

    try:
        weeks = api_client.get_weeks_date()
        job_info = api_client.get_job_info()
        week = api_client.get_submitted_reports_count('week') + 1
        content = generate_article(config, f"第{week}周周报", job_info)
        report_info = {
            'title': f"第{week}周周报",
            'content': content,
            'attachments': '',
            'reportType': 'week',
            'endTime': weeks.get('endTime'),
            'startTime': weeks.get('startTime'),
            'jobId': job_info.get('jobId'),
            'weeks': f"第{week}周"
        }
        api_client.submit_report(report_info)
        return {
            "status": "success",
            "message": f"第{week}周周报已提交",
            "task_type": "周报提交",
            "details": {
                "周报标题": f"第{week}周周报",
                "开始时间": weeks.get('startTime'),
                "结束时间": weeks.get('endTime')
            },
            "report_content": content
        }
    except Exception as e:
        logger.error(f"周报提交失败: {e}")
        return {
            "status": "fail",
            "message": f"周报提交失败: {str(e)}",
            "task_type": "周报提交"
        }


def submit_monthly_report(config: ConfigManager, api_client: ApiClient) -> Dict[str, Any]:
    """提交月报"""
    if not config.get_config("isSubmittedMonthlyReport"):
        return {
            "status": "skip",
            "message": "用户未开启月报提交功能",
            "task_type": "月报提交"
        }

    current_time = datetime.now()
    last_day_of_month = (current_time.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    submit_day = int(config.get_config("submit_monthly_time"))

    if current_time.day != min(submit_day, last_day_of_month.day) or current_time.hour < 12:
        return {
            "status": "skip",
            "message": "未到月报提交时间（需指定日期12点后）",
            "task_type": "月报提交"
        }

    try:
        job_info = api_client.get_job_info()
        month = api_client.get_submitted_reports_count('month') + 1
        content = generate_article(config, f"第{month}月月报", job_info)
        report_info = {
            'title': f"第{month}月月报",
            'content': content,
            'attachments': '',
            'yearmonth': current_time.strftime('%Y-%m'),
            'reportType': 'month',
            'jobId': job_info.get('jobId'),
        }
        api_client.submit_report(report_info)
        return {
            "status": "success",
            "message": f"第{month}月月报已提交",
            "task_type": "月报提交",
            "details": {
                "月报标题": f"第{month}月月报",
                "提交月份": current_time.strftime('%Y-%m')
            },
            "report_content": content
        }
    except Exception as e:
        logger.error(f"月报提交失败: {e}")
        return {
            "status": "fail",
            "message": f"月报提交失败: {str(e)}",
            "task_type": "月报提交"
        }


def generate_markdown_message(results: List[Dict[str, Any]]) -> str:
    """生成 Markdown 格式的消息"""
    message = "# 工学云任务执行报告\n\n"

    # 任务执行统计
    total_tasks = len(results)
    success_tasks = sum(1 for result in results if result.get("status") == "success")
    fail_tasks = sum(1 for result in results if result.get("status") == "fail")
    skip_tasks = sum(1 for result in results if result.get("status") == "skip")

    message += "## 📊 执行统计\n\n"
    message += f"- 总任务数：{total_tasks}\n"
    message += f"- 成功：{success_tasks}\n"
    message += f"- 失败：{fail_tasks}\n"
    message += f"- 跳过：{skip_tasks}\n\n"

    # 详细任务报告
    message += "## 📝 详细任务报告\n\n"

    for result in results:
        task_type = result.get("task_type", "未知任务")
        status = result.get("status", "unknown")
        status_emoji = {
            "success": "✅",
            "fail": "❌",
            "skip": "⏭️"
        }.get(status, "❓")

        message += f"### {status_emoji} {task_type}\n\n"
        message += f"**状态**：{status}\n\n"
        message += f"**结果**：{result.get('message', '无消息')}\n\n"

        details = result.get("details")
        if status == "success" and isinstance(details, dict):
            message += "**详细信息**：\n\n"
            for key, value in details.items():
                message += f"- **{key}**：{value}\n"
            message += "\n"

        # 添加报告内容（如果有）
        if status == "success" and task_type in ["日报提交", "周报提交", "月报提交"]:
            report_content = result.get("report_content", "")
            if report_content:
                preview = report_content[:200] + "..." if len(report_content) > 200 else report_content
                message += f"**报告预览**：\n\n{preview}\n\n"
                message += "<details>\n"
                message += "<summary>点击查看完整报告</summary>\n\n"
                message += f"```\n{report_content}\n```\n"
                message += "</details>\n\n"

        message += "---\n\n"

    return message


def push_notification(config: ConfigManager, results: List[Dict[str, Any]], message: str) -> None:
    """发送推送消息"""
    push_key = config.get_config('pushKey')
    push_type = config.get_config('pushType')

    if push_key and push_type:
        pusher = MessagePusher(push_key, push_type)

        success_count = sum(1 for result in results if result.get("status") == "success")
        total_count = len(results)

        # 简化标题，使用表情符号表示状态
        status_emoji = "🎉" if success_count == total_count else "📊"
        title = f"{status_emoji} 工学云报告 ({success_count}/{total_count})"

        pusher.push(title, message)
    else:
        logger.info("用户未配置推送")


def run(config: ConfigManager) -> None:
    """执行所有任务"""
    results: List[Dict[str, Any]] = []

    try:
        api_client = get_api_client(config)
    except Exception as e:
        error_message = f"获取API客户端失败: {str(e)}"
        logger.error(error_message)
        results.append({
            "status": "fail",
            "message": error_message,
            "task_type": "API客户端初始化"
        })
        message = generate_markdown_message(results)
        push_notification(config, results, message)
        logger.info("任务异常结束\n")
        return  # 终止执行当前用户的所有任务

    logger.info(f'开始执行：{config.get_user_info('nikeName')}')

    try:
        results = [
            perform_clock_in(api_client, config),
            submit_daily_report(api_client, config),
            submit_weekly_report(config, api_client),
            submit_monthly_report(config, api_client)
        ]
    except Exception as e:
        error_message = f"执行任务时发生错误: {str(e)}"
        logger.error(error_message)
        results.append({
            "status": "fail",
            "message": error_message,
            "task_type": "任务执行"
        })

    message = generate_markdown_message(results)
    push_notification(config, results, message)
    logger.info(f'执行结束：{config.get_user_info('nikeName')}\n')


def main() -> None:
    """程序主入口"""
    logger.info("工学云任务开始")

    json_files = [f for f in os.listdir(USER_DIR) if f.endswith('.json')]
    if not json_files:
        logger.info("打卡文件未配置")
        return

    for filename in json_files:
        run(ConfigManager(os.path.join(USER_DIR, filename)))

    logger.info("工学云任务结束")


if __name__ == '__main__':
    main()
