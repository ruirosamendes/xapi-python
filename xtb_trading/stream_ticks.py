import logging
from datetime import datetime as dt
import pandas as pd
import asyncio
import json
import xapi
from set_rsi import set_rsi

logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    credentials = json.load(f)

async def main():
    while True:
        try:
            symbol = "PLTR.US_9"
            symbol_prices = pd.DataFrame(columns=["symbol","ask","bid","low","high", "askVolume","bidVolume","spreadRaw","timestamp","datetime","rsiM1","signal"])
            now = dt.now() # current date and time
            date_time_str = now.strftime("%Y%m%d_%H%M%S")
            filename = symbol + "_ticks_" + date_time_str + ".csv"
            print(filename)        
            async with await xapi.connect(**credentials) as x:
                await x.stream.getTickPrices(symbol)
                current_ticks_data = None
                async for message in x.stream.listen():
                    data = pd.json_normalize(message['data'])
                    
                    raw_ticks_data = data[["symbol","ask","bid"]]
                    if(raw_ticks_data.equals(current_ticks_data)):
                        print("EQUAL TICKS PRICES continue")    
                        continue
                    else:   
                        current_ticks_data = raw_ticks_data
                        print("DIFFERENT TICKS PRICES")


                    ticks_data = data[["symbol","ask","bid","low","high","askVolume","bidVolume","spreadRaw", "timestamp"]]
                    datetime = dt.fromtimestamp(ticks_data["timestamp"][0]/1000)
                    ticks_data.insert(9, "datetime", datetime)
                    symbol_prices = pd.concat([symbol_prices, ticks_data], ignore_index=True)                    
                    set_rsi(symbol_prices, "ask", 7, 70, 30)
                    print(symbol_prices.tail(1))
                    symbol_prices.tail(1).to_csv(filename, mode='a', header=False, index=False)
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