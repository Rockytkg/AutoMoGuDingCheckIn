import logging
import random
import json
from typing import Any, Dict

logging.basicConfig(
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %I:%M:%S"
)
logger = logging.getLogger("UserConfig")


class ConfigManager:
    """管理配置文件的加载、验证和更新。

    Attributes:
        path (str): 配置文件路径。
        config (dict): 加载的配置字典。
        required_fields (list): 配置文件中必需的字段。
    """

    required_fields = [
        'password', 'phone', 'address', 'latitude', 'longitude', 'province', 'city', 'area', 'device'
    ]

    def __init__(self, path: str):
        """初始化ConfigManager实例并加载配置文件。

        :param path: 配置文件的路径。
        :type path: str
        """
        self.path = path
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件。

        :return: 加载的配置字典。
        :rtype: dict

        :raises FileNotFoundError: 如果配置文件未找到。
        :raises json.JSONDecodeError: 如果配置文件格式错误。
        """
        try:
            with open(self.path, 'r', encoding='utf-8') as jsonfile:
                config = json.load(jsonfile)
            logger.info(f"配置文件已加载: {self.path}")
            return config
        except FileNotFoundError:
            logger.error(f"配置文件未找到: {self.path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"配置文件格式错误: {self.path}")
            raise

    def _validate_config(self) -> None:
        """验证配置文件中是否包含所有必需的字段。

        :raises ValueError: 如果配置文件中缺少必需的字段。
        """
        config_data = self.config.get('config', {})

        # 检查是否启用周报或月报
        is_weekly = config_data.get('isSubmittedWeekly', False)
        is_monthly = config_data.get('isSubmittedMonthlyReport', False)

        # 如果任意一种提交方式被启用，检查必填字段
        for field in self.required_fields:
            if field not in config_data:
                logger.error(f"配置错误：'{field}' 为必填项")
                raise ValueError(f"配置错误：'{field}' 为必填项")

        if is_weekly and 'submitWeeklyTime' not in config_data:
            logger.error("配置错误：启用了周报提交，但缺少 'submitWeeklyTime' 字段。请在配置中添加该字段。")
            raise ValueError("配置错误：启用了周报提交，但缺少 'submitWeeklyTime' 字段。请在配置中添加该字段。")

        if is_monthly and 'submitMonthlyReportTime' not in config_data:
            logger.error("配置错误：启用了月报提交，但缺少 'submitMonthlyReportTime' 字段。请在配置中添加该字段。")
            raise ValueError("配置错误：启用了月报提交，但缺少 'submitMonthlyReportTime' 字段。请在配置中添加该字段。")

    def get_config(self, key: str) -> Any:
        """获取config字段中的值。

        :param key: 配置的键名。
        :type key: str

        :return: 配置中的值。如果键名是'latitude'或'longitude'，将随机修改最后一位数字。
        :rtype: Any
        """
        value = self.config.get('config', {}).get(key, None)
        if key in ['latitude', 'longitude'] and value is not None:
            return str(value)[:-1] + str(random.randint(0, 9))
        return value

    def get_plan_info(self, key: str) -> Any:
        """获取planInfo字段中的值。

        :param key: 配置的键名。
        :type key: str

        :return: 配置中的值。
        :rtype: Any
        """
        return self.config.get('planInfo', {}).get(key, None)

    def get_user_info(self, key: str) -> Any:
        """获取userInfo字段中的值。

        :param key: 配置的键名。
        :type key: str

        :return: 配置中的值。
        :rtype: Any
        """
        return self.config.get('userInfo', {}).get(key, None)

    def update_config(self, key: str, value: Any) -> None:
        """更新config字段中的配置并保存。

        :param key: 配置的键名。
        :type key: str
        :param value: 配置的新值。
        :type value: Any
        """
        self.config[key] = value
        self._save_config()

    def _save_config(self) -> None:
        """保存配置到文件。

        该方法将当前的配置字典保存到指定的配置文件中，确保配置的更新能够持久化。

        """
        with open(self.path, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.config, jsonfile, ensure_ascii=False, indent=4)
        logger.info(f"配置文件已更新: {self.path}")
