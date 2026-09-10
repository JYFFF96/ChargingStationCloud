import asyncio
import logging
import threading

import uvicorn

from app.api.http_api import app
from app.tcp_server.server import YKCTCPServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')


def run_http():
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')


async def main():
    threading.Thread(target=run_http, daemon=True).start()
    await YKCTCPServer(host='0.0.0.0', port=8768).start()


if __name__ == '__main__':
    asyncio.run(main())
