import asyncio
import logging

from app.protocol.ykc import (
    extract_frames,
    parse_frame,
    parse_login_body,
    build_login_ack,
    parse_heartbeat_body,
    build_heartbeat_ack,
    parse_tariff_verify_body,
    build_tariff_verify_ack,
    parse_realtime_body,
)
from app.services.device_registry import registry

log = logging.getLogger('ykc.tcp')


class YKCTCPServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8768):
        self.host = host
        self.port = port
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        log.info('YKC TCP server listening on %s:%s', self.host, self.port)
        async with self.server:
            await self.server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer_tuple = writer.get_extra_info('peername')
        peer = f'{peer_tuple[0]}:{peer_tuple[1]}' if peer_tuple else 'unknown'
        log.info('client connected: %s', peer)
        buffer = bytearray()
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                log.info('RX %s | %s', peer, data.hex(' ').upper())
                buffer.extend(data)
                frames, buffer = extract_frames(buffer)
                for raw in frames:
                    try:
                        frame = parse_frame(raw)
                        reply = self._dispatch(frame, peer)
                        if reply:
                            writer.write(reply)
                            await writer.drain()
                            log.info('TX %s | %s', peer, reply.hex(' ').upper())
                    except Exception as exc:
                        log.exception('frame error from %s: %s', peer, exc)
        except (ConnectionResetError, asyncio.IncompleteReadError):
            pass
        finally:
            registry.mark_offline_by_peer(peer)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            log.info('client disconnected: %s', peer)

    def _dispatch(self, frame, peer: str):
        if frame.encrypted != 0:
            log.warning('encrypted frame unsupported: type=0x%02X', frame.frame_type)
            return None

        if frame.frame_type == 0x01:
            info = parse_login_body(frame.body)
            registry.upsert_login(info, peer)
            log.info('LOGIN pile=%s type=%s guns=%s proto=v%.1f', info['pile_code'], info['pile_type'], info['gun_count'], info['protocol_version'])
            return build_login_ack(frame.seq, frame.body[:7], True)

        if frame.frame_type == 0x03:
            info = parse_heartbeat_body(frame.body)
            registry.touch(info['pile_code'], 0x03)
            log.info('HEARTBEAT pile=%s gun=%s status=%s', info['pile_code'], info['gun_no'], info['gun_status'])
            return build_heartbeat_ack(frame.seq, frame.body)

        if frame.frame_type == 0x05:
            info = parse_tariff_verify_body(frame.body)
            registry.touch(info['pile_code'], 0x05)
            log.info('TARIFF VERIFY pile=%s model=%s', info['pile_code'], info['model_code'])
            return build_tariff_verify_ack(frame.seq, frame.body, True)

        if frame.frame_type == 0x13:
            info = parse_realtime_body(frame.body)
            registry.update_realtime(info)
            log.info('REALTIME pile=%s gun=%s status=%s V=%.1f I=%.1f SOC=%s%% energy=%.4fkWh amount=%.4f faults=%s',
                     info['pile_code'], info['gun_no'], info['work_status'], info['voltage_v'], info['current_a'],
                     info['soc_pct'], info['energy_kwh'], info['amount_yuan'], info['faults'])
            return None

        log.info('UNHANDLED frame type=0x%02X seq=%s', frame.frame_type, frame.seq)
        return None
