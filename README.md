# AutoMoGuDingCheckIn

AutoMoGuDingCheckIn 工学云自动打卡，采用新接口，更安全，支持多用户、自定义位置信息、保持登录状态、每日打卡检查、打卡位置浮动、消息推送，免服务器运行

## 项目概述

AutoMoGuDingCheckIn 旨在：

- 自动化工学云应用中的签到过程。
- 自动提交月报、周报、日报。
- ~~适配云函数~~

## 功能列表

- [x] 自动签到
- [x] 消息推送功能
- [x] 多用户支持
- [x] 打卡位置浮动
- [x] 自动提交日报
- [x] 自动提交周报
- [x] 自动提交月报
- [x] AI生成周、日、月报
- [x] 打卡备注以及带图打卡
- [x] Github工作流支持
- [ ] ~~适配云函数~~

## 使用方法

### Github工作流
参见 [Wiki](https://github.com/Rockytkg/AutoMoGuDingCheckIn/wiki/Github-%E5%B7%A5%E4%BD%9C%E6%B5%81%E9%83%A8%E7%BD%B2)

### 本地运行

#### 环境

- Python 3.10+
- pip（Python 包管理器）

#### 安装

1. 克隆代码库：
    ```bash
    git clone https://github.com/Rockytkg/AutoMoGuDingCheckIn.git
    cd AutoMoGuDingCheckIn
    ```

2. 按照下面要求添加配置文件
3. 执行（linux系统，windows需要自行配置计划任务程序）
    ```bash
    chmod +x setup.sh
    bash setup.sh
    ```
    按照脚本提示设置定时任务并执行
#### 配置

1. 打开user目录，根据下表修改json文件中的配置（每个文件就是一个用户）

<table>
    <tr>
        <th>配置项</th>
        <th>字段</th>
        <th>说明</th>
        <th>示例</th>
    </tr>
    <tr>
        <td rowspan="2">用户信息</td>
        <td>phone</td>
        <td>工学云手机号，确保号码正确无误。</td>
        <td>13800138000</td>
    </tr>
    <tr>
        <td>password</td>
        <td>工学云密码，注意区分大小写。</td>
        <td>your_password</td>
    </tr>
    <tr>
        <td rowspan="8">打卡设置</td>
        <td>address</td>
        <td>打卡地点的详细地址，确保信息准确。</td>
        <td>四川省 · 成都市 · 高新区 · 在科创十一街附近</td>
    </tr>
    <tr>
        <td>latitude</td>
        <td>打卡地点的纬度。</td>
        <td>34.059922</td>
    </tr>
    <tr>
        <td>longitude</td>
        <td>打卡地点的经度。</td>
        <td>118.277435</td>
    </tr>
    <tr>
        <td>province</td>
        <td>所在省份。</td>
        <td>四川省</td>
    </tr>
    <tr>
        <td>city</td>
        <td>所在城市。</td>
        <td>成都市</td>
    </tr>
    <tr>
        <td>area</td>
        <td>所在区域。</td>
        <td>高新区</td>
    </tr>
    <tr>
        <td>imageCount</td>
        <td>打卡时需要上传的图片数量，默认为0。</td>
        <td>0</td>
    </tr>
    <tr>
        <td>description</td>
        <td>打卡备注</td>
        <td>列表，一个元素为一条，打卡时候随机抽取，若为空就不带备注</td>
    </tr>
    <tr>
        <td rowspan="8">报告设置</td>
        <td>daily.enabled</td>
        <td>是否启用每日报告（true 或 false）。</td>
        <td>false</td>
    </tr>
    <tr>
        <td>daily.imageCount</td>
        <td>每日报告中需要上传的图片数量。</td>
        <td>0</td>
    </tr>
    <tr>
        <td>weekly.enabled</td>
        <td>是否启用每周报告（true 或 false）。</td>
        <td>true</td>
    </tr>
    <tr>
        <td>weekly.imageCount</td>
        <td>每周报告中需要上传的图片数量。</td>
        <td>0</td>
    </tr>
    <tr>
        <td>weekly.submitTime</td>
        <td>提交时间（以小时为单位，范围为0-23）。</td>
        <td>4</td>
    </tr>
    <tr>
        <td>monthly.enabled</td>
        <td>是否启用每月报告（true 或 false）。</td>
        <td>false</td>
    </tr>
    <tr>
        <td>monthly.imageCount</td>
        <td>每月报告中需要上传的图片数量。</td>
        <td>0</td>
    </tr>
    <tr>
        <td>monthly.submitTime</td>
        <td>提交时间（默认为29号）。</td>
        <td>29</td>
    </tr>
    <tr>
        <td rowspan="3">AI 设置</td>
        <td>model</td>
        <td>AI 模型名称（可根据需求修改）。</td>
        <td>gpt-4o-mini</td>
    </tr>
    <tr>
        <td>apikey</td>
        <td>API 密钥，确保无误。</td>
        <td>sk-osdhgosdipghpsdgjiosfvinoips</td>
    </tr>
    <tr>
        <td>apiUrl</td>
        <td>API 地址，通常为 `https://api.openai.com/`。</td>
        <td>https://api.openai.com/</td>
    </tr>
    <tr>
        <td rowspan="10">推送通知设置</td>
        <td>type</td>
        <td>推送通知的类型（如 Server、PushPlus 等）。</td>
        <td>Server</td>
    </tr>
    <tr>
        <td>enabled</td>
        <td>是否启用该推送通知（true 或 false）。</td>
        <td>true</td>
    </tr>
    <tr>
        <td>sendKey/token</td>
        <td>相应的密钥或令牌。</td>
        <td>your_key</td>
    </tr>
    <tr>
        <td>channel</td>
        <td>对于 AnPush，填写通道 ID，多个用英文逗号隔开。</td>
        <td>通道ID1,通道ID2</td>
    </tr>
    <tr>
        <td>to</td>
        <td>根据官方文档获取的接收者信息。</td>
        <td>recipient@example.com</td>
    </tr>
    <tr>
        <td>host</td>
        <td>SMTP 服务地址。</td>
        <td>smtp.example.com</td>
    </tr>
    <tr>
        <td>port</td>
        <td>SMTP 服务端口，通常为 465。</td>
        <td>465</td>
    </tr>
    <tr>
        <td>username</td>
        <td>发件人邮箱地址。</td>
        <td>sender@example.com</td>
    </tr>
    <tr>
        <td>password</td>
        <td>SMTP 密码。</td>
        <td>smtp_password</td>
    </tr>
    <tr>
        <td>from</td>
        <td>发件人名称。</td>
        <td>发件人名称</td>
    </tr>
    <tr>
        <td rowspan="5">设备信息</td>
        <td>设备信息</td>
        <td>设备信息，<a href="https://www.123pan.com/s/rlqcVv-bQOPH.html" rel="nofollow">用这个小工具获取</a></td>
        <td>{brand: TA J20, systemVersion: 17, Platform: Android, isPhysicalDevice: true, incremental: K23V10A}</td>
    </tr>
</table>

##### 示例 JSON 配置

```json
{
  "config": {
    "user": {
      "phone": "工学云手机号",
      "password": "工学云密码"
    },
    "clockIn": {
      "location": {
        "address": "四川省 · 成都市 · 高新区 · 在科创十一街附近",
        "latitude": "34.059922",
        "longitude": "118.277435",
        "province": "四川省",
        "city": "成都市",
        "area": "高新区"
      },
      "imageCount": 0,
      "description": [
        "今天天气不错",
        "今天天气很好",
        "今天天气不太好"
      ]
    },
    "reportSettings": {
      "daily": {
        "enabled": false,
        "imageCount": 0
      },
      "weekly": {
        "enabled": true,
        "imageCount": 0,
        "submitTime": 4
      },
      "monthly": {
        "enabled": false,
        "imageCount": 0,
        "submitTime": 29
      }
    },
    "ai": {
      "model": "gpt-4o-mini",
      "apikey": "sk-osdhgosdipghpsdgjiosfvinoips",
      "apiUrl": "https://api.openai.com/"
    },
    "pushNotifications": [
      {
        "type": "Server",
        "enabled": true,
        "sendKey": "your_key"
      },
      {
        "type": "PushPlus",
        "enabled": true,
        "token": "your_token"
      },
      {
        "type": "AnPush",
        "enabled": true,
        "token": "your_token",
        "channel": "通道ID,多个用英文逗号隔开",
        "to": "根据官方文档获取"
      },
      {
        "type": "WxPusher",
        "enabled": true,
        "spt": "your_spt"
      },
      {
        "type": "SMTP",
        "enabled": true,
        "host": "smtp服务地址",
        "port": 465,
        "username": "发件人邮箱",
        "password": "smtp密码",
        "from": "发件人名称",
        "to": "收件人邮箱"
      }
    ],
    "device": "{brand: TA J20, systemVersion: 17, Platform: Android, isPhysicalDevice: true, incremental: K23V10A}"
  }
}
```

##### 图片提交说明

配置对应的配置项目，将图片放到images目录，运行时会自动随机抽取指定数量图片提交

##### 消息推送

支持：

- [Server酱](https://sct.ftqq.com/r/13600)
- [PushPlus](https://www.pushplus.plus/)
- [AnPush](https://anpush.com/)
- [WxPusher](https://wxpusher.zjiecode.com/)
- SMTP

#### 运行

```bash
python main.py
```

## 许可证

本项目采用 Apache 2.0 许可。详细信息请参阅 [LICENSE](https://github.com/Rockytkg/AutoMoGuDingCheckIn/blob/main/LICENSE)
文件。

## 联系方式

如有任何疑问或需要支持，请通过提交 [issue](https://github.com/Rockytkg/AutoMoGuDingCheckIn/issues) 与我们联系。

## start
[![Stargazers over time](https://starchart.cc/Rockytkg/AutoMoGuDingCheckIn.svg?variant=adaptive)](https://starchart.cc/Rockytkg/AutoMoGuDingCheckIn)
