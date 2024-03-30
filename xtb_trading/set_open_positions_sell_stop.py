from trade_symbol import Symbol
import logging
import asyncio
import json
import time
import pandas as pd
import xapi
from xapi import Socket


logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    CREDENTIALS = json.load(f)
    
async def set_open_positions_sell_stop_price(percentage:int, commit:bool = False):
    """Set the sell stop_price all open positions."""
    try:
        async with await xapi.connect(**CREDENTIALS) as x:
            response = await x.socket.getTrades(True)
            if response['status'] is True:
                trade_records = response['returnData']
                data = pd.json_normalize(trade_records)        
                buy_trade_records = data[["order", "symbol","cmd"]].query("cmd==0")
                for index, row in buy_trade_records.iterrows():
                    symbol = Symbol(x.socket, row["symbol"])
                    await symbol.set_sell_stop_price_by_percentage(percentage, commit)
                    time.sleep(15)
            else:
                print("Failed to get trade records", response)
                return
            # await set_sell_stop_price(x.socket, "IFX.DE_9", -5, True)
            # await set_sell_stop_price(x.socket, "BBVA.ES_9", -5, True)
            # await set_sell_stop_price(x.socket, "STLAM.IT", -5, True)
            # await set_sell_stop_price(x.socket, "VAR1.DE_9", -5, True)
            # await set_sell_stop_price(x.socket, "MBG.DE_9", -5, True)
            # await set_sell_stop_price(x.socket, "IFX.DE_9", -5, True)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

async def main():
    """Main."""
    await set_open_positions_sell_stop_price(-8, True)

if __name__ == "__main__":
    asyncio.run(main())
