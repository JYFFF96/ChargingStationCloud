import asyncio
import threading
from dataclasses import dataclass
from typing import Dict, Optional

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
        with self._lock:
            self._sessions[pile_code] = Session(pile_code=pile_code, writer=writer, loop=loop)

    def unregister_writer(self, writer: asyncio.StreamWriter) -> None:
        with self._lock:
            for code in [k for k, v in self._sessions.items() if v.writer is writer]:
                del self._sessions[code]

    def online(self, pile_code: str) -> bool:
        with self._lock:
            return pile_code in self._sessions

    def send(self, pile_code: str, frame_type: int, body: bytes, timeout: float = 3.0) -> dict:
        with self._lock:
            session: Optional[Session] = self._sessions.get(pile_code)
            if not session:
                raise RuntimeError('device not connected')
            seq = session.seq
            session.seq = (session.seq + 1) & 0xFFFF
            writer = session.writer
            loop = session.loop
        raw = build_frame(seq, frame_type, body)

        async def _write() -> None:
            writer.write(raw)
            await writer.drain()

        fut = asyncio.run_coroutine_threadsafe(_write(), loop)
        fut.result(timeout=timeout)
        return {'seq': seq, 'frame_type': frame_type, 'raw_hex': raw.hex(' ').upper()}


hub = ControlHub()
