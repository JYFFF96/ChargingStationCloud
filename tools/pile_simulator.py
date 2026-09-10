import argparse
import asyncio

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


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8768)
    ap.add_argument('--pile', default='32010200000001')
    ap.add_argument('--type', type=int, default=1, choices=[0, 1], help='0=DC, 1=AC')
    args = ap.parse_args()

    reader, writer = await asyncio.open_connection(args.host, args.port)
    pile = bcd(args.pile, 7)

    login_body = pile + bytes([args.type, 1, 0x10]) + b'V0.1.0\x00\x00' + b'\x01' + bcd('0', 10) + b'\x04'
    tx = frame(0, 0x01, login_body)
    print('TX LOGIN    ', tx.hex(' ').upper())
    writer.write(tx); await writer.drain()
    print('RX LOGIN ACK', (await recv_frame(reader)).hex(' ').upper())

    seq = 1
    try:
        while True:
            hb = frame(seq, 0x03, pile + bcd('01', 1) + b'\x00')
            print('TX HEARTBEAT', hb.hex(' ').upper())
            writer.write(hb); await writer.drain()
            print('RX HEART ACK', (await recv_frame(reader)).hex(' ').upper())
            seq = (seq + 1) & 0xFFFF
            await asyncio.sleep(10)
    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
