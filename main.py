import logging
import os
import json
import argparse
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import concurrent.futures

from coreApi.MainLogicApi import ApiClient
from coreApi.AiServiceClient import generate_article
from util.Config import ConfigManager
from util.MessagePush import MessagePusher
from util.HelperFunctions import desensitize_name, is_holiday
from util.FileUploader import upload_img

logging.basicConfig(
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

USER_DIR = os.path.join(os.path.dirname(__file__), "user")


def perform_clock_in(api_client: ApiClient, config: ConfigManager) -> Dict[str, Any]:
    """
    执行打卡操作。

    Args:
        api_client (ApiClient): ApiClient 实例。
        config (ConfigManager): 配置管理器。

    Returns:
        Dict[str, Any]: 执行结果。
    """
    try:
        current_time = datetime.now()
        current_hour = current_time.hour

        # 确定打卡类型
        if current_hour < 12:
            checkin_type = "START"
            display_type = "上班"
        else:
            checkin_type = "END"
            display_type = "下班"

        # 判断是否为节假日模式并跳过打卡
        if config.get_value("config.clockIn.mode") == "holiday" and is_holiday():
            if not config.get_value("config.clockIn.specialClockIn"):
                return {
                    "status": "skip",
                    "message": "今天是休息日，已跳过打卡",
                    "task_type": "打卡",
                }
            checkin_type = "HOLIDAY"
            display_type = "休息/节假日"

        # 判断自定义打卡日期模式并跳过打卡
        elif config.get_value("config.clockIn.mode") == "custom":
            today = datetime.today().weekday() + 1  # 获取星期几（1-7）
            if today not in config.get_value("config.clockIn.customDays"):
                if not config.get_value("config.clockIn.specialClockIn"):
                    return {
                        "status": "skip",
                        "message": "今天不在设置打卡时间范围内，已跳过打卡",
                        "task_type": "打卡",
                    }
                checkin_type = "HOLIDAY"
                display_type = "休息/节假日"

        last_checkin_info = api_client.get_checkin_info()

        # 检查是否已经打过卡
        if last_checkin_info and last_checkin_info["type"] == checkin_type:
            last_checkin_time = datetime.strptime(
                last_checkin_info["createTime"], "%Y-%m-%d %H:%M:%S"
            )
            if last_checkin_time.date() == current_time.date():
                logger.info(f"今日 {display_type} 卡已打，无需重复打卡")
                return {
                    "status": "skip",
                    "message": f"今日 {display_type} 卡已打，无需重复打卡",
                    "task_type": "打卡",
                }

        user_name = desensitize_name(config.get_value("userInfo.nikeName"))
        logger.info(f"用户 {user_name} 开始 {display_type} 打卡")

        # 打卡图片和备注
        attachments = upload_img(
            api_client.get_upload_token(),
            config.get_value("userInfo.orgJson.snowFlakeId"),
            config.get_value("userInfo.userId"),
            config.get_value("config.clockIn.imageCount"),
        )
        description = (
            random.choice(config.get_value("config.clockIn.description"))
            if config.get_value("config.clockIn.description")
            else None
        )

        # 设置打卡信息
        checkin_info = {
            "type": checkin_type,
            "lastDetailAddress": last_checkin_info.get("address"),
            "attachments": attachments or None,
            "description": description,
        }

        api_client.submit_clock_in(checkin_info)
        logger.info(f"用户 {user_name} {display_type} 打卡成功")

        return {
            "status": "success",
            "message": f"{display_type}打卡成功",
            "task_type": "打卡",
            "details": {
                "姓名": config.get_value("userInfo.nikeName"),
                "打卡类型": display_type,
                "打卡时间": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "打卡地点": config.get_value("config.clockIn.location.address"),
            },
        }
    except Exception as e:
        logger.error(f"打卡失败: {e}")
        return {"status": "fail", "message": f"打卡失败: {str(e)}", "task_type": "打卡"}


def submit_daily_report(api_client: ApiClient, config: ConfigManager) -> Dict[str, Any]:
    """
    提交日报。

    Args:
        api_client (ApiClient): ApiClient 实例。
        config (ConfigManager): 配置管理器。

    Returns:
        Dict[str, Any]: 执行结果。
    """
    if not config.get_value("config.reportSettings.daily.enabled"):
        logger.info("用户未开启日报提交功能，跳过日报提交任务")
        return {
            "status": "skip",
            "message": "用户未开启日报提交功能",
            "task_type": "日报提交",
        }

    current_time = datetime.now()
    if not (current_time.hour >= 12):
        logger.info("未到日报提交时间（需12点后）")
        return {
            "status": "skip",
            "message": "未到日报提交时间（需12点后）",
            "task_type": "日报提交",
        }

    try:
        # 获取历史提交记录
        submitted_reports_info = api_client.get_submitted_reports_info("day")
        submitted_reports = submitted_reports_info.get("data", [])

        # 检查是否已经提交过今天的日报
        if submitted_reports:
            last_report = submitted_reports[0]
            last_submit_time = datetime.strptime(
                last_report["createTime"], "%Y-%m-%d %H:%M:%S"
            )
            if last_submit_time.date() == current_time.date():
                logger.info("今天已经提交过日报，跳过本次提交")
                return {
                    "status": "skip",
                    "message": "今天已经提交过日报",
                    "task_type": "日报提交",
                }

        job_info = api_client.get_job_info()
        report_count = submitted_reports_info.get("flag", 0) + 1
        content = generate_article(config, f"第{report_count}天日报", job_info)

        # 上传图片并获取附件
        attachments = upload_img(
            api_client.get_upload_token(),
            config.get_value("userInfo.orgJson.snowFlakeId"),
            config.get_value("userInfo.userId"),
            config.get_value("config.reportSettings.daily.imageCount"),
        )

        report_info = {
            "title": f"第{report_count}天日报",
            "content": content,
            "attachments": attachments,
            "reportType": "day",
            "jobId": job_info.get("jobId", None),
            "reportTime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "formFieldDtoList": api_client.get_from_info(7),
        }
        api_client.submit_report(report_info)

        logger.info(
            f"第{report_count}天日报已提交，提交时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return {
            "status": "success",
            "message": f"第{report_count}天日报已提交",
            "task_type": "日报提交",
            "details": {
                "日报标题": f"第{report_count}天日报",
                "提交时间": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "附件": attachments,
            },
            "report_content": content,
        }
    except Exception as e:
        logger.error(f"日报提交失败: {e}")
        return {
            "status": "fail",
            "message": f"日报提交失败: {str(e)}",
            "task_type": "日报提交",
        }


def submit_weekly_report(
    config: ConfigManager, api_client: ApiClient
) -> Dict[str, Any]:
    """提交周报

    Args:
        config (ConfigManager): 配置管理器。
        api_client (ApiClient): ApiClient 实例。

    Returns:
        Dict[str, Any]: 执行结果。
    """
    if not config.get_value("config.reportSettings.weekly.enabled"):
        logger.info("用户未开启周报提交功能，跳过周报提交任务")
        return {
            "status": "skip",
            "message": "用户未开启周报提交功能",
            "task_type": "周报提交",
        }

    current_time = datetime.now()
    submit_day = config.get_value("config.reportSettings.weekly.submitTime")

    if current_time.weekday() + 1 != submit_day or not (current_time.hour >= 12):
        logger.info("未到周报提交时间")
        return {
            "status": "skip",
            "message": "未到周报提交时间",
            "task_type": "周报提交",
        }

    try:
        # 获取当前周信息
        current_week_info = api_client.get_weeks_date()[0]

        # 获取历史提交记录
        submitted_reports_info = api_client.get_submitted_reports_info("week")
        submitted_reports = submitted_reports_info.get("data", [])

        # 获取当前周数
        week = submitted_reports_info.get("flag", 0) + 1
        current_week_string = f"第{week}周"

        # 检查是否已经提交过本周的周报
        if submitted_reports:
            last_report = submitted_reports[0]
            if last_report.get("weeks") == current_week_string:
                logger.info("本周已经提交过周报，跳过本次提交")
                return {
                    "status": "skip",
                    "message": "本周已经提交过周报",
                    "task_type": "周报提交",
                }

        job_info = api_client.get_job_info()
        content = generate_article(config, f"第{week}周周报", job_info)

        # 上传图片并获取附件
        attachments = upload_img(
            api_client.get_upload_token(),
            config.get_value("userInfo.orgJson.snowFlakeId"),
            config.get_value("userInfo.userId"),
            config.get_value("config.reportSettings.weekly.imageCount"),
        )

        report_info = {
            "title": f"第{week}周周报",
            "content": content,
            "attachments": attachments,
            "reportType": "week",
            "endTime": current_week_info.get("endTime"),
            "startTime": current_week_info.get("startTime"),
            "jobId": job_info.get("jobId", None),
            "weeks": current_week_string,
            "formFieldDtoList": api_client.get_from_info(8),
        }
        api_client.submit_report(report_info)

        logger.info(
            f"第{week}周周报已提交，开始时间：{current_week_info.get('startTime')},结束时间：{current_week_info.get('endTime')}"
        )

        return {
            "status": "success",
            "message": f"第{week}周周报已提交",
            "task_type": "周报提交",
            "details": {
                "周报标题": f"第{week}周周报",
                "开始时间": current_week_info.get("startTime"),
                "结束时间": current_week_info.get("endTime"),
                "附件": attachments,
            },
            "report_content": content,
        }
    except Exception as e:
        logger.error(f"周报提交失败: {e}")
        return {
            "status": "fail",
            "message": f"周报提交失败: {str(e)}",
            "task_type": "周报提交",
        }


def submit_monthly_report(
    config: ConfigManager, api_client: ApiClient
) -> Dict[str, Any]:
    """提交月报

    Args:
        config (ConfigManager): 配置管理器。
        api_client (ApiClient): ApiClient 实例。

    Returns:
        Dict[str, Any]: 执行结果。
    """
    if not config.get_value("config.reportSettings.monthly.enabled"):
        logger.info("用户未开启月报提交功能，跳过月报提交任务")
        return {
            "status": "skip",
            "message": "用户未开启月报提交功能",
            "task_type": "月报提交",
        }

    current_time = datetime.now()
    last_day_of_month = (current_time.replace(day=1) + timedelta(days=32)).replace(
        day=1
    ) - timedelta(days=1)
    submit_day = config.get_value("config.reportSettings.monthly.submitTime")

    if current_time.day != min(submit_day, last_day_of_month.day) or not (
        current_time.hour >= 12
    ):
        logger.info("未到月报提交时间")
        return {
            "status": "skip",
            "message": "未到月报提交时间",
            "task_type": "月报提交",
        }

    try:
        # 获取当前年月
        current_yearmonth = current_time.strftime("%Y-%m")

        # 获取历史提交记录
        submitted_reports_info = api_client.get_submitted_reports_info("month")
        submitted_reports = submitted_reports_info.get("data", [])

        # 检查是否已经提交过本月的月报
        if submitted_reports:
            last_report = submitted_reports[0]
            if last_report.get("yearmonth") == current_yearmonth:
                logger.info("本月已经提交过月报，跳过本次提交")
                return {
                    "status": "skip",
                    "message": "本月已经提交过月报",
                    "task_type": "月报提交",
                }

        job_info = api_client.get_job_info()
        month = submitted_reports_info.get("flag", 0) + 1
        content = generate_article(config, f"第{month}月月报", job_info)

        # 上传图片并获取附件
        attachments = upload_img(
            api_client.get_upload_token(),
            config.get_value("userInfo.orgJson.snowFlakeId"),
            config.get_value("userInfo.userId"),
            config.get_value("config.reportSettings.monthly.imageCount"),
        )

        report_info = {
            "title": f"第{month}月月报",
            "content": content,
            "attachments": attachments,
            "yearmonth": current_yearmonth,
            "reportType": "month",
            "jobId": job_info.get("jobId", None),
            "formFieldDtoList": api_client.get_from_info(9),
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
                "附件": attachments,
            },
            "report_content": content,
        }
    except Exception as e:
        logger.error(f"月报提交失败: {e}")
        return {
            "status": "fail",
            "message": f"月报提交失败: {str(e)}",
            "task_type": "月报提交",
        }


