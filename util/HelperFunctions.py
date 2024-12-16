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
