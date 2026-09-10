import time
from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass
class DeviceState:
    pile_code: str
    peer: str
    online: bool = True
    pile_type: int = -1
    gun_count: int = 0
    protocol_version: float = 0.0
    program_version: str = ''
    network_type: int = -1
    last_seen: float = 0.0
    last_frame_type: int = 0

    def touch(self, frame_type: int = 0) -> None:
        self.online = True
        self.last_seen = time.time()
        if frame_type:
            self.last_frame_type = frame_type


class DeviceRegistry:
    def __init__(self) -> None:
        self._devices: Dict[str, DeviceState] = {}

    def upsert_login(self, info: dict, peer: str) -> DeviceState:
        code = info['pile_code']
        dev = self._devices.get(code) or DeviceState(pile_code=code, peer=peer)
        dev.peer = peer
        dev.pile_type = info.get('pile_type', -1)
        dev.gun_count = info.get('gun_count', 0)
        dev.protocol_version = info.get('protocol_version', 0.0)
        dev.program_version = info.get('program_version', '')
        dev.network_type = info.get('network_type', -1)
        dev.touch(0x01)
        self._devices[code] = dev
        return dev

    def touch(self, pile_code: str, frame_type: int) -> Optional[DeviceState]:
        dev = self._devices.get(pile_code)
        if dev:
            dev.touch(frame_type)
        return dev

    def mark_offline_by_peer(self, peer: str) -> None:
        for dev in self._devices.values():
            if dev.peer == peer:
                dev.online = False

    def get(self, pile_code: str) -> Optional[dict]:
        dev = self._devices.get(pile_code)
        return asdict(dev) if dev else None

    def all(self) -> list:
        now = time.time()
        result = []
        for dev in self._devices.values():
            if dev.online and now - dev.last_seen > 35:
                dev.online = False
            result.append(asdict(dev))
        return result


registry = DeviceRegistry()
