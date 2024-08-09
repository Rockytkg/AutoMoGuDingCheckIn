import logging
import os

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


def get_api_client(config_manager: ConfigManager) -> ApiClient:
    """获取配置好的ApiClient实例。

    如果本地不存在用户Token或实习计划ID，执行登录或获取实习计划的操作。

    :param config_manager: 配置管理器实例。
    :type config_manager: ConfigManager

    :return: 配置好的ApiClient实例。
    :rtype: ApiClient
    """
    api_client = ApiClient(config_manager)
    if not config_manager.get_user_info('token'):
        api_client.login()
    if not config_manager.get_plan_info('planId'):
        api_client.fetch_internship_plan()
    else:
        logger.info("使用本地数据")
    return api_client


def run(config_manager: ConfigManager) -> None:
    """执行打卡流程。

    根据当前打卡类型（上班或下班）切换状态并提交打卡信息。
    处理异常并根据配置发送推送消息。

    :param config_manager: 配置管理器实例。
    :type config_manager: ConfigManager
    """
    try:
        api_client = get_api_client(config_manager)
        checkin_info = api_client.get_checkin_info()

        # 切换打卡类型
        checkin_info['type'] = 'END' if checkin_info.get('type') == 'START' else 'START'
        clock_type = '下班' if checkin_info['type'] == 'END' else '上班'

        user_name = config_manager.get_user_info('nikeName')
        logger.info(f'用户 {user_name} 开始签到')
        api_client.submit_clock_in(checkin_info)
        message = f"{user_name} {clock_type} 打卡成功！"
        logger.info(message)

    except Exception as e:
        logger.error(f"运行时出现异常: {e}")
        message = f"运行时出现异常：{str(e)}"

    push_key = config_manager.get_config('pushKey')
    push_type = config_manager.get_config('pushType')

    if push_key and push_type:
        pusher = MessagePusher(push_key, push_type)
        pusher.push('工学云消息', message)
    else:
        logger.info("用户未配置推送")

    logger.info("--------------------------")


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
