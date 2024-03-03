import logging
from datetime import datetime as dt
import pandas as pd
import asyncio
import json
import xapi

logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    credentials = json.load(f)    

async def main():
    while True:
        try:
            symbol = "BITCOINCASH"
            async with await xapi.connect(**credentials) as x:
                await x.stream.getTickPrices(symbol)

                async for message in x.stream.listen():
                    data = message['data']
                    tick_prices = pd.json_normalize(data)
                    #RSI com os tick prices
                    # minute_data.insert(2, "market_value", 0.0)
                    # minute_data["market_value"] = round(openPositions["nominalValue"] + openPositions["profit"], 2)

                    print(tick_prices)


        except xapi.LoginFailed as e:
            print(f"Log in failed: {e}")
            return

        except xapi.ConnectionClosed as e:
            print(f"Connection closed: {e}, reconnecting ...")
            await asyncio.sleep(1)
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass