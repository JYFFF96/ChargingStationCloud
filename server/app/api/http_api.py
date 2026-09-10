from pathlib import Path
import itertools

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.protocol.ykc import build_remote_start_34, build_remote_stop_36, make_transaction_id, parse_frame
from app.services.device_registry import registry
from app.services.control_hub import hub

app=FastAPI(title='ChargingStationCloud',version='1.0.0-rc1')
_tx_serial=itertools.count(1)


class StartRequest(BaseModel):
    pile_code:str
    gun_no:str='01'
    logical_card:str='0000000000000000'
    physical_card:str='0000000000000000'
    balance_yuan:float=Field(default=1000.0,ge=0)


class StopRequest(BaseModel):
    pile_code:str
    gun_no:str='01'
    transaction_id:str|None=None


class VerifyRequest(BaseModel):
    hex_frame:str


@app.get('/health')
def health(): return {'ok':True,'version':'1.0.0-rc1'}

@app.get('/api/devices')
def devices(): return {'items':registry.all()}

@app.get('/api/devices/{pile_code}/realtime')
def realtime(pile_code:str):
    if not registry.get(pile_code): raise HTTPException(404,'device not found')
    data=registry.realtime(pile_code)
    if not data: raise HTTPException(404,'realtime data not available')
    return data

@app.get('/api/devices/{pile_code}')
def device(pile_code:str):
    item=registry.get(pile_code)
    if not item: raise HTTPException(404,'device not found')
    return item

@app.post('/api/charge/start')
def charge_start(req:StartRequest):
    dev=registry.get(req.pile_code)
    if not dev: raise HTTPException(404,'device not found')
    if not hub.online(req.pile_code): raise HTTPException(409,'device offline')
    txid=make_transaction_id(req.pile_code,req.gun_no,next(_tx_serial))
    try:
        sent=hub.send_raw_builder(req.pile_code,lambda seq:build_remote_start_34(seq,txid,req.pile_code,req.gun_no,req.logical_card,req.physical_card,req.balance_yuan))
    except Exception as exc: raise HTTPException(500,str(exc))
    registry.control_sent(req.pile_code,0x34,txid,sent['raw_hex']); registry.log('down',0x34,req.pile_code,f'远程启机 tx={txid}',sent['raw_hex'])
    return {'ok':True,'transaction_id':txid,**sent}

@app.post('/api/charge/stop')
def charge_stop(req:StopRequest):
    dev=registry.get(req.pile_code)
    if not dev: raise HTTPException(404,'device not found')
    if not hub.online(req.pile_code): raise HTTPException(409,'device offline')
    txid=req.transaction_id or dev.get('transaction_id')
    if not txid: raise HTTPException(409,'no active transaction')
    try:
        sent=hub.send_raw_builder(req.pile_code,lambda seq:build_remote_stop_36(seq,txid,req.pile_code,req.gun_no))
    except Exception as exc: raise HTTPException(500,str(exc))
    registry.control_sent(req.pile_code,0x36,txid,sent['raw_hex']); registry.log('down',0x36,req.pile_code,f'远程停机 tx={txid}',sent['raw_hex'])
    return {'ok':True,'transaction_id':txid,**sent}

@app.get('/api/transactions')
def transactions(): return {'items':registry.transactions()}

@app.get('/api/logs')
def logs(limit:int=100): return {'items':registry.logs(limit)}

@app.get('/api/tariff')
def tariff(): return registry.tariff()

@app.post('/api/protocol/verify')
def verify(req:VerifyRequest):
    try:
        raw=bytes.fromhex(req.hex_frame.replace('0x','').replace(',',' ')); f=parse_frame(raw,verify_crc=True)
        return {'ok':True,'seq':f.seq,'encrypted':f.encrypted,'frame_type':f'0x{f.frame_type:02X}','body_len':len(f.body),'raw_hex':raw.hex(' ').upper()}
    except Exception as exc: return {'ok':False,'error':str(exc)}


WEB_DIR=Path(__file__).resolve().parents[3]/'web'
if WEB_DIR.exists(): app.mount('/web',StaticFiles(directory=str(WEB_DIR),html=True),name='web')

@app.get('/')
def root(): return RedirectResponse('/web/')