def run(config: ConfigManager) -> None:
    """
    执行所有任务。

    Args:
        config (ConfigManager): 配置管理器。
    """
    results: List[Dict[str, Any]] = []

    try:
        pusher = MessagePusher(config.get_value("config.pushNotifications"))
    except Exception as e:
        logger.error(f"获取消息推送客户端失败: {str(e)}")
        return

    try:
        api_client = ApiClient(config)
        if not config.get_value("userInfo.token"):
            api_client.login()
        if not config.get_value("planInfo.planId"):
            api_client.fetch_internship_plan()
        else:
            logger.info("使用本地数据")
    except Exception as e:
        error_message = f"获取API客户端失败: {str(e)}"
        logger.error(error_message)
        results.append(
            {"status": "fail", "message": error_message, "task_type": "API客户端初始化"}
        )
        pusher.push(results)
        logger.info("任务异常结束")
        return

    logger.info(f"开始执行：{desensitize_name(config.get_value('userInfo.nikeName'))}")

    try:
        results = [
            perform_clock_in(api_client, config),
            submit_daily_report(api_client, config),
            submit_weekly_report(config, api_client),
            submit_monthly_report(config, api_client),
        ]
    except Exception as e:
        error_message = f"执行任务时发生错误: {str(e)}"
        logger.error(error_message)
        results.append(
            {"status": "fail", "message": error_message, "task_type": "任务执行"}
        )

    pusher.push(results)
    logger.info(f"执行结束：{desensitize_name(config.get_value('userInfo.nikeName'))}")


