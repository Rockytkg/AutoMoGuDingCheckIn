import logging
from hashlib import md5
from datetime import datetime, timedelta
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


def aes_encrypt(plaintext: str) -> str:
    """AES加密。

    该方法使用指定的密钥对给定的明文字符串进行AES加密，并返回加密后的密文。

    :param plaintext: 明文字符串。
    :type plaintext: str

    :return: 加密后的密文。
    :rtype: str

    :raises ValueError: 如果加密失败，抛出包含详细错误信息的异常。
    """
    try:
        cipher = AESECBPKCS5Padding("23DbtQHR2UMbH6mJ", "hex")
        ciphertext = cipher.encrypt(plaintext)
        return ciphertext
    except Exception as e:
        logger.error(f"加密失败: {e}")
        raise ValueError(f"加密失败: {str(e)}")


def aes_decrypt(ciphertext: str) -> str:
    """AES解密。

    该方法使用指定的密钥对给定的密文字符串进行AES解密，并返回解密后的明文。

    :param ciphertext: 密文字符串。
    :type ciphertext: str

    :return: 解密后的明文。
    :rtype: str

    :raises ValueError: 如果解密失败，抛出包含详细错误信息的异常。
    """
    try:
        cipher = AESECBPKCS5Padding("23DbtQHR2UMbH6mJ", "hex")
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
