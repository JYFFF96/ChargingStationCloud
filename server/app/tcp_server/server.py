import asyncio
import itertools
import logging

from app.protocol.ykc import (
    extract_frames, parse_frame, parse_login_body, build_login_ack,
    parse_heartbeat_body, build_heartbeat_ack, parse_tariff_verify_body,
    build_tariff_verify_ack, parse_realtime_body, parse_start_request_31,
    build_start_confirm_32, parse_start_reply_33, parse_stop_reply_35,
    parse_transaction_3b, build_transaction_ack_40, make_transaction_id,
)
from app.services.device_registry import registry
from app.services.control_hub import hub

log = logging.getLogger('ykc.tcp')


class YKCTCPServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8768):
        self.host=host; self.port=port; self.server=None; self._tx_serial=itertools.count(1)

    async def start(self):
        self.server=await asyncio.start_server(self._handle_client,self.host,self.port)
        log.info('YKC TCP server listening on %s:%s',self.host,self.port)
        async with self.server: await self.server.serve_forever()

    async def _handle_client(self,reader:asyncio.StreamReader,writer:asyncio.StreamWriter):
        peer_tuple=writer.get_extra_info('peername'); peer=f'{peer_tuple[0]}:{peer_tuple[1]}' if peer_tuple else 'unknown'
        log.info('client connected: %s',peer); buffer=bytearray()
        try:
            while True:
                data=await reader.read(4096)
                if not data: break
                log.info('RX %s | %s',peer,data.hex(' ').upper()); buffer.extend(data)
                frames,buffer=extract_frames(buffer)
                for raw in frames:
                    try:
                        frame=parse_frame(raw)
                        reply=self._dispatch(frame,peer,writer)
                        if reply:
                            writer.write(reply); await writer.drain(); log.info('TX %s | %s',peer,reply.hex(' ').upper())
                    except Exception as exc: log.exception('frame error from %s: %s',peer,exc)
        except (ConnectionResetError,asyncio.IncompleteReadError): pass
        finally:
            hub.unregister_writer(writer); registry.mark_offline_by_peer(peer); writer.close()
            try: await writer.wait_closed()
            except Exception: pass
            log.info('client disconnected: %s',peer)

    def _dispatch(self,frame,peer:str,writer:asyncio.StreamWriter):
        if frame.encrypted!=0:
            log.warning('encrypted frame unsupported: type=0x%02X',frame.frame_type); return None
        raw_hex=frame.raw.hex(' ').upper()

        if frame.frame_type==0x01:
            info=parse_login_body(frame.body); registry.upsert_login(info,peer); hub.register(info['pile_code'],writer,asyncio.get_running_loop())
            registry.log('up',0x01,info['pile_code'],'登录认证',raw_hex)
            log.info('LOGIN pile=%s type=%s guns=%s proto=v%.1f',info['pile_code'],info['pile_type'],info['gun_count'],info['protocol_version'])
            reply=build_login_ack(frame.seq,frame.body[:7],True); registry.log('down',0x02,info['pile_code'],'登录认证通过',reply.hex(' ').upper()); return reply

        if frame.frame_type==0x03:
            info=parse_heartbeat_body(frame.body); registry.touch(info['pile_code'],0x03); registry.log('up',0x03,info['pile_code'],f"心跳 gun={info['gun_no']} status={info['gun_status']}",raw_hex)
            reply=build_heartbeat_ack(frame.seq,frame.body); registry.log('down',0x04,info['pile_code'],'心跳应答',reply.hex(' ').upper()); return reply

        if frame.frame_type==0x05:
            info=parse_tariff_verify_body(frame.body); registry.touch(info['pile_code'],0x05); registry.log('up',0x05,info['pile_code'],f"计费模型验证 {info['model_code']}",raw_hex)
            reply=build_tariff_verify_ack(frame.seq,frame.body,True); registry.log('down',0x06,info['pile_code'],'计费模型一致',reply.hex(' ').upper()); return reply

        if frame.frame_type==0x13:
            info=parse_realtime_body(frame.body); registry.update_realtime(info); registry.log('up',0x13,info['pile_code'],f"实时 V={info['voltage_v']:.1f} I={info['current_a']:.1f} SOC={info['soc_pct']}%",raw_hex)
            log.info('REALTIME pile=%s gun=%s status=%s V=%.1f I=%.1f SOC=%s%% energy=%.4fkWh amount=%.4f faults=%s',info['pile_code'],info['gun_no'],info['work_status'],info['voltage_v'],info['current_a'],info['soc_pct'],info['energy_kwh'],info['amount_yuan'],info['faults']); return None

        if frame.frame_type==0x31:
            info=parse_start_request_31(frame.body); registry.touch(info['pile_code'],0x31); txid=make_transaction_id(info['pile_code'],info['gun_no'],next(self._tx_serial))
            registry.log('up',0x31,info['pile_code'],f"桩端申请启动 method={info['start_method']}",raw_hex)
            reply=build_start_confirm_32(frame.seq,txid,info['pile_code'],info['gun_no'],logical_card='0',balance_yuan=1000.0,ok=True,reason=0)
            registry.control_sent(info['pile_code'],0x32,txid,reply.hex(' ').upper()); registry.log('down',0x32,info['pile_code'],f'确认启动 tx={txid}',reply.hex(' ').upper()); return reply

        if frame.frame_type==0x33:
            info=parse_start_reply_33(frame.body); registry.start_reply(info); registry.log('up',0x33,info['pile_code'],f"启机回复 result={info['result']} reason={info['reason']}",raw_hex); return None

        if frame.frame_type==0x35:
            info=parse_stop_reply_35(frame.body); registry.stop_reply(info); registry.log('up',0x35,info['pile_code'],f"停机回复 result={info['result']} reason={info['reason']}",raw_hex); return None

        if frame.frame_type==0x3B:
            info=parse_transaction_3b(frame.body); registry.transaction_record(info); registry.log('up',0x3B,info['pile_code'],f"交易记录 tx={info['transaction_id']}",raw_hex)
            reply=build_transaction_ack_40(frame.seq,frame.body); registry.log('down',0x40,info['pile_code'],'交易记录确认',reply.hex(' ').upper()); return reply

        registry.log('up',frame.frame_type,'',f'未处理帧 seq={frame.seq}',raw_hex); log.info('UNHANDLED frame type=0x%02X seq=%s',frame.frame_type,frame.seq); return None
