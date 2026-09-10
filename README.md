# ChargingStationCloud

基于《云快充平台协议 V1.6》的充电桩私有云平台、Web 实训教学云平台与微信小程序项目。

## 当前版本：V1.0-RC1

本版本用于集中联调，先把核心业务链打通，再根据真实充电桩测试结果修正协议细节。

已实现：

- Python 3.11 asyncio TCP Server，默认端口 8768
- 0x68 帧拆包/粘包、序列号、加密标志、CRC、BCD/BIN 处理
- 0x01 / 0x02 登录认证
- 0x03 / 0x04 心跳
- 0x05 / 0x06 计费模型验证
- 0x13 实时监测数据：电压、电流、SOC、温度、时长、电量、金额、故障位
- 0x31 / 0x32 桩端申请启动 / 平台确认启动
- 0x34 / 0x33 平台远程启机 / 桩启动回复
- 0x36 / 0x35 平台远程停机 / 桩停机回复
- 0x3B / 0x40 交易记录接收 / 平台确认
- 设备在线状态、当前交易状态、通信日志、交易列表
- Web 云平台：设备、实时监控、远程启停、二维码内容、故障、日志、报文校验、计费模型、教学说明
- 微信小程序：首页、扫码、充电、我的；扫码可选择桩，充电页可下发远程启停
- 支付、余额、计费字段和界面暂时保留

> 注意：RC1 模拟器发送的 0x3B 为“最小交易记录模拟帧”，用于验证 0x3B -> 0x40 链路。接真实桩时，服务端允许接收完整 V1.6 交易记录，但完整字段解析将在真实报文到手后逐字段校准。

## Windows 11 启动

项目根目录：

```bash
cd /d/Code/ChargingStationCloud
source .venv/Scripts/activate
python server/main.py
```

服务地址：

- TCP：`0.0.0.0:8768`
- HTTP API：`http://127.0.0.1:8000`
- Web：`http://127.0.0.1:8000/`
- Swagger：`http://127.0.0.1:8000/docs`

另开终端启动模拟桩：

```bash
cd /d/Code/ChargingStationCloud
source .venv/Scripts/activate
python tools/pile_simulator.py --host 127.0.0.1 --port 8768 --pile 32010200000001
```

模拟“桩端刷卡启动 0x31”：

```bash
python tools/pile_simulator.py --host 127.0.0.1 --port 8768 --pile 32010200000001 --pile-start
```

## 推荐 RC1 测试顺序

1. 启动 `server/main.py`。
2. 启动 `pile_simulator.py`，确认 0x01/0x02、0x03/0x04 正常。
3. 打开 Web，确认设备在线及 0x13 数据刷新。
4. 进入“远程启停充电”，点击 0x34；模拟桩应收到 0x34 并回复 0x33，同时 0x13 状态变为充电中。
5. 点击 0x36；模拟桩回复 0x35，并上送 0x3B，平台回复 0x40。
6. 查看“通信日志”和“充电交易”，确认同一订单交易流水号一致。
7. 微信开发者工具打开 `miniprogram/`，充电页测试启动/停止。
8. 使用 `--pile-start` 测试 0x31 -> 0x32 桩端启动。

协议要求同一笔订单的鉴权回复、实时数据和交易记录使用同一个交易流水号；RC1 按这个规则维护订单状态。

## REST API

```text
GET  /health
GET  /api/devices
GET  /api/devices/{pile_code}
GET  /api/devices/{pile_code}/realtime
POST /api/charge/start
POST /api/charge/stop
GET  /api/transactions
GET  /api/logs
GET  /api/tariff
POST /api/protocol/verify
```

## 项目目录

```text
server/
  app/
    api/
    protocol/
    tcp_server/
    services/
web/
miniprogram/
tools/
```

## 真实设备联调重点

真实 ACP611CN / RXDCP810 接入后，优先核对：完整 0x3B 字段布局、0x35/0x40 实际回复字段、计费模型 0x09/0x0A/0x58/0x57、0x15/0x17/0x19/0x23/0x25 BMS 过程帧，以及厂家对 CRC 实现和字节序的实际要求。RC1 不把模拟数据当作真实桩验证结论。
