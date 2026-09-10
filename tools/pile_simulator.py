import argparse
import asyncio
import itertools

START_FLAG = 0x68


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF


def bcd(text: str, n: int) -> bytes:
    s = ''.join(c for c in text if c.isdigit()).zfill(n * 2)[-n * 2:]
    return bytes((int(s[i]) << 4) | int(s[i + 1]) for i in range(0, len(s), 2))


def frame(seq: int, tp: int, body: bytes) -> bytes:
    payload = seq.to_bytes(2, 'little') + b'\x00' + bytes([tp]) + body
    return bytes([START_FLAG, len(payload)]) + payload + crc16_modbus(payload).to_bytes(2, 'little')


def read_one(buf: bytearray):
    while buf and buf[0] != START_FLAG:
        del buf[0]
    if len(buf) < 2:
        return None
    total = buf[1] + 4
    if len(buf) < total:
        return None
    raw = bytes(buf[:total])
    del buf[:total]
    return raw


async def recv_frame(reader: asyncio.StreamReader):
    buf = bytearray()
    while True:
        raw = read_one(buf)
        if raw:
            return raw
        data = await reader.read(4096)
        if not data:
            raise ConnectionError('server closed')
        buf.extend(data)


def realtime_body(pile: bytes, sample: int) -> bytes:
    # 云快充 V1.6 7.2 / 0x13，BIN 多字节字段低位在前。
    soc = min(95, 46 + sample)
    voltage = 3990 + (sample % 10) * 2          # 399.0 ~ 400.8 V
    current = 999 + (sample % 8) * 5           # 99.9 ~ 103.4 A
    elapsed = 35 + sample
    remaining = max(0, 60 - elapsed)
    energy = 234567 + sample * 1250             # 23.4567 kWh +
    amount = 303838 + sample * 1600             # 30.3838 yuan +
    transaction = bcd('320102000000010126091022300001', 16)
    return b''.join([
        transaction,
        pile,
        bcd('01', 1),
        b'\x03',                                # charging
        b'\x00',                                # gun not returned
        b'\x01',                                # plugged
        voltage.to_bytes(2, 'little'),
        current.to_bytes(2, 'little'),
        bytes([90]),                             # 40 C with -50 offset
        b'\x00' * 8,
        bytes([soc]),
        bytes([85]),                             # battery max temp 35 C
        elapsed.to_bytes(2, 'little'),
        remaining.to_bytes(2, 'little'),
        energy.to_bytes(4, 'little'),
        energy.to_bytes(4, 'little'),            # loss energy, demo same as energy
        amount.to_bytes(4, 'little'),
        b'\x00\x00',                           # no hardware fault
    ])


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8768)
    ap.add_argument('--pile', default='32010200000001')
    ap.add_argument('--type', type=int, default=1, choices=[0, 1], help='0=DC, 1=AC')
    args = ap.parse_args()

    reader, writer = await asyncio.open_connection(args.host, args.port)
    pile = bcd(args.pile, 7)
    login_body = pile + bytes([args.type, 1, 0x10]) + b'V0.3.0\x00\x00' + b'\x01' + bcd('0', 10) + b'\x04'
    tx = frame(0, 0x01, login_body)
    print('TX LOGIN    ', tx.hex(' ').upper())
    writer.write(tx); await writer.drain()
    print('RX LOGIN ACK', (await recv_frame(reader)).hex(' ').upper())

    seq = itertools.count(1)
    sample = 0
    try:
        while True:
            hb_seq = next(seq) & 0xFFFF
            hb = frame(hb_seq, 0x03, pile + bcd('01', 1) + b'\x00')
            print('TX HEARTBEAT', hb.hex(' ').upper())
            writer.write(hb); await writer.drain()
            print('RX HEART ACK', (await recv_frame(reader)).hex(' ').upper())

            rt_seq = next(seq) & 0xFFFF
            rt = frame(rt_seq, 0x13, realtime_body(pile, sample))
            print('TX REALTIME ', rt.hex(' ').upper())
            writer.write(rt); await writer.drain()
            sample += 1
            await asyncio.sleep(15)
    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
