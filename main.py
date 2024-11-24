import logging
import os
import argparse
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

from util.Api import ApiClient, generate_article, upload
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
    """获取配置好的ApiClient实例。

    :param config: 配置管理器。
    :type config: ConfigManager
    :return: ApiClient实例。
    :rtype: ApiClient
    """
    api_client = ApiClient(config)
    if not config.get_value('userInfo.token'):
        api_client.login()
    if not config.get_value('planInfo.planId'):
        api_client.fetch_internship_plan()
    else:
        logger.info("使用本地数据")
    return api_client


def upload_img(api_client: ApiClient, config: ConfigManager, count: int) -> str:
    """上传指定数量的图片

    :param api_client: ApiClient实例。
    :type api_client: ApiClient
    :param config: 配置管理器。
    :type config: ConfigManager
    :param count: 需要上传的图片数量。
    :type count: int
    :return: 上传成功的图片链接
    :rtype: str
    """
    # 检查数量是否大于0
    if count <= 0:
        return ""

    images_dir = os.path.join(os.path.dirname(__file__), "images")
    # 获取所有符合条件的图片文件
    all_images = [os.path.join(images_dir, f) for f in os.listdir(images_dir) if
                  f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    # 检查可用图片数量
    if len(all_images) < count:
        return ""

    # 随机选择指定数量的图片
    images = random.sample(all_images, count)

    # 获取上传令牌并上传图片
    token = api_client.get_upload_token()
    return upload(token, images, config)


def perform_clock_in(api_client: ApiClient, config: ConfigManager) -> Dict[str, Any]:
    """执行打卡操作

    :param api_client: ApiClient实例。
    :type api_client: ApiClient
    :param config: 配置管理器。
    :type config: ConfigManager
    :return: 执行结果
    :rtype: Dict[str, Any]
    """
    try:
        current_time = datetime.now()
        current_hour = current_time.hour

        # 判断打卡类型
        if 8 <= current_hour < 12:
            checkin_type = 'START'
            display_type = '上班'
        elif 17 <= current_hour < 20:
            checkin_type = 'END'
            display_type = '下班'
        else:
            logger.info("当前不在打卡时间范围内")
            return {
                "status": "skip",
                "message": "当前不在打卡时间范围内",
                "task_type": "打卡"
            }

        last_checkin_info = api_client.get_checkin_info()

        # 检查是否已经打过卡
        if last_checkin_info and last_checkin_info['type'] == checkin_type:
            last_checkin_time = datetime.strptime(last_checkin_info['createTime'], "%Y-%m-%d %H:%M:%S")
            if last_checkin_time.date() == current_time.date():
                logger.info(f"今日 {display_type} 卡已打，无需重复打卡")
                return {
                    "status": "skip",
                    "message": f"今日 {display_type} 卡已打，无需重复打卡",
                    "task_type": "打卡"
                }

        user_name = config.get_value('userInfo.nikeName')
        logger.info(f'用户 {user_name} 开始 {display_type} 打卡')

        # 打卡图片和备注
        attachments = upload_img(api_client, config, config.get_value("config.clockIn.imageCount"))
        description = random.choice(config.get_value('config.clockIn.description')) if config.get_value(
            'config.clockIn.description') else None

        # 设置打卡信息
        checkin_info = {
            'type': checkin_type,
            'lastDetailAddress': last_checkin_info.get('address'),
            'attachments': attachments or None,
            'description': description
        }

        api_client.submit_clock_in(checkin_info)
        logger.info(f'用户 {user_name} {display_type} 打卡成功')

        return {
            "status": "success",
            "message": f"{display_type}打卡成功",
            "task_type": "打卡",
            "details": {
                "姓名": user_name,
                "打卡类型": display_type,
                "打卡时间": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "打卡地点": config.get_value('config.clockIn.location.address')
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
    """提交日报

    :param api_client: ApiClient实例。
    :type api_client: ApiClient
    :param config: 配置管理器。
    :type config: ConfigManager
    :return: 执行结果
    :rtype: Dict[str, Any]
    """
    if not config.get_value("config.reportSettings.daily.enabled"):
        logger.info("用户未开启日报提交功能，跳过日报提交任务")
        return {
            "status": "skip",
            "message": "用户未开启日报提交功能",
            "task_type": "日报提交"
        }

    current_time = datetime.now()
    if not (17 <= current_time.hour < 20):
        logger.info("未到日报提交时间（需12点后）")
        return {
            "status": "skip",
            "message": "未到日报提交时间（需12点后）",
            "task_type": "日报提交"
        }

    try:
        # 获取历史提交记录
        submitted_reports_info = api_client.get_submitted_reports_info("day")
        submitted_reports = submitted_reports_info.get('data', [])

        # 检查是否已经提交过今天的日报
        if submitted_reports:
            last_report = submitted_reports[0]
            last_submit_time = datetime.strptime(last_report['createTime'], '%Y-%m-%d %H:%M:%S')
            if last_submit_time.date() == current_time.date():
                logger.info("今天已经提交过日报，跳过本次提交")
                return {
                    "status": "skip",
                    "message": "今天已经提交过日报",
                    "task_type": "日报提交"
                }

        job_info = api_client.get_job_info()
        report_count = submitted_reports_info.get('flag', 0) + 1
        content = generate_article(config, f"第{report_count}天日报", job_info)

        # 上传图片并获取附件
        attachments = upload_img(api_client, config, config.get_value("config.reportSettings.daily.imageCount"))

        report_info = {
            'title': f'第{report_count}天日报',
            'content': content,
            'attachments': attachments,
            'reportType': 'day',
            'jobId': job_info.get('jobId'),
            'reportTime': current_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        api_client.submit_report(report_info)

        logger.info(f"第{report_count}天日报已提交，提交时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return {
            "status": "success",
            "message": f"第{report_count}天日报已提交",
            "task_type": "日报提交",
            "details": {
                "日报标题": f'第{report_count}天日报',
                "提交时间": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                "附件": attachments
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
    """提交周报

    :param config: 配置管理器。
    :type config: ConfigManager
    :param api_client: ApiClient实例。
    :type api_client: ApiClient
    :return: 执行结果
    :rtype: Dict[str, Any]
    """
    if not config.get_value('config.reportSettings.weekly.enabled'):
        logger.info("用户未开启周报提交功能，跳过周报提交任务")
        return {
            "status": "skip",
            "message": "用户未开启周报提交功能",
            "task_type": "周报提交"
        }

    current_time = datetime.now()
    submit_day = config.get_value('config.reportSettings.weekly.submitTime')

    if current_time.weekday() + 1 != submit_day or not (17 <= current_time.hour < 20):
        logger.info("未到周报提交时间")
        return {
            "status": "skip",
            "message": "未到周报提交时间",
            "task_type": "周报提交"
        }

    try:
        # 获取当前周信息
        current_week_info = api_client.get_weeks_date()[0]

        # 获取历史提交记录
        submitted_reports_info = api_client.get_submitted_reports_info('week')
        submitted_reports = submitted_reports_info.get('data', [])

        # 获取当前周数
        week = submitted_reports_info.get('flag', 0) + 1
        current_week_string = f"第{week}周"

        # 检查是否已经提交过本周的周报
        if submitted_reports:
            last_report = submitted_reports[0]
            if last_report.get('weeks') == current_week_string:
                logger.info("本周已经提交过周报，跳过本次提交")
                return {
                    "status": "skip",
                    "message": "本周已经提交过周报",
                    "task_type": "周报提交"
                }

        job_info = api_client.get_job_info()
        content = generate_article(config, f"第{week}周周报", job_info)

        # 上传图片并获取附件
        attachments = upload_img(api_client, config, config.get_value('config.reportSettings.weekly.imageCount'))

        report_info = {
            'title': f"第{week}周周报",
            'content': content,
            'attachments': attachments,
            'reportType': 'week',
            'endTime': current_week_info.get('endTime'),
            'startTime': current_week_info.get('startTime'),
            'jobId': job_info.get('jobId'),
            'weeks': current_week_string
        }
        api_client.submit_report(report_info)

        logger.info(
            f"第{week}周周报已提交，开始时间：{current_week_info.get('startTime')}, 结束时间：{current_week_info.get('endTime')}")

        return {
            "status": "success",
            "message": f"第{week}周周报已提交",
            "task_type": "周报提交",
            "details": {
                "周报标题": f"第{week}周周报",
                "开始时间": current_week_info.get('startTime'),
                "结束时间": current_week_info.get('endTime'),
                "附件": attachments
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
    """提交月报

    :param config: 配置管理器。
    :type config: ConfigManager
    :param api_client: ApiClient实例。
    :type api_client: ApiClient
    :return: 执行结果
    :rtype: Dict[str, Any]
    """
    if not config.get_value('config.reportSettings.monthly.enabled'):
        logger.info("用户未开启月报提交功能，跳过月报提交任务")
        return {
            "status": "skip",
            "message": "用户未开启月报提交功能",
            "task_type": "月报提交"
        }

    current_time = datetime.now()
    last_day_of_month = (current_time.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    submit_day = config.get_value('config.reportSettings.monthly.submitTime')

    if current_time.day != min(submit_day, last_day_of_month.day) or not (17 <= current_time.hour < 20):
        logger.info("未到月报提交时间")
        return {
            "status": "skip",
            "message": "未到月报提交时间",
            "task_type": "月报提交"
        }

    try:
        # 获取当前年月
        current_yearmonth = current_time.strftime('%Y-%m')

        # 获取历史提交记录
        submitted_reports_info = api_client.get_submitted_reports_info('month')
        submitted_reports = submitted_reports_info.get('data', [])

        # 检查是否已经提交过本月的月报
        if submitted_reports:
            last_report = submitted_reports[0]
            if last_report.get('yearmonth') == current_yearmonth:
                logger.info("本月已经提交过月报，跳过本次提交")
                return {
                    "status": "skip",
                    "message": "本月已经提交过月报",
                    "task_type": "月报提交"
                }

        job_info = api_client.get_job_info()
        month = submitted_reports_info.get('flag', 0) + 1
        content = generate_article(config, f"第{month}月月报", job_info)

        # 上传图片并获取附件
        attachments = upload_img(api_client, config, config.get_value('config.reportSettings.monthly.imageCount'))

        report_info = {
            'title': f"第{month}月月报",
            'content': content,
            'attachments': attachments,
            'yearmonth': current_yearmonth,
            'reportType': 'month',
            'jobId': job_info.get('jobId'),
        }
        api_client.submit_report(report_info)

        logger.info(f"第{month}月月报已提交，提交月份：{current_yearmonth}")

        return {
            "status": "success",
            "message": f"第{month}月月报已提交",
            "task_type": "月报提交",
            "details": {
                "月报标题": f"第{month}月月报",
                "提交月份": current_yearmonth,
                "附件": attachments
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


def run(config: ConfigManager) -> None:
    """执行所有任务

    :param config: 配置管理器
    :type config: ConfigManager
    """
    results: List[Dict[str, Any]] = []

    try:
        pusher = MessagePusher(config.get_value('config.pushNotifications'))
    except Exception as e:
        logger.error(f"获取消息推送客户端失败: {str(e)}")
        return

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
        pusher.push(results)
        logger.info("任务异常结束\n")
        return

    logger.info(f"开始执行：{config.get_value('userInfo.nikeName')}")

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

    pusher.push(results)
    logger.info(f"执行结束：{config.get_value('userInfo.nikeName')}")


def main(selected_files: list = None) -> None:
    """程序主入口

    :param selected_files: 选定的配置文件名（不带路径和后缀）
    :type selected_files: list
    """
    logger.info("工学云任务开始")

    json_files = {f[:-5]: f for f in os.listdir(USER_DIR) if f.endswith('.json')}
    if not json_files:
        logger.info("打卡文件未配置")
        return

    if selected_files:
        for selected_file in selected_files:
            if selected_file in json_files:
                run(ConfigManager(os.path.join(USER_DIR, json_files[selected_file])))
            else:
                logger.error(f"指定的文件 {selected_file}.json 不存在")
    else:
        for filename in json_files.values():
            run(ConfigManager(os.path.join(USER_DIR, filename)))

    logger.info("工学云任务结束")


if __name__ == '__main__':
    # 读取命令行参数
    parser = argparse.ArgumentParser(description="运行工学云任务")
    parser.add_argument('--file', type=str, nargs='+', help='指定要执行的配置文件名（不带路径和后缀），可以一次性指定多个')
    args = parser.parse_args()

    # 执行命令
    main(args.file)
