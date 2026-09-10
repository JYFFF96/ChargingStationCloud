# ChargingStationCloud

基于《云快充平台协议 V1.6》的充电桩私有云平台、Web 教学云平台与微信小程序项目。

## 当前版本 V0.3

已完成：

- Python asyncio TCP Server
- 云快充 0x68 帧解析与组帧
- TCP 粘包/拆包处理
- CRC16(Modbus 表算法兼容实现)
- BCD / BIN 编解码
- 0x01 / 0x02 充电桩登录认证
- 0x03 / 0x04 心跳，10 秒周期
- 0x05 / 0x06 计费模型验证兼容
- 0x13 上传实时监测数据解析
- 设备在线 / 离线状态
- 实时电压、电流、SOC、温度、时长、电量、金额、故障位
- FastAPI REST API
- Web 实训教学云平台
- 微信小程序首页 / 扫码 / 充电 / 我的
- 模拟充电桩，充电状态下每 15 秒发送 0x13

支付、余额、计费相关界面与协议字段暂时保留，后续按项目需求继续实现。

## 目录

```text
server/
  app/
    api/
    protocol/
    tcp_server/
    services/
  main.py
  requirements.txt
web/
  index.html
  style.css
  app.js
miniprogram/
  pages/
    index/
    scan/
    charging/
    profile/
tools/
  pile_simulator.py
```

## Windows 11 启动

在项目根目录激活 Python 3.11 虚拟环境：

```bash
source .venv/Scripts/activate
python server/main.py
```

默认服务：

- 充电桩 TCP：`0.0.0.0:8768`
- HTTP API：`0.0.0.0:8000`
- Web 云平台：`http://127.0.0.1:8000/`
- Swagger：`http://127.0.0.1:8000/docs`

另开终端启动模拟桩：

```bash
source .venv/Scripts/activate
python tools/pile_simulator.py --host 127.0.0.1 --port 8768 --pile 32010200000001
```

## REST API

```text
GET /health
GET /api/devices
GET /api/devices/{pile_code}
GET /api/devices/{pile_code}/realtime
```

`/realtime` 数据来自云快充 V1.6 的 `0x13` 上传实时监测数据。

## 下一步

- 0x34 / 0x33 远程启动充电
- 0x36 / 0x35 远程停止充电
- 0x31 / 0x32 桩端申请启动
- 0x3B / 0x40 交易记录
- 0x23 / 0x25 BMS 充电过程数据
- 计费模型和支付业务继续按原型保留并逐步接入真实逻辑
