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
    """生成签名

    Args:
        *args: 要生成签名的参数

    Returns:
        str: 生成的MD5签名
    """
    sign_str = ''.join(args) + "3478cbbc33f84bd00d75d7dfa69e0daa"
    return md5(sign_str.encode("utf-8")).hexdigest()


def aes_encrypt(plaintext: str) -> str:
    """AES加密

    Args:
        plaintext (str): 明文字符串

    Returns:
        str: 加密后的密文

    Raises:
        ValueError: 加密失败时抛出异常
    """
    try:
        cipher = AESECBPKCS5Padding("23DbtQHR2UMbH6mJ", "hex")
        ciphertext = cipher.encrypt(plaintext)
        return ciphertext
    except Exception as e:
        logger.error(f"加密失败: {e}")
        raise ValueError(f"加密失败: {e}")


def aes_decrypt(ciphertext: str) -> str:
    """AES解密

    Args:
        ciphertext (str): 密文字符串

    Returns:
        str: 解密后的明文

    Raises:
        ValueError: 解密失败时抛出异常
    """
    try:
        cipher = AESECBPKCS5Padding("23DbtQHR2UMbH6mJ", "hex")
        plaintext = cipher.decrypt(ciphertext)
        return plaintext
    except Exception as e:
        logger.error(f"解密失败: {e}")
        raise ValueError(f"解密失败: {e}")


def get_current_month_info() -> dict:
    """获取当前月份的开始和结束时间

    Returns:
        dict: 包含当前月份开始和结束时间的字典
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
