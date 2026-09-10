# ChargingStationCloud

基于《云快充平台协议 V1.6》的充电桩私有云平台与微信小程序项目。

## V0.1 目标

- Python asyncio TCP Server
- 云快充 0x68 帧解析与组帧
- TCP 粘包/拆包处理
- CRC16(Modbus)
- BCD 编解码
- 0x01/0x02 充电桩登录认证
- 0x03/0x04 心跳
- 0x05/0x06 计费模型验证兼容（业务不做支付、计费）
- 设备在线/离线状态
- FastAPI REST API
- 模拟充电桩测试工具

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
tools/
  pile_simulator.py
config/
  config.yaml
```

## 启动

```bash
cd server
python3 -m pip install -r requirements.txt
python3 main.py
```

默认：

- TCP 充电桩接入端口：8768
- HTTP API：8000

模拟充电桩：

```bash
python3 tools/pile_simulator.py --host 127.0.0.1 --port 8768 --pile 32010200000001
```

## REST API

```text
GET /health
GET /api/devices
GET /api/devices/{pile_code}
```

> 当前版本不做支付、不做业务计费。协议层保留计费模型验证应答，避免充电桩登录后卡在协议流程。
