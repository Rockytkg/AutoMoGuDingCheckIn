import logging
import time
import json
import requests
from util.Tool import create_sign, aes_encrypt, aes_decrypt, get_current_month_info

# 常量
BASE_URL = 'https://api.moguding.net:9000/'
HEADERS = {
    'user-agent': 'Dart/2.17 (dart:io)',
    'content-type': 'application/json; charset=utf-8',
    'accept-encoding': 'gzip',
    'host': 'api.moguding.net:9000'
}

logging.basicConfig(
    format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %I:%M:%S'
)
api_module_log = logging.getLogger('ApiModule')


class ApiClient:
    """
    ApiClient类用于与远程服务器进行交互，包括用户登录、获取实习计划、获取打卡信息、提交打卡等功能。
    该类主要通过POST请求与API进行通信，并支持自动处理Token失效的情况。

    Attributes:
        config_manager (ConfigManager): 用于管理配置的实例。
        max_retries (int): 控制请求失败后重新尝试的次数，默认值为1。
    """

    def __init__(self, config_manager):
        """
        初始化ApiClient实例。

        :param config_manager: 用于管理配置的实例。
        :type config_manager: ConfigManager
        """
        self.config_manager = config_manager
        self.max_retries = 1  # 控制重新尝试的次数

    def _post_request(self, url, headers, data, msg='请求失败', retry_count=0):
        """
        发送POST请求，并处理请求过程中可能发生的错误。
        如果返回的响应码不是200，且错误消息表明Token失效，会自动尝试重新登录并重试请求。

        :param url: 请求的API地址（不包括BASE_URL部分）。
        :type url: str
        :param headers: 请求头信息，包括授权信息。
        :type headers: dict
        :param data: POST请求的数据。
        :type data: dict
        :param msg: 如果请求失败，输出的错误信息前缀，默认为'请求失败'。
        :type msg: str, optional
        :param retry_count: 当前请求的重试次数，默认为0。
        :type retry_count: int, optional

        :return: 如果请求成功，返回响应的JSON数据。
        :rtype: dict

        :raises ValueError: 如果请求失败或响应包含错误信息，则抛出包含详细错误信息的异常。
        """
        try:
            response = requests.post(f'{BASE_URL}{url}', headers=headers, json=data)
            response.raise_for_status()
            rsp = response.json()

            # 如果返回的 code 不是 200，检查是否是 token 失效
            if rsp.get('code') != 200:
                error_msg = rsp.get('msg', '未知错误')
                if 'token失效' in error_msg and retry_count < self.max_retries:
                    api_module_log.info('Token失效，正在重新登录...')
                    self.login()  # 重新登录以更新 token
                    headers['authorization'] = self.config_manager.get_user_info('token')  # 更新 token
                    return self._post_request(url, headers, data, msg, retry_count + 1)  # 递归重试请求
                else:
                    raise ValueError(error_msg)

            return rsp

        except requests.RequestException as e:
            api_module_log.error(f'{msg}: {e}')
            raise ValueError(f'{msg}: {str(e)}')

    def login(self):
        """
        执行用户登录操作，获取新的用户信息并更新配置。

        此方法使用已加密的用户凭据发送登录请求，并在成功后更新用户信息。

        :raises ValueError: 如果登录请求失败，抛出包含详细错误信息的异常。
        """
        url = 'session/user/v5/login'
        data = {
            'phone': aes_encrypt(self.config_manager.get_config('phone')),
            'password': aes_encrypt(self.config_manager.get_config('password')),
            'captcha': None,
            'loginType': 'android',
            'uuid': '',
            'device': 'android',
            'version': '5.14.0',
            't': aes_encrypt(str(int(time.time() * 1000)))
        }
        rsp = self._post_request(url, HEADERS, data, '登陆失败')
        user_info = json.loads(aes_decrypt(rsp.get('data', '')))
        self.config_manager.update_config('userInfo', user_info)

    def fetch_internship_plan(self):
        """
        获取当前用户的实习计划并更新配置中的planInfo。

        该方法会发送请求获取当前用户的实习计划列表，并将结果更新到配置管理器中。

        :raises ValueError: 如果获取实习计划失败，抛出包含详细错误信息的异常。
        """
        url = 'practice/plan/v3/getPlanByStu'
        data = {
            "pageSize": 999999,
            "t": aes_encrypt(str(int(time.time() * 1000)))
        }
        headers = self._get_authenticated_headers(
            sign_data=[
                self.config_manager.get_user_info('userId'),
                self.config_manager.get_user_info('roleKey')
            ]
        )
        rsp = self._post_request(url, headers, data, '获取planID失败')
        plan_info = rsp.get('data', [{}])[0]
        self.config_manager.update_config('planInfo', plan_info)

    def get_checkin_info(self):
        """
        获取用户的打卡信息。

        该方法会发送请求获取当前用户当月的打卡记录。

        :return: 包含用户打卡信息的字典。
        :rtype: dict

        :raises ValueError: 如果获取打卡信息失败，抛出包含详细错误信息的异常。
        """
        url = '/attendence/clock/v2/listSynchro'
        headers = self._get_authenticated_headers()
        data = {
            **get_current_month_info(),
            "t": aes_encrypt(str(int(time.time() * 1000)))
        }
        rsp = self._post_request(url, headers, data, '获取打卡信息失败')
        return rsp.get('data', {})[0]

    def submit_clock_in(self, checkin_info):
        """
        提交打卡信息。

        该方法会根据传入的打卡信息生成打卡请求，并发送至服务器完成打卡操作。

        :param checkin_info: 包含打卡类型及相关信息的字典。
        :type checkin_info: dict

        :raises ValueError: 如果打卡提交失败，抛出包含详细错误信息的异常。
        """
        url = 'attendence/clock/v4/save'
        api_module_log.info(f'打卡类型：{checkin_info.get("type")}')

        data = {
            "distance": None,
            "address": self.config_manager.get_config('address'),
            "content": None,
            "lastAddress": None,
            "lastDetailAddress": checkin_info.get('address'),
            "attendanceId": None,
            "city": self.config_manager.get_config('city'),
            "area": self.config_manager.get_config('area'),
            "country": "中国",
            "createBy": None,
            "createTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "description": None,
            "device": self.config_manager.get_config('device'),
            "images": None,
            "isDeleted": None,
            "isReplace": None,
            "latitude": self.config_manager.get_config('latitude'),
            "longitude": self.config_manager.get_config('longitude'),
            "modifiedBy": None,
            "modifiedTime": None,
            "province": self.config_manager.get_config('province'),
            "schoolId": None,
            "state": "NORMAL",
            "teacherId": None,
            "teacherNumber": None,
            "type": checkin_info.get('type'),
            "stuId": None,
            "planId": self.config_manager.get_plan_info('planId'),
            "attendanceType": None,
            "username": None,
            "attachments": None,
            "userId": self.config_manager.get_user_info('userId'),
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
            "t": aes_encrypt(str(int(time.time() * 1000)))
        }

        headers = self._get_authenticated_headers(
            sign_data=[
                self.config_manager.get_config('device'),
                checkin_info.get('type'),
                self.config_manager.get_plan_info('planId'),
                self.config_manager.get_user_info('userId'),
                self.config_manager.get_config('address')
            ]
        )

        self._post_request(url, headers, data, '打卡失败')

    def _get_authenticated_headers(self, sign_data=None):
        """
        生成带有认证信息的请求头。

        该方法会从配置管理器中获取用户的Token、用户ID及角色Key，并生成包含这些信息的请求头。
        如果提供了sign_data，还会生成并添加签名信息。

        :param sign_data: 用于生成签名的数据列表，默认为None。
        :type sign_data: list, optional

        :return: 包含认证信息和签名的请求头字典。
        :rtype: dict
        """
        headers = {
            **HEADERS,
            'authorization': self.config_manager.get_user_info('token'),
            'userid': self.config_manager.get_user_info('userId'),
            'rolekey': self.config_manager.get_user_info('roleKey'),
        }
        if sign_data:
            headers['sign'] = create_sign(*sign_data)
        return headers
    # TODO [日报、周报、月报相关Api]
