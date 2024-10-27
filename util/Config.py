import json
import logging
import random
from typing import Any, Dict
from pathlib import Path


class ConfigManager:
    """管理配置文件的加载、验证和更新。"""

    def __init__(self, path: str):
        """
        初始化ConfigManager实例并加载配置文件。

        :param path: 配置文件的路径。
        """
        self._path = Path(path)
        self._logger = logging.getLogger(__name__)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件并修改经纬度。

        :return: 加载的配置字典。
        :raises FileNotFoundError: 如果配置文件未找到。
        :raises json.JSONDecodeError: 如果配置文件格式错误。
        """
        try:
            with self._path.open('r', encoding='utf-8') as jsonfile:
                config = json.load(jsonfile)

            # 为经纬度添加随机偏移
            location = config.get('config', {}).get('clockIn', {}).get('location', {})
            for coord in ['latitude', 'longitude']:
                if coord in location and isinstance(location[coord], str) and len(location[coord]) > 1:
                    location[coord] = location[coord][:-1] + str(random.randint(0, 9))

            self._logger.info(f"配置文件已加载: {self._path}")
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self._logger.error(f"配置文件加载失败: {e}")
            raise

    def get_value(self, *keys: str) -> Any:
        """
        获取配置中的值。

        :param keys: 配置的键名序列。
        :return: 配置中的值。如果键不存在，返回None。
        """
        value = self._config
        try:
            for key in keys:
                # 拆分点（.）符号的键名
                for sub_key in key.split('.'):
                    value = value[sub_key]
            return value
        except KeyError:
            self._logger.warning(f"配置键不存在: {'->'.join(keys)}")
            return None

    def update_config(self, value: Any, *keys: str) -> None:
        """
        更新配置并保存。

        :param value: 配置的新值。
        :param keys: 配置的键名序列，用点（.）分隔。
        """
        config = self._config
        try:
            for key in keys[:-1]:
                # 使用 setdefault 确保中间的字典存在
                config = config.setdefault(key, {})
            # 更新或设置最后一个键名的值
            config[keys[-1]] = value
            self._save_config()
        except Exception as e:
            self._logger.error(f"更新配置失败: {e}")
            raise

    def _save_config(self) -> None:
        """
        保存配置到文件。
        """
        try:
            with self._path.open('w', encoding='utf-8') as jsonfile:
                json.dump(self._config, jsonfile, ensure_ascii=False, indent=2)
            self._logger.info(f"配置文件已更新: {self._path}")
        except Exception as e:
            self._logger.error(f"保存配置文件失败: {e}")
            raise

    @property
    def config(self) -> Dict[str, Any]:
        """
        获取配置字典的只读副本。

        :return: 配置字典的副本。
        """
        return self._config.copy()