def execute_tasks(selected_files: Optional[List[str]] = None):
    """
    创建并执行任务。

    Args:
        selected_files (Optional[List[str]]): 指定配置文件列表（不含扩展名），默认为 None。
    """
    logger.info("开始执行工学云任务")

    # 获取用户目录下的所有 .json 文件(不含后缀)
    try:
        json_files = [f[:-5] for f in os.listdir(USER_DIR) if f.endswith(".json")]
        logger.info(f"发现 {len(json_files)} 个配置文件")
    except OSError as e:
        logger.error(f"扫描配置文件目录失败: {e}")
        json_files = []

    # 筛选指定的配置文件
    if selected_files:
        existing_files = set(selected_files) & set(json_files)
        missing_files = set(selected_files) - existing_files
        if missing_files:
            logger.error(f"以下配置文件未找到: {', '.join(missing_files)}")
        json_files = list(existing_files)

    # 从环境变量获取配置
    try:
        user_env = os.getenv("USER", "[]")
        user_configs = json.loads(user_env)
        if not isinstance(user_configs, list):
            raise ValueError("环境变量 USER 必须包含 JSON 数组")
        logger.info(f"从环境变量中获取到 {len(user_configs)} 个配置")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"解析环境变量 USER 失败: {e}")
        user_configs = []

    # 检查是否存在有效配置
    if not json_files and not user_configs:
        logger.warning("未找到任何有效配置")
        return

    # 创建任务列表
    tasks = []

    def add_task(source, **kwargs):
        try:
            tasks.append(ConfigManager(**kwargs))
            logger.debug(f"已添加来自 {source} 的任务配置")
        except Exception as err:
            logger.error(f"创建来自 {source} 的任务失败: {err}")

    # 处理环境变量中的配置
    for config in user_configs:
        add_task("环境变量", config=config)

    # 处理配置文件
    for name in json_files:
        file_path = os.path.join(USER_DIR, f"{name}.json")
        add_task(f"配置文件 {name}", path=file_path)

    if not tasks:
        logger.error("没有成功创建任何任务")
        return

    # 执行任务
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_task = {executor.submit(run, task): task for task in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"任务 {task} 处理过程中发生错误: {e}")

    logger.info("工学云任务执行结束")


if __name__ == "__main__":
    # 读取命令行参数
    parser = argparse.ArgumentParser(description="运行工学云任务")
    parser.add_argument(
        "--file",
        type=str,
        nargs="+",
        help="指定要执行的配置文件名（不带路径和后缀），可以一次性指定多个",
    )
    args = parser.parse_args()

    # 执行命令
    execute_tasks(args.file)
