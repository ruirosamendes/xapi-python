from trade_symbol import Symbol
import logging
import asyncio
import json
import pandas as pd
import xapi


logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    CREDENTIALS = json.load(f)
    
async def main():
    try:
        async with await xapi.connect(**CREDENTIALS) as x:            
            # symbol = Symbol(x.socket, "PLTR.US_9")
            # await symbol.open_short_buy(1000, True)
            # symbol = Symbol(x.socket, "RHM.DE_9")
            # await symbol.open_short_buy(1000, True)
            # symbol = Symbol(x.socket, "ABI.BE_9")
            # await symbol.open_short_buy(1000, True)
            # symbol = Symbol(x.socket, "CON.DE_9")
            # await symbol.open_short_buy(1000, True)
            # symbol = Symbol(x.socket, "CBK.DE_9")
            #await symbol.open_short_buy(1000, False)
            # symbol = Symbol(x.socket, "BAYN.DE_9")
            # await symbol.open_short_buy(1000, True)
            # symbol = Symbol(x.socket, "DBK.DE_9")
            # await symbol.open_short_buy(1000, True)
            # symbol = Symbol(x.socket, "TEF1.ES_9")
            # await symbol.open_short_buy(1000, False)
            # symbol = Symbol(x.socket, "FTK.DE")
            # await symbol.open_short_buy(1000, False)
            # symbol = Symbol(x.socket, "BITCOINCASH")
            # await symbol.open_short_buy(1000, True)
            # symbol = Symbol(x.socket, "QCOM.US_9")
            # await symbol.open_short_buy(1000, False)
            # symbol = Symbol(x.socket, "ETHEREUM")
            # await symbol.open_short_buy(20000, False)
            

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
