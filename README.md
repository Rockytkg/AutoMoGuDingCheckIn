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
- [x] 自动提交日报
- [x] 自动提交周报
- [x] 自动提交月报
- [x] AI生成周、日、月报
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

| 字段名                        | 描述                                                                   | 示例                                                                                                                         |
|----------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| `phone`                    | 手机号                                                                  | `"1234567890"`                                                                                                             |
| `password`                 | 工学云密码                                                                | `"your_password"`                                                                                                          |
| `address`                  | 打卡地点，用于工学云显示（格式参照example.json）                                       | `"四川省 · 成都市 · 高新区 · 在科创十一街附近"`                                                                                             |
| `latitude`                 | 打卡的纬度，精确到小数点后六位                                                      | `"34.059922"`                                                                                                              |
| `longitude`                | 打卡的经度，精确到小数点后六位                                                      | `"-118.277437"`                                                                                                            |
| `province`                 | 打卡的省份                                                                | `"四川省"`                                                                                                                    |
| `city`                     | 打卡的城市                                                                | `"成都市"`                                                                                                                    |
| `area`                     | 打卡的县/区                                                               | `"高新区"`                                                                                                                    |
| `device`                   | 设备信息（[用这个小工具获取](https://www.123pan.com/s/rlqcVv-bQOPH.html)          | `"{brand: OnePlus PHP310, systemVersion: 13, Platform: Android, isPhysicalDevice: true, incremental: T.18b78b-be23-ce7d}"` |
| `clockInImageCount`        | 打卡时候需要提交图片的数量，默认0                                                    | `0`                                                                                                                        |
| `isSubmittedDaily`         | 是否提交日报                                                               | `false`                                                                                                                    |
| `dailyReportImageCount`    | 日报提交图片数量（默认不提交，不为0会从img目录随机抽取）                                       | `0`                                                                                                                        |
| `isSubmittedWeekly`        | 是否提交周报                                                               | `true`                                                                                                                     |
| `weeklyReportImageCount`   | 周报提交图片数量（默认不提交，不为0会从img目录随机抽取）                                       | `0`                                                                                                                        |
| `isSubmittedMonthlyReport` | 是否提交月报                                                               | `false`                                                                                                                    |
| `monthlyReportImageCount`  | 月报提交图片数量（默认不提交，不为0会从img目录随机抽取）                                       | `0`                                                                                                                        |
| `submitWeeklyTime`         | 周报提交时间                                                               | `"4"`                                                                                                                      |
| `submitMonthlyReportTime`  | 月报提交时间                                                               | `"29"`                                                                                                                     |
| `model`                    | OpenAI模型名称（提交周、日、月报需要填写）                                             | `"gpt-4o-mini"`                                                                                                            |
| `apikey`                   | OpenAI API密钥                                                         | `"sk-osdhgosdipghpsdgjiosfvinoips"`                                                                                        |
| `apiUrl`                   | OpenAI API URL（推荐[KKSJ API](https://api.kksj.org/register?aff=1kzT)） | `"https://api.openai.com/"`                                                                                                |
| `pushType`                 | 推送方式                                                                 | `server`、`pushplus`、`anpush`                                                                                               |
| `pushKey`                  | 推送密钥                                                                 | `null`                                                                                                                     |

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
    "clockInImageCount": 0,
    "isSubmittedDaily": false,
    "dailyReportImageCount": 0,
    "isSubmittedWeekly": true,
    "weeklyReportImageCount": 0,
    "submitWeeklyTime": "4",
    "isSubmittedMonthlyReport": false,
    "monthlyReportImageCount": 0,
    "submitMonthlyReportTime": "29",
    "model": "gpt-4o-mini",
    "apikey": "sk-osdhgosdipghpsdgjiosfvinoips",
    "apiUrl": "https://api.openai.com/",
    "pushType": null,
    "pushKey": null,
    "device": "{brand: OnePlus PHP110, systemVersion: 14, Platform: Android, isPhysicalDevice: true, incremental: T.1as885b-be80-be7f}"
  }
}
```

#### 图片提交说明

配置对应的配置项目，将图片放到images目录，运行时会自动随机抽取指定数量图片提交

#### 消息推送

支持：

- [Server酱](https://sct.ftqq.com/r/13600)
- [PushPlus](https://www.pushplus.plus/)
- [AnPush](https://anpush.com/)

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
[![Stargazers over time](https://starchart.cc/Rockytkg/AutoMoGuDingCheckIn.svg?variant=adaptive)](https://starchart.cc/Rockytkg/AutoMoGuDingCheckIn)
