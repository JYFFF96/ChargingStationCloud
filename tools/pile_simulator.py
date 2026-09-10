import argparse
import asyncio
import itertools

START_FLAG=0x68


def crc16_modbus(data:bytes)->int:
    crc=0xFFFF
    for b in data:
        crc^=b
        for _ in range(8): crc=(crc>>1)^0xA001 if crc&1 else crc>>1
    return crc&0xFFFF


def bcd(text:str,n:int)->bytes:
    s=''.join(c for c in str(text) if c.isdigit()).zfill(n*2)[-n*2:]
    return bytes((int(s[i])<<4)|int(s[i+1]) for i in range(0,len(s),2))


def bcd_decode(data:bytes)->str: return ''.join(f'{(x>>4)&15}{x&15}' for x in data)


def frame(seq:int,tp:int,body:bytes=b'')->bytes:
    payload=seq.to_bytes(2,'little')+b'\x00'+bytes([tp])+body
    return bytes([START_FLAG,len(payload)])+payload+crc16_modbus(payload).to_bytes(2,'little')


def extract(buf:bytearray):
    out=[]
    while True:
        while buf and buf[0]!=0x68: del buf[0]
        if len(buf)<2: break
        total=buf[1]+4
        if len(buf)<total: break
        out.append(bytes(buf[:total])); del buf[:total]
    return out


def body_of(raw:bytes)->bytes: return raw[6:-2]
def type_of(raw:bytes)->int: return raw[5]


class Sim:
    def __init__(self,args):
        self.args=args; self.pile=bcd(args.pile,7); self.seq=itertools.count(1); self.charging=False; self.transaction='0'*32; self.sample=0; self.writer=None
    def next_seq(self): return next(self.seq)&0xFFFF

    def realtime_body(self):
        s=self.sample; status=3 if self.charging else 2; soc=min(100,46+s) if self.charging else 46
        voltage=3990+(s%10)*2 if self.charging else 0; current=999+(s%8)*5 if self.charging else 0
        elapsed=35+s if self.charging else 0; remaining=max(0,60-elapsed) if self.charging else 0
        energy=234567+s*1250 if self.charging else 0; amount=303838+s*1600 if self.charging else 0
        return b''.join([bcd(self.transaction,16),self.pile,bcd('01',1),bytes([status]),b'\x00',b'\x01',voltage.to_bytes(2,'little'),current.to_bytes(2,'little'),bytes([90]),b'\x00'*8,bytes([soc]),bytes([85]),elapsed.to_bytes(2,'little'),remaining.to_bytes(2,'little'),energy.to_bytes(4,'little'),energy.to_bytes(4,'little'),amount.to_bytes(4,'little'),b'\x00\x00'])

    async def send(self,tp,body=b'',label='TX'):
        raw=frame(self.next_seq(),tp,body); print(f'{label:<14}',raw.hex(' ').upper()); self.writer.write(raw); await self.writer.drain(); return raw

    async def rx_loop(self,reader):
        buf=bytearray()
        while True:
            data=await reader.read(4096)
            if not data: raise ConnectionError('server closed')
            buf.extend(data)
            for raw in extract(buf):
                tp=type_of(raw); body=body_of(raw); print(f'RX 0x{tp:02X}       ',raw.hex(' ').upper())
                if tp==0x34:
                    self.transaction=bcd_decode(body[:16]); self.charging=True; self.sample=0
                    await self.send(0x33,body[:24]+b'\x01\x00','TX START ACK')
                    await self.send(0x13,self.realtime_body(),'TX REALTIME')
                elif tp==0x36:
                    self.transaction=bcd_decode(body[:16]); self.charging=False
                    await self.send(0x35,body[:24]+b'\x01\x00','TX STOP ACK')
                    await self.send(0x3B,body[:24],'TX TRANSACTION')
                elif tp==0x32:
                    self.transaction=bcd_decode(body[:16]); ok=body[-2] if len(body)>=2 else 0
                    self.charging=ok==1; print('PILE START AUTH', 'OK' if self.charging else 'FAILED',self.transaction)

    async def tx_loop(self):
        tick=0
        while True:
            await self.send(0x03,self.pile+bcd('01',1)+b'\x00','TX HEARTBEAT')
            if tick%2==0 or self.charging:
                await self.send(0x13,self.realtime_body(),'TX REALTIME')
                if self.charging: self.sample+=1
            tick+=1; await asyncio.sleep(10)

    async def pile_start_demo(self):
        await asyncio.sleep(2)
        body=self.pile+bcd('01',1)+b'\x01\x00'+bytes.fromhex('00000000D14B0A54')+b'\x00'*16+b'\x00'*17
        await self.send(0x31,body,'TX PILE START')

    async def run(self):
        reader,self.writer=await asyncio.open_connection(self.args.host,self.args.port)
        login=self.pile+bytes([self.args.type,1,0x10])+b'V1.0RC1\x00'+b'\x01'+bcd('0',10)+b'\x04'
        raw=frame(0,0x01,login); print('TX LOGIN      ',raw.hex(' ').upper()); self.writer.write(raw); await self.writer.drain()
        data=await reader.read(4096); print('RX LOGIN DATA ',data.hex(' ').upper())
        tasks=[asyncio.create_task(self.rx_loop(reader)),asyncio.create_task(self.tx_loop())]
        if self.args.pile_start: tasks.append(asyncio.create_task(self.pile_start_demo()))
        try: await asyncio.gather(*tasks)
        finally:
            self.writer.close(); await self.writer.wait_closed()


async def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--host',default='127.0.0.1'); ap.add_argument('--port',type=int,default=8768); ap.add_argument('--pile',default='32010200000001'); ap.add_argument('--type',type=int,default=1,choices=[0,1]); ap.add_argument('--pile-start',action='store_true',help='2秒后模拟桩端刷卡申请0x31')
    await Sim(ap.parse_args()).run()


if __name__=='__main__': asyncio.run(main())
