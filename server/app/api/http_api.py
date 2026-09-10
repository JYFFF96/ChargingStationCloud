from fastapi import FastAPI, HTTPException
from app.services.device_registry import registry

app = FastAPI(title='ChargingStationCloud', version='0.1.0')


@app.get('/health')
def health():
    return {'ok': True, 'version': '0.1.0'}


@app.get('/api/devices')
def devices():
    return {'items': registry.all()}


@app.get('/api/devices/{pile_code}')
def device(pile_code: str):
    item = registry.get(pile_code)
    if not item:
        raise HTTPException(status_code=404, detail='device not found')
    return item
