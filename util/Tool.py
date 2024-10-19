import logging
import struct
import random
import json
import base64
from hashlib import md5
from datetime import datetime, timedelta

import ddddocr
from aes_pkcs5.algorithms.aes_ecb_pkcs5_padding import AESECBPKCS5Padding

logging.basicConfig(
    format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %I:%M:%S'
)
logger = logging.getLogger('ToolModule')


def create_sign(*args) -> str:
    """生成签名。

    该方法接收任意数量的参数，将它们连接成一个字符串，并附加一个预定义的密钥后，
    生成并返回该字符串的MD5签名。

    :param args: 要生成签名的参数。
    :type args: str

    :return: 生成的MD5签名。
    :rtype: str
    """
    sign_str = ''.join(args) + "3478cbbc33f84bd00d75d7dfa69e0daa"
    return md5(sign_str.encode("utf-8")).hexdigest()


def aes_encrypt(plaintext: str, key: str = "23DbtQHR2UMbH6mJ", out_format: str = "hex") -> str:
    """AES加密。

    该方法使用指定的密钥对给定的明文字符串进行AES加密，并返回加密后的密文。

    :param plaintext: 明文字符串。
    :type plaintext: str
    :param key: AES密钥，默认 "23DbtQHR2UMbH6mJ"。
    :type key: str
    :param out_format: 输出格式，默认 "hex"。
    :type out_format: str

    :return: 加密后的密文。
    :rtype: str

    :raises ValueError: 如果加密失败，抛出包含详细错误信息的异常。
    """
    try:
        cipher = AESECBPKCS5Padding(key, out_format)
        ciphertext = cipher.encrypt(plaintext)
        return ciphertext
    except Exception as e:
        logger.error(f"加密失败: {e}")
        raise ValueError(f"加密失败: {str(e)}")


def aes_decrypt(ciphertext: str, key: str = "23DbtQHR2UMbH6mJ", out_format: str = "hex") -> str:
    """AES解密。

    该方法使用指定的密钥对给定的密文字符串进行AES解密，并返回解密后的明文。

    :param ciphertext: 密文字符串。
    :type ciphertext: str
    :param key: AES密钥，默认 "23DbtQHR2UMbH6mJ"。
    :type key: str
    :param out_format: 输出格式，默认 "hex"。
    :type out_format: str

    :return: 解密后的明文。
    :rtype: str

    :raises ValueError: 如果解密失败，抛出包含详细错误信息的异常。
    """
    try:
        cipher = AESECBPKCS5Padding(key, out_format)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext
    except Exception as e:
        logger.error(f"解密失败: {e}")
        raise ValueError(f"解密失败: {str(e)}")


def get_current_month_info() -> dict:
    """获取当前月份的开始和结束时间。

    该方法计算当前月份的开始日期和结束日期，并将它们返回为字典，
    字典中包含这两项的字符串表示。

    :return: 包含当前月份开始和结束时间的字典。
    :rtype: dict
    """
    now = datetime.now()

    start_of_month = datetime(now.year, now.month, 1)

    if now.month == 12:
        next_month_start = datetime(now.year + 1, 1, 1)
    else:
        next_month_start = datetime(now.year, now.month + 1, 1)

    end_of_month = next_month_start - timedelta(days=1)

    start_time_str = start_of_month.strftime('%Y-%m-%d %H:%M:%S')
    end_time_str = end_of_month.strftime('%Y-%m-%d 00:00:00Z')

    return {"startTime": start_time_str, "endTime": end_time_str}


def calculate_precise_slider_distance(target_start_x: int, target_end_x: int, slider_width: int) -> float:
    """
    计算滑块需要移动的精确距离，并添加微小随机偏移。

    :param target_start_x: 目标区域的起始x坐标
    :type: int
    :param target_end_x: 目标区域的结束x坐标
    :type: int
    :param slider_width: 滑块的宽度
    :type: int

    :return: 精确到小数点后14位的滑动距离，包含微小随机偏移
    :rtype: float
    """
    target_center_x = (target_start_x + target_end_x) / 2
    slider_initial_center_x = slider_width / 2
    precise_distance = target_center_x - slider_initial_center_x
    random_offset = random.uniform(-0.1, 0.1)
    final_distance = round(precise_distance + random_offset, 1)

    return final_distance


def extract_png_width(png_binary):
    """从PNG二进制数据中提取图像宽度。

    该函数从给定的PNG格式二进制数据中提取并返回图像的宽度。

    :param png_binary: PNG图像的二进制数据。
    :type png_binary: bytes

    :return: PNG图像的宽度（以像素为单位）。
    :rtype: int

    :raises ValueError: 如果输入数据不是有效的PNG图像，抛出包含详细错误信息的异常。
    """
    if png_binary[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError("无效的PNG签名：不是有效的PNG图像")
    try:
        width = struct.unpack('>I', png_binary[16:20])[0]
    except struct.error:
        raise ValueError("无法从PNG数据中提取宽度信息")

    return width


def recognize_captcha(target: str, background: str) -> str:
    """识别图像验证码。

    :param target: 目标图像的二进制数据的base64编码
    :type target: str
    :param background: 背景图像的二进制数据的base64编码
    :type background: str

    :return: 滑块需要滑动的距离
    :rtype: str
    """
    target_bytes = base64.b64decode(target)
    background_bytes = base64.b64decode(background)
    slide = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    res = slide.slide_match(target_bytes=target_bytes, background_bytes=background_bytes, simple_target=True)
    target_width = extract_png_width(target_bytes)
    slider_distance = calculate_precise_slider_distance(res['target'][0], res['target'][2], target_width)
    slider_data = {"x": slider_distance, "y": 5}
    return json.dumps(slider_data, separators=(',', ':'))
