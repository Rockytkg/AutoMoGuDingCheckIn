import requests
import time
import logging
from typing import List


logger = logging.getLogger(__name__)


def build_upload_key(snowFlakeId: str, userId: str) -> str:
    """
    生成唯一的文件上传路径。

    根据传入的雪花ID和用户ID，生成一个唯一的文件上传路径。
    路径格式为：upload/{snowFlakeId}/{当前日期}/report/{userId}_{当前时间戳}.jpg

    Args:
        snowFlakeId (str): 用于标识文件唯一性的雪花ID。
        userId (str): 用于标识文件所有者的用户ID。

    Returns:
        str: 生成的文件上传路径。
    """
    return (
        f"upload/{snowFlakeId}"
        f"/{time.strftime('%Y-%m-%d', time.localtime())}"
        f"/report/{userId}_{int(time.time() * 1000000)}.jpg"
    )


def upload_image(
    url: str,
    headers: dict,
    image_data: bytes,
    token: str,
    key: str,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> str | None:
    """
    上传单张图片并处理错误。

    上传图片到服务器，并返回成功上传的图片标识符。如果上传失败，函数将重试指定的次数，每次重试之间会有指数增长的延迟。

    Args:
        url (str): 上传图片的目标URL。
        headers (dict): 请求头信息。
        image_data (bytes): 要上传的图片数据。
        token (str): 用于身份验证的令牌。
        key (str): 上传图片的唯一标识符。
        max_retries (int): 最大重试次数，默认为3次。
        retry_delay (int): 初始重试延迟时间（秒），默认为5秒。每次重试时，延迟时间会指数增长。

    Returns:
        str: 成功上传的图片标识符（去除前缀 "upload/"）。如果上传失败且达到最大重试次数，则抛出 ValueError 异常。

    Raises:
        ValueError: 如果上传失败且达到最大重试次数，则抛出此异常。
    """
    data = {
        "token": token,
        "key": key,
        "x-qn-meta-fname": f"{int(time.time() * 1000)}.jpg",
    }

    files = {"file": (key, image_data, "application/octet-stream")}

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()  # 如果响应状态不是200，将引发HTTPError异常

            # 解析响应中的 key
            response_data = response.json()
            if "key" in response_data:
                return response_data["key"].replace("upload/", "")
            else:
                logger.warning("上传成功，但响应中没有key字段")
                return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"上传失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                # 指数回退，重试前等待一段时间
                wait_time = retry_delay * (
                    2**attempt
                )  # 每次重试时延长等待时间（指数回退）
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error(f"上传失败，已达到最大重试次数 {max_retries}")
                raise ValueError(f"上传失败，已达到最大重试次数 {max_retries}")


def upload(
    token: str,
    snowFlakeId: str,
    userId: str,
    images: List[bytes],
) -> str:
    """
    上传图片（支持一次性上传多张图片）

    上传图片到服务器，并返回成功上传的图片链接，链接之间用逗号分隔。

    Args:
        token (str): 上传文件的认证令牌。
        snowFlakeId (str): 组织ID，用于标识上传的唯一性。
        userId (str): 用户ID，用于标识上传者。
        images (List[bytes]): 图片的二进制数据列表。

    Returns:
        str: 成功上传的图片链接，用逗号分隔。
    """
    url = "https://up.qiniup.com/"
    headers = {
        "host": "up.qiniup.com",
        "accept-encoding": "gzip",
        "user-agent": "Dart / 2.17(dart:io)",
    }

    successful_keys = []

    for image_data in images:
        key = build_upload_key(snowFlakeId, userId)

        try:
            # 上传图片并获取上传后的 key
            uploaded_key = upload_image(url, headers, image_data, token, key)

            if uploaded_key:
                successful_keys.append(uploaded_key)

        except Exception as e:
            logger.error(f"图片上传失败：{str(e)}")

    return ",".join(successful_keys)
