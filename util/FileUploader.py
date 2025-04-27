import os
import io
import random

from PIL import Image

from coreApi.FileUploadApi import upload


def process_image(image_path: str) -> bytes:
    """
    读取并处理图片，确保格式为JPEG，且大小不超过1MB。
    通过动态调整JPEG压缩质量来控制文件大小。

    Args:
        image_path (str): 图片路径。

    Returns:
        bytes: 处理后的图片二进制数据。
    """
    # 打开原始图片
    with Image.open(image_path) as img:
        # 如果图片格式不是JPEG，则转换为RGB模式
        if (img.format is None) or (str(img.format).upper() != "JPEG"):
            img = img.convert("RGB")

        # 定义文件大小上限（1MB）
        max_size = 1 * 1024 * 1024

        # 初始化质量参数
        quality = 85
        min_quality = 5
        max_quality = 95

        # 使用二分查找方法优化质量压缩
        while max_quality - min_quality > 5:
            # 将图片保存到内存缓冲区
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="JPEG", quality=quality)

            # 获取当前图片大小
            current_size = img_byte_arr.tell()

            # 根据当前大小调整压缩质量
            if current_size > max_size:
                # 如果太大，降低质量
                max_quality = quality
                quality = (min_quality + quality) // 2
            elif current_size < max_size:
                # 如果太小，可以尝试提高质量
                min_quality = quality
                quality = (max_quality + quality) // 2
            else:
                # 恰好等于目标大小，退出循环
                break

        # 最终保存并返回图片数据
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG", quality=quality)

        return img_byte_arr.getvalue()


def upload_img(token: str, snowFlakeId: str, userId: str, count: int) -> str:
    """上传指定数量的处理后图片

    Args:
        token (str): 上传令牌。
        snowFlakeId (str): 组织ID。
        userId (str): 用户ID。
        count (int): 需要上传的图片数量。

    Returns:
        str: 上传成功的图片链接。
    """
    if count < 1:
        return ""

    # 获取图片文件夹路径
    images_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images"
    )

    # 获取所有符合条件的图片文件路径
    all_images = [
        os.path.join(images_dir, f)
        for f in os.listdir(images_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    # 如果图片数量不够，直接返回空
    if len(all_images) < count:
        return ""

    # 随机选择指定数量的图片
    selected_images = random.sample(all_images, count)

    # 处理选中的图片并上传
    processed_images = [process_image(img) for img in selected_images]

    return upload(token, snowFlakeId, userId, processed_images)
