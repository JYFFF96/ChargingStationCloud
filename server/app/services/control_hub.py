import asyncio
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Callable

from app.protocol.ykc import build_frame


@dataclass
class Session:
    pile_code: str
    writer: asyncio.StreamWriter
    loop: asyncio.AbstractEventLoop
    seq: int = 0


class ControlHub:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()

    def register(self, pile_code: str, writer: asyncio.StreamWriter, loop: asyncio.AbstractEventLoop) -> None:
        with self._lock: self._sessions[pile_code] = Session(pile_code=pile_code, writer=writer, loop=loop)

    def unregister_writer(self, writer: asyncio.StreamWriter) -> None:
        with self._lock:
            for code in [k for k,v in self._sessions.items() if v.writer is writer]: del self._sessions[code]

    def online(self, pile_code: str) -> bool:
        with self._lock: return pile_code in self._sessions

    def _session_and_seq(self, pile_code: str):
        with self._lock:
            session: Optional[Session] = self._sessions.get(pile_code)
            if not session: raise RuntimeError('device not connected')
            seq=session.seq; session.seq=(session.seq+1)&0xFFFF
            return session,seq

    def send_raw_builder(self,pile_code:str,builder:Callable[[int],bytes],timeout:float=3.0)->dict:
        session,seq=self._session_and_seq(pile_code); raw=builder(seq)
        async def _write():
            session.writer.write(raw); await session.writer.drain()
        fut=asyncio.run_coroutine_threadsafe(_write(),session.loop); fut.result(timeout=timeout)
        return {'seq':seq,'frame_type':raw[5] if len(raw)>5 else 0,'raw_hex':raw.hex(' ').upper()}

    def send(self,pile_code:str,frame_type:int,body:bytes,timeout:float=3.0)->dict:
        return self.send_raw_builder(pile_code,lambda seq:build_frame(seq,frame_type,body),timeout)


hub=ControlHub()
