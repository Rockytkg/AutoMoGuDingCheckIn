import logging
import os
import time

from util.Api import ApiClient
from util.Config import ConfigManager
from util.MessagePush import MessagePusher

# 配置日志
logging.basicConfig(
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %I:%M:%S"
)
logger = logging.getLogger("MainModule")

USER_DIR = os.path.join(os.path.dirname(__file__), "user")


def get_api_client(config: ConfigManager) -> ApiClient:
    """获取配置好的ApiClient实例。

    如果本地不存在用户Token或实习计划ID，执行登录或获取实习计划的操作。

    :param config: 配置管理器实例。
    :type config: ConfigManager

    :return: 配置好的ApiClient实例。
    :rtype: ApiClient
    """
    api_client = ApiClient(config)
    if not config.get_user_info('token'):
        api_client.login()
    if not config.get_plan_info('planId'):
        api_client.fetch_internship_plan()
    else:
        logger.info("使用本地数据")
    return api_client


def run(config: ConfigManager) -> None:
    """执行打卡流程。

    根据当前打卡类型（上班或下班）切换状态并提交打卡信息。
    处理异常并根据配置发送推送消息。

    :param config: 配置管理器实例。
    :type config: ConfigManager
    """
    try:
        api_client = get_api_client(config)
        checkin_info = toggle_checkin_type(api_client.get_checkin_info())
        user_name = config.get_user_info('nikeName')
        logger.info(f'用户 {user_name} 开始签到')

        print(api_client.get_job_info())

        # 提交打卡信息
        #api_client.submit_clock_in(checkin_info)
        message = (
            f"姓名：{user_name}\n\n"
            f"打卡类型：{checkin_info['type']}\n\n"
            f"打卡时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n\n"
            f"打卡地点：{config.get_config('address')}\n\n"
            f"上次打卡时间：{checkin_info.get('createTime')}\n\n"
            f"上次打卡地点：{checkin_info.get('address')}\n\n"
        )
        logger.info("工学云签到成功")

        # 提交日报、周报、月报
        if config.get_config("is_submit_daily"):
            message += submit_daily_report(api_client)
        else:
            logger.info("用户未开启日报提交")
            message += "日报：用户未开启此功能\n\n"

        if config.get_config("is_submit_weekly"):
            message += submit_weekly_report(config, api_client)
        else:
            logger.info("用户未开启周报提交")
            message += "周报：用户未开启此功能\n\n"

        if config.get_config("is_submit_monthly"):
            message += submit_monthly_report(config, api_client)
        else:
            logger.info("用户未开启月报提交")
            message += "月报：用户未开启此功能\n\n"

    except Exception as e:
        logger.error(f"运行时出现异常: {e}")
        message = f"运行时出现异常：{str(e)}"
        push_notification(config, "工学云打卡失败", message)
    else:
        push_notification(config, "工学云打卡成功", message)

    logger.info("--------------------------")


def toggle_checkin_type(checkin_info: dict) -> dict:
    """切换打卡类型"""
    checkin_info['type'] = 'END' if checkin_info.get('type') == 'START' else 'START'
    return checkin_info


def submit_daily_report(api_client: ApiClient) -> str:
    """提交日报"""
    report_info = {
        'title': f'第{api_client.get_submitted_reports_count("day") + 1}天日报',
        'content': '',
        'attachments': '',
        'reportType': 'day',
        'reportTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    }
    api_client.submit_report(report_info)
    return f"日报：第{api_client.get_submitted_reports_count('day') + 1}天日报已提交\n\n"


def submit_weekly_report(config: ConfigManager, api_client: ApiClient) -> str:
    """提交周报"""
    if config.get_config("submit_weekly_time") == ('7' if time.strftime('%w') == '0' else time.strftime('%w')):
        weeks = api_client.get_weeks_date()
        report_info = {
            'title': f"第{api_client.get_submitted_reports_count('week') + 1}周周报",
            'content': '',
            'attachments': '',
            'reportType': 'week',
            'endTime': weeks.get('endTime'),
            'startTime': weeks.get('startTime'),
            'weeks': f"第{api_client.get_submitted_reports_count('week') + 1}周"
        }
        api_client.submit_report(report_info)
        return f"周报：第{api_client.get_submitted_reports_count('week') + 1}周周报已提交\n\n"
    else:
        logger.info("未到周报提交时间")
        return "周报：未到周报提交时间\n\n"


def submit_monthly_report(config: ConfigManager, api_client: ApiClient) -> str:
    """提交月报"""
    if config.get_config("submit_monthly_time") == time.strftime('%d'):
        report_info = {
            'title': f"第{api_client.get_submitted_reports_count('week') + 1}月月报",
            'content': '',
            'attachments': '',
            'yearmonth': time.strftime('%Y-%m', time.localtime()),
            'reportType': 'month',
        }
        api_client.submit_report(report_info)
        return f"月报：第{api_client.get_submitted_reports_count('week') + 1}月月报已提交\n\n"
    else:
        logger.info("未到月报提交时间")
        return "月报：未到月报提交时间\n\n"


def push_notification(config: ConfigManager, title: str, message: str) -> None:
    """发送推送消息"""
    push_key = config.get_config('pushKey')
    push_type = config.get_config('pushType')

    if push_key and push_type:
        pusher = MessagePusher(push_key, push_type)
        #pusher.push(title, message)
    else:
        logger.info("用户未配置推送")


def main() -> None:
    """程序主入口，执行打卡程序。

    遍历用户目录中的配置文件，依次执行打卡流程，并记录程序的开始和结束信息。
    """
    logger.info("工学云打卡开始")

    json_files = [f for f in os.listdir(USER_DIR) if f.endswith('.json')]
    if not json_files:
        logger.info("打卡文件未配置")
        return

    for filename in json_files:
        run(ConfigManager(os.path.join(USER_DIR, filename)))

    logger.info("工学云打卡结束")


if __name__ == '__main__':
    main()
