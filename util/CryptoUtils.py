import logging
from hashlib import md5

from aes_pkcs5.algorithms.aes_ecb_pkcs5_padding import AESECBPKCS5Padding

# 配置日志
logger = logging.getLogger(__name__)


def create_sign(*args) -> str:
    """
    生成MD5签名。

    该方法接收任意数量的字符串参数，将它们连接成一个长字符串，随后附加一个预定义的盐值。

    Args:
        *args (str): 用于生成签名的任意数量的字符串参数。

    Returns:
        str: 生成的MD5签名，作为十六进制字符串返回。

    Raises:
        ValueError: 如果在签名生成过程中发生错误，将抛出此异常。
    """
    try:
        # 将所有输入参数连接成一个长字符串，并在末尾添加盐值
        sign_str = "".join(args) + "3478cbbc33f84bd00d75d7dfa69e0daa"
        # 使用MD5对最终字符串进行加密，并返回加密后的十六进制签名
        return md5(sign_str.encode("utf-8")).hexdigest()

    except Exception as e:
        logger.error(f"签名生成失败: {e}")
        raise ValueError(f"签名生成失败: {str(e)}")


def aes_encrypt(
    plaintext: str, key: str = "23DbtQHR2UMbH6mJ", out_format: str = "hex"
) -> str:
    """
    AES加密。

    该方法使用指定的密钥对给定的明文字符串进行AES加密，并返回加密后的密文。

    Args:
        plaintext (str): 明文字符串。
        key (str, optional): AES密钥，默认 "23DbtQHR2UMbH6mJ"。
        out_format (str, optional): 输出格式，默认 "hex"。

    Returns:
        str: 加密后的密文。

    Raises:
        ValueError: 如果加密失败，抛出包含详细错误信息的异常。
    """
    try:
        # 使用指定的密钥和输出格式初始化AES加密器
        cipher = AESECBPKCS5Padding(key, out_format)
        # 对明文进行AES加密
        ciphertext = cipher.encrypt(plaintext)
        return ciphertext

    except Exception as e:
        logger.error(f"加密失败: {e}")
        raise ValueError(f"加密失败: {str(e)}")


def aes_decrypt(
    ciphertext: str, key: str = "23DbtQHR2UMbH6mJ", out_format: str = "hex"
) -> str:
    """
    AES解密。

    该方法使用指定的密钥对给定的密文字符串进行AES解密，并返回解密后的明文。

    Args:
        ciphertext (str): 密文字符串。
        key (str, optional): AES密钥，默认 "23DbtQHR2UMbH6mJ"。
        out_format (str, optional): 输出格式，默认 "hex"。

    Returns:
        str: 解密后的明文。

    Raises:
        ValueError: 如果解密失败，抛出包含详细错误信息的异常。
    """
    try:
        # 使用指定的密钥和输出格式初始化AES解密器
        cipher = AESECBPKCS5Padding(key, out_format)
        # 对密文进行AES解密
        plaintext = cipher.decrypt(ciphertext)
        return plaintext

    except Exception as e:
        logger.error(f"解密失败: {e}")
        raise ValueError(f"解密失败: {str(e)}")
