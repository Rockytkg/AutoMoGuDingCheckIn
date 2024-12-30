import json
import logging
import re
import time
import uuid
import random
from typing import Dict, Any, List, Optional

import requests

from util.Config import ConfigManager
from util.CryptoUtils import create_sign, aes_encrypt, aes_decrypt
from util.CaptchaUtils import recognize_captcha
from util.HelperFunctions import get_current_month_info

# 常量
BASE_URL = "https://api.moguding.net:9000/"
HEADERS = {
    "user-agent": "Dart/2.17 (dart:io)",
    "content-type": "application/json; charset=utf-8",
    "accept-encoding": "gzip",
    "host": "api.moguding.net:9000",
}

logger = logging.getLogger(__name__)


class ApiClient:
    """
    ApiClient类用于与远程服务器进行交互，包括用户登录、获取实习计划、获取打卡信息、提交打卡等功能。
    该类主要通过POST请求与API进行通信，并支持自动处理Token失效的情况。

    Attributes:
        config (ConfigManager): 用于管理配置的实例。
        max_retries (int): 控制请求失败后重新尝试的次数，默认值为1。
    """

    def __init__(self, config: ConfigManager):
        """
        初始化ApiClient实例。

        Args:
            config (ConfigManager): 用于管理配置的实例。
        """
        self.config = config
        self.max_retries = 5  # 控制重新尝试的次数

    def _post_request(
        self,
        url: str,
        headers: Dict[str, str],
        data: Dict[str, Any],
        msg: str = "请求失败",
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        发送POST请求，并处理请求过程中可能发生的错误。
        包括自动重试机制和Token失效处理。

        Args:
            url (str): 请求的API地址（不包括BASE_URL部分）。
            headers (Dict[str, str]): 请求头信息，包括授权信息。
            data (Dict[str, Any]): POST请求的数据。
            msg (str, optional): 如果请求失败，输出的错误信息前缀，默认为'请求失败'。
            retry_count (int, optional): 当前请求的重试次数，默认为0。

        Returns:
            Dict[str, Any]: 如果请求成功，返回响应的JSON数据。

        Raises:
            ValueError: 如果请求失败或响应包含错误信息，则抛出包含详细错误信息的异常。
        """
        try:
            response = requests.post(
                f"{BASE_URL}{url}", headers=headers, json=data, timeout=10
            )
            response.raise_for_status()
            rsp = response.json()

            if rsp.get("code") == 200 or rsp.get("code") == 6111:
                return rsp

            if (
                "token失效" in rsp.get("msg", "未知错误")
                and retry_count < self.max_retries
            ):
                wait_time = 1 * (2**retry_count)
                time.sleep(wait_time)
                logger.warning("Token失效，正在重新登录...")
                self.login()
                headers["authorization"] = self.config.get_value("userInfo.token")
                return self._post_request(url, headers, data, msg, retry_count + 1)
            else:
                raise ValueError(rsp.get("msg", "未知错误"))

        except (requests.RequestException, ValueError) as e:
            if re.search(r"[\u4e00-\u9fff]", str(e)) or retry_count >= self.max_retries:
                raise ValueError(f"{msg}，{str(e)}")

            wait_time = 1 * (2**retry_count)
            logger.warning(
                f"{msg}: 重试 {retry_count + 1}/{self.max_retries}，等待 {wait_time:.2f} 秒"
            )
            time.sleep(wait_time)

        return self._post_request(url, headers, data, msg, retry_count + 1)

    def pass_captcha(self, max_attempts: Optional[int] = 5) -> str:
        """
        通过行为验证码（验证码类型为blockPuzzle）。

        Args:
            max_attempts (Optional[int]): 最大尝试次数，默认为5次。

        Returns:
            str: 验证参数。

        Raises:
            Exception: 当达到最大尝试次数时抛出异常。
        """
        attempts = 0
        while attempts < max_attempts:
            time.sleep(random.uniform(0.5, 0.7))
            captcha_url = "session/captcha/v1/get"
            request_data = {
                "clientUid": str(uuid.uuid4()).replace("-", ""),
                "captchaType": "blockPuzzle",
            }
            captcha_info = self._post_request(
                captcha_url, HEADERS, request_data, "获取验证码失败"
            )
            slider_data = recognize_captcha(
                captcha_info["data"]["jigsawImageBase64"],
                captcha_info["data"]["originalImageBase64"],
            )
            check_slider_url = "session/captcha/v1/check"
            check_slider_data = {
                "pointJson": aes_encrypt(
                    slider_data, captcha_info["data"]["secretKey"], "b64"
                ),
                "token": captcha_info["data"]["token"],
                "captchaType": "blockPuzzle",
            }
            check_result = self._post_request(
                check_slider_url, HEADERS, check_slider_data, "验证验证码失败"
            )
            if check_result.get("code") != 6111:
                return aes_encrypt(
                    captcha_info["data"]["token"] + "---" + slider_data,
                    captcha_info["data"]["secretKey"],
                    "b64",
                )
            attempts += 1
        raise Exception("验证码验证失败超过最大尝试次数")

    def login(self) -> None:
        """
        执行用户登录操作，获取新的用户信息并更新配置。

        此方法使用已加密的用户凭据发送登录请求，并在成功后更新用户信息。

        Raises:
            ValueError: 如果登录请求失败，抛出包含详细错误信息的异常。
        """
        url = "session/user/v6/login"
        data = {
            "phone": aes_encrypt(self.config.get_value("config.user.phone")),
            "password": aes_encrypt(self.config.get_value("config.user.password")),
            "captcha": self.pass_captcha(),
            "loginType": "android",
            "uuid": str(uuid.uuid4()).replace("-", ""),
            "device": "android",
            "version": "5.16.0",
            "t": aes_encrypt(str(int(time.time() * 1000))),
        }
        rsp = self._post_request(url, HEADERS, data, "登陆失败")
        user_info = json.loads(aes_decrypt(rsp.get("data", "")))
        self.config.update_config(user_info, "userInfo")

    def fetch_internship_plan(self) -> None:
        """
        获取当前用户的实习计划并更新配置中的planInfo。

        该方法会发送请求获取当前用户的实习计划列表，并将结果更新到配置管理器中。

        Raises:
            ValueError: 如果获取实习计划失败，抛出包含详细错误信息的异常。
        """
        url = "practice/plan/v3/getPlanByStu"
        data = {"pageSize": 999999, "t": aes_encrypt(str(int(time.time() * 1000)))}
        headers = self._get_authenticated_headers(
            sign_data=[
                self.config.get_value("userInfo.userId"),
                self.config.get_value("userInfo.roleKey"),
            ]
        )
        rsp = self._post_request(url, headers, data, "获取planID失败")
        plan_info = rsp.get("data", [{}])[0]
        self.config.update_config(plan_info, "planInfo")

    def get_job_info(self) -> Dict[str, Any]:
        """
        获取用户的工作ID。

        该方法会发送请求获取当前用户的岗位ID。

        Returns:
            用户的工作ID。

        Raises:
            ValueError: 如果获取岗位信息失败，抛出包含详细错误信息的异常。
        """
        url = "practice/job/v4/infoByStu"
        data = {
            "planId": self.config.get_value("planInfo.planId"),
            "t": aes_encrypt(str(int(time.time() * 1000))),
        }
        headers = self._get_authenticated_headers()
        rsp = self._post_request(url, headers, data, "获取岗位信息失败")
        data = rsp.get("data", {})
        return {} if data is None else data

    def get_submitted_reports_info(self, report_type: str) -> Dict[str, Any]:
        """
        获取已经提交的日报、周报或月报的数量。

        Args:
            report_type (str): 报告类型，可选值为 "day"（日报）、"week"（周报）或 "month"（月报）。

        Returns:
            Dict[str, Any]: 已经提交的报告数量。

        Raises:
            ValueError: 如果获取数量失败，抛出包含详细错误信息的异常。
        """
        url = "practice/paper/v2/listByStu"
        data = {
            "currPage": 1,
            "pageSize": 10,
            "reportType": report_type,
            "planId": self.config.get_value("planInfo.planId"),
            "t": aes_encrypt(str(int(time.time() * 1000))),
        }
        headers = self._get_authenticated_headers(
            sign_data=[
                self.config.get_value("userInfo.userId"),
                self.config.get_value("userInfo.roleKey"),
                report_type,
            ]
        )
        rsp = self._post_request(url, headers, data, "获取报告列表失败")
        return rsp

    def submit_report(self, report_info: Dict[str, Any]) -> None:
        """
        提交报告。

        Args:
            report_info (Dict[str, Any]): 报告信息。

        Returns:
            None: 无返回值。

        Raises:
            ValueError: 如果提交报告失败，抛出包含详细错误信息的异常。
        """
        url = "practice/paper/v6/save"
        headers = self._get_authenticated_headers(
            sign_data=[
                self.config.get_value("userInfo.userId"),
                report_info.get("reportType"),
                self.config.get_value("planInfo.planId"),
                report_info.get("title"),
            ]
        )
        data = {
            "address": None,
            "applyId": None,
            "applyName": None,
            "attachmentList": None,
            "commentNum": None,
            "commentContent": None,
            "content": report_info.get("content"),
            "createBy": None,
            "createTime": None,
            "depName": None,
            "reject": None,
            "endTime": report_info.get("endTime", None),
            "headImg": None,
            "yearmonth": report_info.get("yearmonth", None),
            "imageList": None,
            "isFine": None,
            "latitude": None,
            "gpmsSchoolYear": None,
            "longitude": None,
            "planId": self.config.get_value("planInfo.planId"),
            "planName": None,
            "reportId": None,
            "reportType": report_info.get("reportType"),
            "reportTime": report_info.get("reportTime", None),
            "isOnTime": None,
            "schoolId": None,
            "startTime": report_info.get("startTime", None),
            "state": None,
            "studentId": None,
            "studentNumber": None,
            "supportNum": None,
            "title": report_info.get("title"),
            "url": None,
            "username": None,
            "weeks": report_info.get("weeks", None),
            "videoUrl": None,
            "videoTitle": None,
            "attachments": report_info.get("attachments", ""),
            "companyName": None,
            "jobName": None,
            "jobId": report_info.get("jobId", ""),
            "score": None,
            "tpJobId": None,
            "starNum": None,
            "confirmDays": None,
            "isApply": None,
            "compStarNum": None,
            "compScore": None,
            "compComment": None,
            "compState": None,
            "apply": None,
            "levelEntity": None,
            "formFieldDtoList": report_info.get("formFieldDtoList", []),
            "fieldEntityList": [],
            "feedback": None,
            "handleWay": None,
            "isWarning": 0,
            "warningType": None,
            "t": aes_encrypt(str(int(time.time() * 1000))),
        }
        self._post_request(url, headers, data, report_info.get("msg"))

    def get_weeks_date(self) -> list[Dict[str, Any]]:
        """
        获取本周周报周期信息。

        Returns:
            list[Dict[str, Any]]: 包含周报周期信息的字典列表。
        """
        url = "practice/paper/v3/getWeeks1"
        data = {"t": aes_encrypt(str(int(time.time() * 1000)))}
        headers = self._get_authenticated_headers()
        rsp = self._post_request(url, headers, data, "获取周报周期失败")
        return rsp.get("data", [])

    def get_from_info(self, formType: int) -> list[Dict[str, Any]]:
        """
        获取子表单（问卷），并设置值
        Args:
            formType (int): 表单类型。日报：7，周报：8，月报：9
        Returns:
            list[Dict[str, Any]]: 问卷
        """
        url = "practice/paper/v2/info"
        data = {"formType": formType, "t": aes_encrypt(str(int(time.time() * 1000)))}
        headers = self._get_authenticated_headers()
        rsp = self._post_request(url, headers, data, "获取问卷失败").get("data", {})
        formFieldDtoList = rsp.get("formFieldDtoList", [])
        # 没有问卷就直接返回
        if not formFieldDtoList:
            return formFieldDtoList
        logger.info("检测到问卷，已自动填写")
        # 有问卷就自动填写
        for item in formFieldDtoList:
            # 默认暂时就先选个 b 吧
            item["value"] = "b"

        return formFieldDtoList

    def get_checkin_info(self) -> Dict[str, Any]:
        """
        获取用户的打卡信息。

        该方法会发送请求获取当前用户当月的打卡记录。

        Returns:
            包含用户打卡信息的字典。

        Raises:
            ValueError: 如果获取打卡信息失败，抛出包含详细错误信息的异常。
        """
        url = "attendence/clock/v2/listSynchro"
        headers = self._get_authenticated_headers()
        data = {
            **get_current_month_info(),
            "t": aes_encrypt(str(int(time.time() * 1000))),
        }
        rsp = self._post_request(url, headers, data, "获取打卡信息失败")
        # 每月第一天的第一次打卡返回的是空，所以特殊处理返回空字典
        return rsp.get("data", [{}])[0] if rsp.get("data") else {}

    def submit_clock_in(self, checkin_info: Dict[str, Any]) -> None:
        """
        提交打卡信息。

        该方法会根据传入的打卡信息生成打卡请求，并发送至服务器完成打卡操作。

        Args:
            checkin_info (Dict[str, Any]): 包含打卡类型及相关信息的字典。

        Raises:
            ValueError: 如果打卡提交失败，抛出包含详细错误信息的异常。
        """
        url = "attendence/clock/v5/save"
        logger.info(f'打卡类型：{checkin_info.get("type")}')

        data = {
            "distance": None,
            "content": None,
            "lastAddress": None,
            "lastDetailAddress": checkin_info.get("lastDetailAddress"),
            "attendanceId": None,
            "country": "中国",
            "createBy": None,
            "createTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "description": checkin_info.get("description", None),
            "device": self.config.get_value("config.device"),
            "images": None,
            "isDeleted": None,
            "isReplace": None,
            "modifiedBy": None,
            "modifiedTime": None,
            "schoolId": None,
            "state": "NORMAL",
            "teacherId": None,
            "teacherNumber": None,
            "type": checkin_info.get("type"),
            "stuId": None,
            "planId": self.config.get_value("planInfo.planId"),
            "attendanceType": None,
            "username": None,
            "attachments": checkin_info.get("attachments", None),
            "userId": self.config.get_value("userInfo.userId"),
            "isSYN": None,
            "studentId": None,
            "applyState": None,
            "studentNumber": None,
            "memberNumber": None,
            "headImg": None,
            "attendenceTime": None,
            "depName": None,
            "majorName": None,
            "className": None,
            "logDtoList": None,
            "isBeyondFence": None,
            "practiceAddress": None,
            "tpJobId": None,
            "t": aes_encrypt(str(int(time.time() * 1000))),
        }

        data.update(self.config.get_value("config.clockIn.location"))

        headers = self._get_authenticated_headers(
            sign_data=[
                self.config.get_value("config.device"),
                checkin_info.get("type"),
                self.config.get_value("planInfo.planId"),
                self.config.get_value("userInfo.userId"),
                self.config.get_value("config.clockIn.location.address"),
            ]
        )

        self._post_request(url, headers, data, "打卡失败")

    def get_upload_token(self) -> str:
        """
        获取上传文件的认证令牌。

        该方法会发送请求获取上传文件的认证令牌。

        Returns:
            上传文件的认证令牌。
        """
        url = "session/upload/v1/token"
        headers = self._get_authenticated_headers()
        data = {"t": aes_encrypt(str(int(time.time() * 1000)))}
        rsp = self._post_request(url, headers, data, "获取上传文件的认证令牌失败")
        return rsp.get("data", "")

    def _get_authenticated_headers(
        self, sign_data: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        生成带有认证信息的请求头。

        该方法会从配置管理器中获取用户的Token、用户ID及角色Key，并生成包含这些信息的请求头。
        如果提供了sign_data，还会生成并添加签名信息。

        Args:
            sign_data (Optional[List[str]]): 用于生成签名的数据列表，默认为None。

        Returns:
            包含认证信息和签名的请求头字典。
        """
        headers = {
            **HEADERS,
            "authorization": self.config.get_value("userInfo.token"),
            "userid": self.config.get_value("userInfo.userId"),
            "rolekey": self.config.get_value("userInfo.roleKey"),
        }
        if sign_data:
            headers["sign"] = create_sign(*sign_data)
        return headers
