from dataclasses import dataclass
from typing import List, Tuple

START_FLAG = 0x68


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF


def bcd_encode_digits(text: str, byte_len: int) -> bytes:
    digits = ''.join(ch for ch in text if ch.isdigit()).zfill(byte_len * 2)[-byte_len * 2:]
    return bytes((int(digits[i]) << 4) | int(digits[i + 1]) for i in range(0, len(digits), 2))


def bcd_decode(data: bytes) -> str:
    out = []
    for b in data:
        out.append(str((b >> 4) & 0x0F))
        out.append(str(b & 0x0F))
    return ''.join(out)


@dataclass
class Frame:
    seq: int
    encrypted: int
    frame_type: int
    body: bytes
    raw: bytes


def build_frame(seq: int, frame_type: int, body: bytes = b'', encrypted: int = 0) -> bytes:
    payload = seq.to_bytes(2, 'little') + bytes([encrypted, frame_type]) + body
    if len(payload) > 200:
        raise ValueError('payload too long')
    crc = crc16_modbus(payload)
    return bytes([START_FLAG, len(payload)]) + payload + crc.to_bytes(2, 'little')


def parse_frame(raw: bytes, verify_crc: bool = True) -> Frame:
    if len(raw) < 8 or raw[0] != START_FLAG:
        raise ValueError('invalid frame')
    data_len = raw[1]
    total = data_len + 4
    if len(raw) != total:
        raise ValueError(f'length mismatch expected={total} actual={len(raw)}')
    payload = raw[2:2 + data_len]
    recv_crc = int.from_bytes(raw[-2:], 'little')
    calc_crc = crc16_modbus(payload)
    if verify_crc and recv_crc != calc_crc:
        raise ValueError(f'crc mismatch recv=0x{recv_crc:04X} calc=0x{calc_crc:04X}')
    return Frame(seq=int.from_bytes(payload[0:2], 'little'), encrypted=payload[2], frame_type=payload[3], body=payload[4:], raw=raw)


def extract_frames(buffer: bytearray) -> Tuple[List[bytes], bytearray]:
    frames: List[bytes] = []
    while True:
        while buffer and buffer[0] != START_FLAG:
            del buffer[0]
        if len(buffer) < 2:
            break
        total = buffer[1] + 4
        if total < 8:
            del buffer[0]
            continue
        if len(buffer) < total:
            break
        frames.append(bytes(buffer[:total]))
        del buffer[:total]
    return frames, buffer


def parse_login_body(body: bytes) -> dict:
    if len(body) < 30:
        raise ValueError('login body too short')
    return {'pile_code': bcd_decode(body[0:7]), 'pile_type': body[7], 'gun_count': body[8], 'protocol_version': body[9] / 10.0, 'program_version': body[10:18].rstrip(b'\x00').decode('ascii', errors='replace'), 'network_type': body[18], 'sim': bcd_decode(body[19:29]), 'operator': body[29]}


def build_login_ack(seq: int, pile_code_bcd: bytes, ok: bool = True) -> bytes:
    return build_frame(seq, 0x02, pile_code_bcd[:7] + bytes([0x00 if ok else 0x01]))


def parse_heartbeat_body(body: bytes) -> dict:
    if len(body) < 9:
        raise ValueError('heartbeat body too short')
    return {'pile_code': bcd_decode(body[0:7]), 'gun_no': bcd_decode(body[7:8]), 'gun_status': body[8]}


def build_heartbeat_ack(seq: int, body: bytes) -> bytes:
    if len(body) < 8:
        raise ValueError('heartbeat body too short')
    return build_frame(seq, 0x04, body[0:8] + b'\x00')


def parse_tariff_verify_body(body: bytes) -> dict:
    if len(body) < 9:
        raise ValueError('tariff verify body too short')
    return {'pile_code': bcd_decode(body[:7]), 'model_code': bcd_decode(body[7:9])}


def build_tariff_verify_ack(seq: int, body: bytes, consistent: bool = True) -> bytes:
    if len(body) < 9:
        raise ValueError('tariff verify body too short')
    return build_frame(seq, 0x06, body[:9] + bytes([0x00 if consistent else 0x01]))


def parse_realtime_body(body: bytes) -> dict:
    """云快充 V1.6 7.2 / 0x13，消息体固定 60B，BIN 多字节低位在前。"""
    if len(body) < 60:
        raise ValueError(f'realtime body too short: {len(body)}')
    u16 = lambda p: int.from_bytes(body[p:p + 2], 'little')
    u32 = lambda p: int.from_bytes(body[p:p + 4], 'little')
    fault_bits = u16(58)
    return {
        'transaction_id': bcd_decode(body[0:16]),
        'pile_code': bcd_decode(body[16:23]),
        'gun_no': bcd_decode(body[23:24]),
        'work_status': body[24],
        'gun_returned': body[25],
        'gun_plugged': body[26],
        'voltage_v': u16(27) / 10.0,
        'current_a': u16(29) / 10.0,
        'gun_temp_c': body[31] - 50,
        'gun_code': body[32:40].hex().upper(),
        'soc_pct': body[40],
        'battery_max_temp_c': body[41] - 50,
        'elapsed_min': u16(42),
        'remaining_min': u16(44),
        'energy_kwh': u32(46) / 10000.0,
        'loss_energy_kwh': u32(50) / 10000.0,
        'amount_yuan': u32(54) / 10000.0,
        'fault_bits': fault_bits,
        'faults': [bit + 1 for bit in range(13) if fault_bits & (1 << bit)],
    }
