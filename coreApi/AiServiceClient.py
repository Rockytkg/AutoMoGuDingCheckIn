import logging
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException

from util.HelperFunctions import strip_markdown

logger = logging.getLogger(__name__)


def generate_article(
    config: Any,
    title: str,
    job_info: Dict[str, Any],
    count: int = 500,
    max_retries: int = 3,
    retry_delay: int = 1,
    timeout: int = 600,
) -> str:
    """
    生成日报、周报、月报。

    Args:
        config: 配置管理器，负责提供 API 配置。
        title: 文章标题。
        job_info: 工作相关信息字典。
        count: 字数下限，默认500。
        max_retries: 最大重试次数，默认3。
        retry_delay: 每次重试的延迟时间（秒）。
        timeout: 请求超时时间（秒）。
    Returns:
        生成的文章内容字符串。
    Raises:
        ValueError: 超过最大重试、响应异常、内容异常。
    """

    # 获取所有配置，仅调用一次
    api_key = config.get_value("config.ai.apikey")
    api_base_url = config.get_value("config.ai.apiUrl")
    api_model = config.get_value("config.ai.model")

    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    # 使用urljoin防止拼接错误
    api_url = urljoin(api_base_url.rstrip("/") + "/", "v1/chat/completions")

    # 构造系统提示词
    system_prompt = (
        f"根据用户提供的信息撰写一篇文章，内容流畅且符合中文语法规范，"
        f"不得使用 Markdown 语法，字数不少于 {count} 字。"
        f"文章需与职位描述相关，并使用以下模板："
        "\n\n模板：\n实习地点：xxxx\n\n工作内容：\n\nxxxxxx\n\n工作总结：\n\nxxxxxx\n\n"
        "遇到问题：\n\nxxxxxx\n\n自我评价：\n\nxxxxxx"
    )

    # 提取公司信息，保证对象安全
    company_info = job_info.get("practiceCompanyEntity", {}) or {}
    data = {
        "model": api_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"相关资料：报告标题：{title}，"
                    f"工作地点：{job_info.get('jobAddress', '未知')}; "
                    f"公司名：{company_info.get('companyName', '未知')}; "
                    f"岗位职责：{job_info.get('quartersIntroduce', '未提供')}; "
                    f"公司所属行业：{company_info.get('tradeValue', '未提供')}"
                ),
            },
        ],
    }

    def parse_response(resp_json: Dict) -> Optional[str]:
        """
        从接口响应解析content，返回None表示解析失败。
        """
        try:
            choices = resp_json.get("choices")
            if not choices or not isinstance(choices, list):
                return None
            return choices[0].get("message", {}).get("content", "").strip() or None
        except Exception as e:
            logger.exception("解析响应发生异常")
            return None

    # === 主重试流程 ===
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"第 {attempt} 次请求，标题：{title}")
            response = requests.post(
                url=api_url,
                headers=headers,
                json=data,
                timeout=timeout,
            )
            response.raise_for_status()
            content = parse_response(response.json())
            if not content:
                logger.error("AI 返回内容为空或格式不正确")
                raise ValueError("AI 返回内容为空或格式不正确")
            logger.info("文章生成成功")
            return strip_markdown(content)
        except RequestException as e:
            logger.warning(f"网络请求错误 （尝试 {attempt}/{max_retries}）：{e}")
            if attempt == max_retries:
                logger.error(f"达到最大重试次数，最后一次错误: {e}")
                raise ValueError(f"网络异常，生成失败: {e}")
            time.sleep(retry_delay)
        except ValueError as e:
            logger.error(f"内容错误或解析失败：{e}")
            raise
        except Exception as e:
            logger.exception(f"未知异常（第 {attempt} 次）：{e}")
            if attempt == max_retries:
                raise ValueError(f"生成文章失败，未知错误: {e}")
            time.sleep(retry_delay)

    raise ValueError("文章生成失败，所有重试均未成功")