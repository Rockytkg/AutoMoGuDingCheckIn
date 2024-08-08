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


# TODO: [完善注释]
class ApiClient:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.max_retries = 1  # 控制重新尝试的次数

    def _post_request(self, url, headers, data, msg='请求失败', retry_count=0):
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
        user_info = json.loads(aes_decrypt(rsp.get('data', {})))
        self.config_manager.update_config('userInfo', user_info)

    def fetch_internship_plan(self):
        url = 'practice/plan/v3/getPlanByStu'
        data = {
            "pageSize": 999999,
            "t": aes_encrypt(str(int(time.time() * 1000)))
        }
        headers = self._get_authenticated_headers()
        rsp = self._post_request(url, headers, data, '获取planID失败')
        plan_info = rsp.get('data', [{}])[0]
        self.config_manager.update_config('planInfo', plan_info)

    def get_checkin_info(self):
        url = '/attendence/clock/v2/listSynchro'
        headers = self._get_authenticated_headers()
        data = {
            **get_current_month_info(),
            "t": aes_encrypt(str(int(time.time() * 1000)))
        }
        rsp = self._post_request(url, headers, data, '获取打卡信息失败')
        return rsp.get('data', {})[0]

    # TODO: [打卡备注、图片]
    def submit_clock_in(self, checkin_info):
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
        headers = {
            **HEADERS,
            'authorization': self.config_manager.get_user_info('token'),
            'userid': self.config_manager.get_user_info('userId'),
            'rolekey': self.config_manager.get_user_info('roleKey'),
        }
        if sign_data:
            headers['sign'] = create_sign(*sign_data)
        return headers

    # TODO: [日报、周报、月报相关Api]
