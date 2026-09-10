from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.services.device_registry import registry

app = FastAPI(title='ChargingStationCloud', version='0.2.0')


@app.get('/health')
def health():
    return {'ok': True, 'version': '0.2.0'}


@app.get('/api/devices')
def devices():
    return {'items': registry.all()}


@app.get('/api/devices/{pile_code}')
def device(pile_code: str):
    item = registry.get(pile_code)
    if not item:
        raise HTTPException(status_code=404, detail='device not found')
    return item


WEB_DIR = Path(__file__).resolve().parents[3] / 'web'
if WEB_DIR.exists():
    app.mount('/web', StaticFiles(directory=str(WEB_DIR), html=True), name='web')


@app.get('/')
def root():
    return RedirectResponse('/web/')
