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
            symbol = "BITCOIN"
            now = dt.now() # current date and time
            date_time_str = now.strftime("%Y%m%d_%H%M%S")
            filename = symbol + "_candles_" + date_time_str + ".csv"
            print(filename)            
            async with await xapi.connect(**credentials) as x:
                await x.stream.getCandles(symbol)

                async for message in x.stream.listen():
                    data = message['data']
                    minute_data = pd.json_normalize(data)
                    print(minute_data)
                    minute_data.to_csv(filename, mode='a', header=True, index=False)

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