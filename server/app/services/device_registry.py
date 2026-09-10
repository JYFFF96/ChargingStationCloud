import time
from dataclasses import asdict, dataclass, field
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
    realtime: dict = field(default_factory=dict)
    transaction_id: str = ''
    charge_state: str = 'idle'
    last_control: dict = field(default_factory=dict)

    def touch(self, frame_type: int = 0) -> None:
        self.online = True; self.last_seen = time.time()
        if frame_type: self.last_frame_type = frame_type


class DeviceRegistry:
    def __init__(self) -> None:
        self._devices: Dict[str, DeviceState] = {}
        self._transactions: Dict[str, dict] = {}
        self._logs: list = []
        self._tariff = {'model_code':'0001','sharp':5.0,'peak':4.0,'flat':3.0,'valley':2.0,'service_fee':0.4,'loss_ratio':0.0}

    def log(self, direction:str, frame_type:int, pile_code:str='', summary:str='', raw_hex:str='') -> None:
        self._logs.insert(0, {'time':time.time(),'direction':direction,'frame_type':f'0x{frame_type:02X}','pile_code':pile_code,'summary':summary,'raw_hex':raw_hex})
        del self._logs[300:]

    def logs(self, limit:int=100) -> list: return list(self._logs[:max(1,min(limit,300))])
    def tariff(self) -> dict: return dict(self._tariff)

    def upsert_login(self, info: dict, peer: str) -> DeviceState:
        code=info['pile_code']; dev=self._devices.get(code) or DeviceState(pile_code=code,peer=peer)
        dev.peer=peer; dev.pile_type=info.get('pile_type',-1); dev.gun_count=info.get('gun_count',0); dev.protocol_version=info.get('protocol_version',0.0); dev.program_version=info.get('program_version',''); dev.network_type=info.get('network_type',-1); dev.touch(0x01); self._devices[code]=dev
        return dev

    def touch(self, pile_code: str, frame_type: int) -> Optional[DeviceState]:
        dev=self._devices.get(pile_code)
        if dev: dev.touch(frame_type)
        return dev

    def update_realtime(self, info: dict) -> Optional[DeviceState]:
        dev=self._devices.get(info['pile_code'])
        if not dev: return None
        dev.realtime=dict(info); dev.realtime['updated_at']=time.time()
        txid=info.get('transaction_id','')
        if txid and txid.strip('0'): dev.transaction_id=txid
        if info.get('work_status') == 3: dev.charge_state='charging'
        elif info.get('work_status') in (0,1,2) and dev.charge_state not in ('starting','stopping'): dev.charge_state='idle'
        dev.touch(0x13)
        if txid and txid.strip('0'):
            tx=self._transactions.setdefault(txid, {'transaction_id':txid,'pile_code':dev.pile_code,'gun_no':info.get('gun_no','01'),'status':'charging','started_at':time.time()})
            tx.update({'status':'charging' if info.get('work_status')==3 else tx.get('status','idle'),'soc_pct':info.get('soc_pct'),'energy_kwh':info.get('energy_kwh'),'amount_yuan':info.get('amount_yuan'),'updated_at':time.time()})
        return dev

    def control_sent(self,pile_code:str,frame_type:int,transaction_id:str,raw_hex:str) -> None:
        dev=self._devices.get(pile_code)
        if dev:
            dev.transaction_id=transaction_id; dev.last_control={'frame_type':frame_type,'transaction_id':transaction_id,'time':time.time(),'raw_hex':raw_hex}; dev.touch(frame_type)
            if frame_type==0x34: dev.charge_state='starting'
            elif frame_type==0x36: dev.charge_state='stopping'
        if frame_type==0x34:
            self._transactions[transaction_id]={'transaction_id':transaction_id,'pile_code':pile_code,'gun_no':'01','status':'starting','started_at':time.time()}
        elif frame_type==0x36 and transaction_id in self._transactions:
            self._transactions[transaction_id]['status']='stopping'; self._transactions[transaction_id]['updated_at']=time.time()

    def start_reply(self,info:dict) -> None:
        dev=self._devices.get(info['pile_code'])
        if dev: dev.charge_state='charging' if info['result']==1 else 'idle'; dev.transaction_id=info['transaction_id']; dev.touch(0x33)
        tx=self._transactions.setdefault(info['transaction_id'],dict(info)); tx.update(info); tx['status']='charging' if info['result']==1 else 'start_failed'; tx['updated_at']=time.time()

    def stop_reply(self,info:dict) -> None:
        dev=self._devices.get(info['pile_code'])
        if dev: dev.charge_state='stopping' if info['result']==1 else 'charging'; dev.touch(0x35)
        tx=self._transactions.setdefault(info['transaction_id'],dict(info)); tx.update(info); tx['status']='stopped' if info['result']==1 else 'stop_failed'; tx['updated_at']=time.time()

    def transaction_record(self,info:dict) -> None:
        tx=self._transactions.setdefault(info['transaction_id'],dict(info)); tx.update(info); tx['status']='completed'; tx['completed_at']=time.time()
        dev=self._devices.get(info['pile_code'])
        if dev: dev.charge_state='idle'; dev.transaction_id=''; dev.touch(0x3B)

    def transactions(self) -> list: return sorted(self._transactions.values(),key=lambda x:x.get('started_at',x.get('updated_at',0)),reverse=True)

    def mark_offline_by_peer(self, peer: str) -> None:
        for dev in self._devices.values():
            if dev.peer==peer: dev.online=False

    def get(self,pile_code:str)->Optional[dict]:
        dev=self._devices.get(pile_code); return asdict(dev) if dev else None
    def realtime(self,pile_code:str)->Optional[dict]:
        dev=self._devices.get(pile_code); return dict(dev.realtime) if dev and dev.realtime else None
    def all(self)->list:
        now=time.time(); result=[]
        for dev in self._devices.values():
            if dev.online and now-dev.last_seen>35: dev.online=False
            result.append(asdict(dev))
        return result


registry=DeviceRegistry()
