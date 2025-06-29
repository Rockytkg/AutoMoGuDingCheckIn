import re
import logging
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)


def get_current_month_info() -> dict:
    """
    获取当前月份的开始和结束时间。

    该方法计算当前月份的开始日期和结束日期，并将它们返回为字典，
    字典中包含这两项的字符串表示。

    Returns:
        包含当前月份开始和结束时间的字典。
    """
    now = datetime.now()
    # 当前月份的第一天
    start_of_month = datetime(now.year, now.month, 1)

    # 下个月的第一天
    if now.month == 12:
        next_month_start = datetime(now.year + 1, 1, 1)
    else:
        next_month_start = datetime(now.year, now.month + 1, 1)

    # 当前月份的最后一天（下个月第一天减一天）
    end_of_month = next_month_start - timedelta(days=1)

    # 格式化为字符串
    start_time_str = start_of_month.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_of_month.strftime("%Y-%m-%d 00:00:00Z")

    return {"startTime": start_time_str, "endTime": end_time_str}


def desensitize_name(name: str) -> str:
    """
    对姓名进行脱敏处理，将中间部分字符替换为星号。

    Args:
        name (str): 待脱敏的姓名。

    Returns:
        str: 脱敏后的姓名。
    """
    name = name.strip()  # 去除前后空格，防止输入有空格影响判断

    n = len(name)
    if n < 3:
        return f"{name[0]}*"
    else:
        return f"{name[0]}{'*' * (n - 2)}{name[-1]}"


def is_holiday(current_datetime: datetime = datetime.now()) -> bool:
    """
    判断当前日期是否为节假日或周末。

    Args:
        current_datetime (datetime): 当前日期时间，默认为系统当前时间。

    Returns:
        bool: 是否为节假日。
    """
    # 获取当前年份和日期字符串
    year = current_datetime.year
    current_date = current_datetime.strftime("%Y-%m-%d")

    # 从远程获取节假日数据
    response = requests.get(
        f"https://gh-proxy.com/https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json",
        timeout=10,  # 设置超时时间，防止请求挂起
    )

    holiday_list = response.json().get("days", [])

    # 遍历节假日数据，检查当前日期是否为节假日
    for holiday in holiday_list:
        if holiday.get("date") == current_date:
            is_off_day = holiday.get("isOffDay", False)
            return is_off_day

    # 如果不是节假日，检查是否为周末
    is_weekend = current_datetime.weekday() > 4  # 周末为星期六（5）和星期日（6）
    return is_weekend


def strip_markdown(text):
    """
    过滤Markdown标记，保留文本内容和换行符

    Args:
        text (str): 包含Markdown标记的原始文本

    Returns:
        str: 过滤后的纯文本
    """
    # 1. 移除注释
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # 2. 移除代码块 (保留代码内容)
    text = re.sub(r"```[a-zA-Z0-9]*\n([\s\S]*?)\n```", r"\1", text)

    # 3. 移除行内代码标记
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # 4. 移除图片标记 (保留alt文本)
    text = re.sub(r"!\[(.*?)\]\(.*?\)", r"\1", text)

    # 5. 移除超链接标记 (保留链接文本)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)

    # 6. 移除脚注引用 例如 [^1]
    text = re.sub(r"\[\^([^\]]+)\]", "", text)

    # 7. 移除脚注定义 例如 [^1]: some text
    text = re.sub(r"^\[\^.+?\]:.*$", "", text, flags=re.MULTILINE)

    # 8. 移除表格分隔（仅去除 | 和 ---、不动表格实际内容）
    text = re.sub(
        r"^\s*\|?(?:\s*[:-]+\s*\|)+\s*[:-]+\s*\|?\s*$", "", text, flags=re.MULTILINE
    )
    text = re.sub(r"\|", " ", text)  # 用空格替掉行内|

    # 9. 移除水平分割线
    text = re.sub(r"^\s*([-*_])[ \1]{2,}\s*$", "", text, flags=re.MULTILINE)

    # 10. 移除删除线
    text = re.sub(r"~~(.*?)~~", r"\1", text)

    # 11. 移除粗体和斜体标记
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"\1", text)  # ***bold italic***
    text = re.sub(r"___(.*?)___", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold**
    text = re.sub(r"__(.*?)__", r"\1", text)  # __bold__
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # *italic*
    text = re.sub(r"_(.*?)_", r"\1", text)  # _italic_

    # 12. 移除标题标记 (保留标题文本)
    text = re.sub(r"^#{1,6}\s+(.*)$", r"\1", text, flags=re.MULTILINE)

    # 13. 移除列表标记
    text = re.sub(
        r"^(\s*)[-*+]\s+\[.\]\s+", r"\1", text, flags=re.MULTILINE
    )  # 任务列表勾选框
    text = re.sub(r"^(\s*)[-*+]\s+", r"\1", text, flags=re.MULTILINE)
    text = re.sub(r"^(\s*)\d+\.\s+", r"\1", text, flags=re.MULTILINE)

    # 14. 移除引用标记
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

    # 15. 移除行内HTML标签
    text = re.sub(r"</?[^>]+>", "", text)

    # 16. 多空白行合并
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()

    return text
