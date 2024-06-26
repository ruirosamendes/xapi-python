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
            # symbol = Symbol(x.socket, "RHM.DE_9")
            # await symbol.close_short_buy(True)
            # symbol = Symbol(x.socket, "CBK.DE_9")
            #await symbol.close_short_buy(False)
            # symbol = Symbol(x.socket, "BAYN.DE_9")
            # await symbol.close_short_buy(True)
            # symbol = Symbol(x.socket, "TEF1.ES_9")
            # await symbol.close_short_buy(False)
            # symbol = Symbol(x.socket, "FTK.DE")
            # await symbol.close_short_buy(False)
            # symbol = Symbol(x.socket, "BAYN.DE_9")
            # await symbol.close_short_buy(False)
            # symbol = Symbol(x.socket, "DBK.DE_9")
            # await symbol.close_short_buy(True)
            # symbol = Symbol(x.socket, "MSF.DE_9")
            # await symbol.close_short_buy(True)
            # symbol = Symbol(x.socket, "MSFT.US_9")
            # await symbol.close_short_buy(True)
            #symbol = Symbol(x.socket, "PLTR.US_9")
            #await symbol.set_sell_stop_price_to_close(True)
            symbol = Symbol(x.socket, "ETHEREUM")
            await symbol.close_short_buy(True)      

            
                                              

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
