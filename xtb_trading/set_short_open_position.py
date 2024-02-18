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
            #symbol = Symbol(x.socket, "DBK.DE_9")
            symbol = Symbol(x.socket, "MSF.DE_9")
            await symbol.open_short_buy(2500, True)
            
    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
