import base64
import json
import logging
import random
import struct
from io import BytesIO

from PIL import Image
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
    # 初始化 ddddocr 的滑块检测对象，禁用广告显示
    det = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)

    # 调用 ddddocr 的 slide_match 方法进行滑块匹配
    x1, _, x2, _ = det.slide_match(target_bytes, background_bytes).get("target")

    # 返回结果
    return [x1, x2]


def recognize_blockPuzzle_captcha(target: str, background: str) -> str:
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


def recognize_clickWord_captcha(target: str, wordlist: list) -> str:
    """
    从给定的图像中识别点击文字验证码，并返回单词的坐标。

    此函数初始化ddddocr检测器和识别器，以检测和识别验证码中的单词。然后，它使用识别到的单词为给定单词列表中的单词生成随机坐标。

    Args:
        target (str): base64编码的图像字符串。
        wordlist (list): 要识别的单词列表。

    Returns:
        str: 单词列表中的单词的坐标的JSON字符串列表。

    引发：
        logger.warning: 在处理文本框时出错或未找到字符时。
    """
    target_bytes = base64.b64decode(target)

    # 初始化ddddocr的检测器和识别器
    det = ddddocr.DdddOcr(det=True, show_ad=False)
    ocr = ddddocr.DdddOcr(
        det=False,
        ocr=False,
        import_onnx_path="./models/01.onnx",
        charsets_path="./models/charsets.json",
        show_ad=False,
    )

    bboxes = det.detection(target_bytes)
    image = Image.open(BytesIO(target_bytes))

    # 识别每个文本框中的文本，并存储为字典以便快速查找
    recognized_dict = {}
    for bbox in bboxes:
        try:
            with BytesIO() as cropped_buffer:
                image.crop(bbox).save(cropped_buffer, format="JPEG")
                cropped_binary = cropped_buffer.getvalue()
                text = ocr.classification(cropped_binary)
                recognized_dict[text] = bbox
        except Exception as e:
            logger.warning(f"处理文本框时出错: {e}")

    # 根据wordlist的顺序找到对应的文本框，并生成随机坐标
    random_coordinates = []
    for word in wordlist:
        bbox = recognized_dict.get(word)
        if bbox:
            # 生成随机坐标
            x = random.randint(bbox[0], bbox[2])
            y = random.randint(bbox[1], bbox[3])
            random_coordinates.append({"x": x, "y": y})
        else:
            logger.warning(f"未找到字符: {word}")
            # 可以选择跳过或添加占位符
            # random_coordinates.append("0,0")
    return json.dumps(random_coordinates, separators=(",", ":"))
