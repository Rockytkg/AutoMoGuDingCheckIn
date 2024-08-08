import logging
import os

from util.Api import ApiClient
from util.ConfigManager import ConfigManager
from util.MessagePusher import push_message

# 配置日志
logging.basicConfig(
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %I:%M:%S"
)
logger = logging.getLogger("MainModule")

USER_DIR = os.path.join(os.path.dirname(__file__), "user")


def get_api_client(config_manager: ConfigManager) -> ApiClient:
    api_client = ApiClient(config_manager)
    if not config_manager.get_user_info('token'):
        api_client.login()
    if not config_manager.get_plan_info('planId'):
        api_client.fetch_internship_plan()
    else:
        logger.info("使用本地数据")

    return api_client


def run(config_manager: ConfigManager) -> None:
    try:
        api_client = get_api_client(config_manager)
        checkin_info = api_client.get_checkin_info()

        if checkin_info.get('type') == 'START':
            checkin_info['type'] = 'END'
            clock_type = '下班'
        else:
            checkin_info['type'] = 'START'
            clock_type = '上班'

        user_name = config_manager.get_user_info('nikeName')
        logger.info(f'用户 {user_name} 开始签到')

        api_client.submit_clock_in(checkin_info)

        message = f"{user_name} {clock_type} 打卡成功！"
        logger.info(message)

        # TODO: [日报、周报、月报相关逻辑]
        # logger.info("检查是否提交日报")
        # logger.info("检查是否提交周报")
        # logger.info("检查是否提交月报")

    except Exception as e:
        logger.error(f"运行时出现异常: {e}")
        message = f"运行时出现异常：{str(e)}"

    push_key = config_manager.get_config('pushKey')
    push_type = config_manager.get_config('pushType')

    if push_key and push_type:
        push_message(
            push_type,
            '工学云消息',
            message,
            push_key
        )
    else:
        logger.info("用户未配置推送")

    logger.info("--------------------------")


def main() -> None:
    logger.info("工学云打卡开始")

    json_files = [f for f in os.listdir(USER_DIR) if f.endswith('.json')]

    if not json_files:
        logger.info("打卡文件未配置")

    for filename in json_files:
        config_manager = ConfigManager(os.path.join(USER_DIR, filename))
        run(config_manager)

    logger.info("工学云打卡结束")


if __name__ == '__main__':
    main()
