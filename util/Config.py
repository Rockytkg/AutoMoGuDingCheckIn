import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """管理配置文件的加载、验证和更新。"""

    def __init__(
        self, path: Optional[str] = None, config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化ConfigManager实例。

        Args:
            path (Optional[str]): 配置文件的路径。默认为 None。
            config (Optional[Dict[str, Any]]): 直接传入的配置字典。如果传入此参数，则不从文件加载配置。默认为 None。
        """
        if config is not None:
            self._config = config
            self._path = None
            logger.info("使用直接传入的配置字典初始化")
        elif path is not None:
            self._path = Path(path)
            self._config = self._load_config()
        else:
            raise ValueError("必须提供路径或配置字典之一")

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件并修改经纬度。

        Returns:
            加载的配置字典。

        Raises:
            FileNotFoundError: 如果配置文件未找到。
            json.JSONDecodeError: 如果配置文件格式错误。
        """
        try:
            # 打开并加载配置文件
            with open(str(self._path), "r", encoding="utf-8") as jsonfile:
                config = json.load(jsonfile)

            # 确保 config 和 clockIn 字典存在
            config.setdefault("config", {})
            clock_in = config["config"].setdefault("clockIn", {})

            # 检查并添加 mode 字段
            if "mode" not in clock_in:
                clock_in["mode"] = "daily"
                logger.warning(
                    "配置文件中缺少 'mode' 字段，已自动添加默认值 'daily'。"
                    "请尽快更新配置文件以确保正确性。"
                )

            # 确保 location 字典存在
            location = clock_in.setdefault("location", {})

            # 为经纬度添加随机偏移
            for coord in ["latitude", "longitude"]:
                value = location.get(coord)
                if isinstance(value, str) and len(value) > 1:
                    location[coord] = value[:-1] + str(random.randint(0, 9))

            logger.info(f"配置文件已加载: {self._path}")
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"配置文件加载失败: {e}")
            raise

    def get_value(self, *keys: str) -> Any:
        """
        获取配置中的值。

        Args:
            *keys (str): 配置的键名序列。

        Returns:
            Any: 配置中的值。如果键不存在，返回None。
        """
        value = self._config
        try:
            for key in keys:
                # 拆分点（.）符号的键名
                for sub_key in key.split("."):
                    value = value[sub_key]
            return value
        except KeyError:
            logger.warning(f"配置键不存在: {'->'.join(keys)}")
            return None

    def update_config(self, value: Any, *keys: str) -> None:
        """
        更新配置并保存（如果是从文件加载的配置）。

        Args:
            value (Any): 配置的新值。
            keys (str): 配置的键名序列，用点（.）分隔。
        """
        config = self._config
        try:
            for key in keys[:-1]:
                # 使用 setdefault 确保中间的字典存在
                config = config.setdefault(key, {})
            # 更新或设置最后一个键名的值
            config[keys[-1]] = value

            # 如果从文件加载，则保存配置
            if self._path is not None:
                self._save_config()
            else:
                logger.info("配置已更新（未保存到文件，因为直接使用字典初始化）")
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            raise

    def _save_config(self) -> None:
        """
        保存配置到文件。
        """
        if self._path is None:
            logger.warning("直接使用字典初始化时，_save_config 方法无效")
            return

        try:
            with self._path.open("w", encoding="utf-8") as jsonfile:
                json.dump(self._config, jsonfile, ensure_ascii=False, indent=2)
            logger.info(f"配置文件已更新: {self._path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise

    @property
    def config(self) -> Dict[str, Any]:
        """
        获取配置字典的只读副本。

        Returns:
            配置字典的副本。
        """
        return self._config.copy()
