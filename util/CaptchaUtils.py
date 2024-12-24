import base64
import json
import logging
import random
import struct

import ddddocr

logger = logging.getLogger(__name__)


def calculate_precise_slider_distance(
    target_start_x: int, target_end_x: int, slider_width: int
) -> float:
    """
    计算滑块需要移动的精确距离，并添加微小随机偏移。

    Args:
        target_start_x (int): 目标区域的起始x坐标。
        target_end_x (int): 目标区域的结束x坐标。
        slider_width (int): 滑块的宽度。

    Returns:
        float: 精确到小数点后1位的滑动距离，包含微小随机偏移。
    """
    try:
        # 计算目标区域的中心点x坐标
        target_center_x = (target_start_x + target_end_x) / 2

        # 计算滑块初始位置的中心点x坐标
        slider_initial_center_x = slider_width / 2

        # 计算滑块需要移动的精确距离
        precise_distance = target_center_x - slider_initial_center_x

        # 添加一个随机的微小偏移，模拟真实用户滑动
        random_offset = random.uniform(-0.1, 0.1)

        # 将最终距离四舍五入到小数点后1位
        final_distance = round(precise_distance + random_offset, 1)

        logger.info(f"计算滑块距离成功: {final_distance}")
        return final_distance

    except Exception as e:
        logger.error(f"计算滑块距离时发生错误: {e}")
        raise


def extract_png_width(png_binary: bytes) -> int:
    """
    从PNG二进制数据中提取图像宽度。

    Args:
        png_binary (bytes): PNG图像的二进制数据。

    Returns:
        int: PNG图像的宽度（以像素为单位）。

    Raises:
        ValueError: 如果输入数据不是有效的PNG图像。
    """
    try:
        # 检查PNG文件头是否合法（固定8字节的PNG签名）
        if png_binary[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("无效的PNG签名：不是有效的PNG图像")

        # 从PNG数据的固定位置提取宽度信息
        width = struct.unpack(">I", png_binary[16:20])[0]
        logger.info(f"提取PNG宽度成功: {width}")
        return width

    except struct.error as e:
        logger.error(f"无法从PNG数据中提取宽度信息: {e}")
        raise ValueError("无法从PNG数据中提取宽度信息") from e

    except Exception as e:
        logger.error(f"提取PNG宽度时发生错误: {e}")
        raise


def slide_match(target_bytes: bytes = None, background_bytes: bytes = None) -> list:
    """
    获取验证区域坐标，使用目标检测算法。

    Args:
        target_bytes (bytes): 滑块图片二进制数据，默认为 None。
        background_bytes (bytes): 背景图片二进制数据，默认为 None。

    Returns:
        list: 目标区域左边界坐标，右边界坐标。
    """
    det = ddddocr.DdddOcr(ocr=False, show_ad=False)
    res = det.slide_match(target_bytes, background_bytes)
    x1, _, x2, _ = res["target"]

    return [x1, x2]


def recognize_captcha(target: str, background: str) -> str:
    """
    识别图像验证码。

    Args:
        target (str): 目标图像的二进制数据的base64编码。
        background (str): 背景图像的二进制数据的base64编码。

    Returns:
        str: 滑块需要滑动的距离。
    """
    try:
        # 将base64编码的字符串解码为二进制数据
        target_bytes = base64.b64decode(target)
        background_bytes = base64.b64decode(background)

        # 调用滑块匹配算法获取目标区域的坐标
        res = slide_match(target_bytes=target_bytes, background_bytes=background_bytes)

        # 从滑块图像提取宽度信息
        target_width = extract_png_width(target_bytes)

        # 计算滑块需要移动的距离
        slider_distance = calculate_precise_slider_distance(
            res[0], res[1], target_width
        )

        # 构造返回的数据，格式为JSON
        slider_data = {
            "x": slider_distance,
            "y": 5,
        }  # 固定y值为5
        logger.info(f"验证码识别成功: {slider_data}")
        return json.dumps(slider_data, separators=(",", ":"))

    except Exception as e:
        logger.error(f"验证码识别时发生错误: {e}")
        raise
