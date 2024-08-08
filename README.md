# AutoMoGuDingCheckIn

AutoMoGuDingCheckIn 工学云自动打卡，采用新接口，更安全，支持多用户、自定义位置信息、保持登录状态、每日打卡检查、打卡位置浮动、消息推送

## 项目概述

AutoMoGuDingCheckIn 旨在：

- 自动化工学云应用中的签到过程。
- 自动提交月报、周报、日报。
- 适配云函数

## 功能列表

- [x] 自动签到
- [x] 消息推送功能
- [x] 多用户支持
- [x] 打卡位置浮动
- [ ] 自动提交日报
- [ ] 自动提交周报
- [ ] 自动提交月报
- [ ] 打卡备注以及带图打卡
- [ ] 适配云函数

## 使用方法

### 环境

- Python 3.8+
- pip（Python 包管理器）

### 安装

1. 克隆代码库：
    ```bash
    git clone https://github.com/Rockytkg/AutoMoGuDingCheckIn.git
    cd AutoMoGuDingCheckIn
    ```

2. 安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

### 配置

1. 打开user目录，根据下表修改json文件中的配置（每个文件就是一个用户）

| 字段名                        | 数据类型      | 描述                             | 示例                             | 是否必须填写 |
|----------------------------|-----------|--------------------------------|--------------------------------|--------|
| `phone`                    | `string`  | 手机号                            | `"1234567890"`                 | 必须     |
| `password`                 | `string`  | 工学云密码                          | `"your_password"`              | 必须     |
| `address`                  | `string`  | 打卡地点，用于工学云显示（格式参照example.json） | `"四川省 · 成都市 · 高新区 · 在科创十一街附近"` | 必须     |
| `latitude`                 | `string`  | 打卡的纬度，精确到小数点后六位                | `"34.051122"`                  | 必须     |
| `longitude`                | `string`  | 打卡的经度，精确到小数点后六位                | `"-118.241137"`                | 必须     |
| `province`                 | `string`  | 打卡的省份                          | `"四川省"`                        | 必须     |
| `city`                     | `string`  | 打卡的城市                          | `"成都市"`                        | 必须     |
| `area`                     | `string`  | 打卡的县/区                         | `"高新区"`                        | 必须     |
| `device`                   | `string`  | 设备信息（参照example.json）           | `"设备信息"`                       | 必须     |
| `is_submit_daily`          | `boolean` | 是否提交日报                         | `false`                        | 必须     |
| `is_submit_weekly`         | `boolean` | 是否提交周报                         | `false`                        | 必须     |
| `is_submit_month_report`   | `boolean` | 是否提交月报                         | `false`                        | 必须     |
| `submit_weekly_time`       | `string`  | 周报提交时间                         | `"1"`                          | 不必须    |
| `submit_month_report_time` | `string`  | 月报提交时间                         | `"2"`                          | 不必须    |
| `pushType`                 | `string`  | 推送方式                           | `"server"` 或 `"pushplus"`      | 不必须    |
| `pushKey`                  | `string`  | 推送密钥                           | `"your_push_key"`              | 不必须    |

#### 示例 JSON 配置

```json
{
  "config": {
    "phone": "1234567890",
    "password": "your_password",
    "address": "四川省 · 成都市 · 高新区 · 在科创十一街附近",
    "latitude": "34.059922",
    "longitude": "-118.277437",
    "province": "四川省",
    "city": "成都市",
    "area": "高新区",
    "is_submit_daily": false,
    "is_submit_weekly": false,
    "is_submit_month_report": false,
    "submit_weekly_time": 2,
    "submit_month_report_time": 30,
    "pushType": null,
    "pushKey": null,
    "device": "{brand: OnePlus PHP110, systemVersion: 14, Platform: Android, isPhysicalDevice: true, incremental: T.18b885b-be80-be7f}"
  }
}
```

### 运行

```bash
python main.py
```

### 许可证

本项目采用 Apache 2.0 许可。详细信息请参阅 [LICENSE](https://github.com/Rockytkg/AutoMoGuDingCheckIn/blob/main/LICENSE)
文件。

### 联系方式

如有任何疑问或需要支持，请通过提交 [issue](https://github.com/Rockytkg/AutoMoGuDingCheckIn/issues) 与我们联系。

## start

[![Stargazers over time](https://starchart.cc/Rockytkg/AutoMoGuDingCheckIn)](https://starchart.cc/Rockytkg/AutoMoGuDingCheckIn)