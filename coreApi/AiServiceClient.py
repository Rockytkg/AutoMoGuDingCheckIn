import logging
import time
from typing import Dict, Any

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def generate_article(
    config: Any,
    title: str,
    job_info: Dict[str, Any],
    count: int = 500,
    max_retries: int = 3,
    retry_delay: int = 1,
) -> str:
    """
    生成日报、周报、月报。

    Args:
        config (Any): 配置管理器，负责提供所需的 API 配置信息。
        title (str): 文章标题。
        job_info (Dict[str, Any]): 包含工作相关信息的字典。
        count (int): 文章字数下限，默认为 500。
        max_retries (int): 最大重试次数，默认为 3。
        retry_delay (int): 每次重试的延迟时间（秒），默认为 1。

    Returns:
        str: 返回生成的文章内容。

    Raises:
        ValueError: 如果达到最大重试次数或发生解析错误时。
    """
    # 准备请求头和 API URL
    headers = {
        "Authorization": f"Bearer {config.get_value('config.ai.apikey')}",
    }
    api_url = config.get_value("config.ai.apiUrl").rstrip("/") + "/v1/chat/completions"

    # 动态生成系统提示词，支持更灵活的扩展
    system_prompt = (
        f"根据用户提供的信息撰写一篇文章，内容流畅且符合中文语法规范，"
        f"不得使用 Markdown 语法，字数不少于 {count} 字。"
        f"文章需与职位描述相关，并符合以下模板："
        f"\n\n模板：\n实习地点：xxxx\n\n工作内容：\n\nxxxxxx\n\n工作总结：\n\nxxxxxx\n\n"
        f"遇到问题：\n\nxxxxxx\n\n自我评价：\n\nxxxxxx"
    )

    # 准备请求载荷
    data = {
        "model": config.get_value("config.ai.model"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"相关资料：报告标题：{title}，工作地点：{job_info.get('jobAddress', '未知')}; "
                    f"公司名：{job_info.get('practiceCompanyEntity', {}).get('companyName', '未知')}; "
                    f"岗位职责：{job_info.get('quartersIntroduce', '未提供')}; "
                    f"公司所属行业：{job_info.get('practiceCompanyEntity', {}).get('tradeValue', '未提供')}"
                ),
            },
        ],
    }

    # 重试逻辑
    for attempt in range(max_retries):
        try:
            logger.info(f"第 {attempt + 1} 次尝试生成文章")
            response = requests.post(
                url=api_url, headers=headers, json=data, timeout=30
            )
            response.raise_for_status()

            # 解析响应内容
            content = (
                response.json()
                .get("choices", [])[0]
                .get("message", {})
                .get("content", "")
            )
            if not content.strip():
                raise ValueError("AI 返回的内容为空或格式不正确")

            logger.info("文章生成成功")
            return content
        except RequestException as e:
            logger.warning(f"网络请求错误（第 {attempt + 1} 次尝试）: {e}")
            if attempt == max_retries - 1:
                logger.error(f"达到最大重试次数。最后一次错误: {e}")
                raise ValueError(f"生成文章失败，达到最大重试次数: {e}")
            time.sleep(retry_delay)
        except (KeyError, IndexError) as e:
            logger.error(f"解析响应时发生错误: {e}")
            raise ValueError(f"解析响应时发生错误: {e}")
        except Exception as e:
            logger.error(f"未知错误（第 {attempt + 1} 次尝试）: {e}")
            raise ValueError(f"生成文章失败，未知错误: {e}")

    # 若所有尝试均失败，返回提示
    raise ValueError("文章生成失败，所有重试均未成功")
