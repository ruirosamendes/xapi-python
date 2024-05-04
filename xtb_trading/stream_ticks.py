from trade_symbol import Symbol
import logging
from datetime import datetime as dt
import pandas as pd
import asyncio
import json
import xapi
from set_rsi import buy_sell_with_rsi

logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    credentials = json.load(f)

async def main():
    # symbol_str = "PLTR.US_9"
    # symbol_str = "GOOGL.US_9"
    symbol_str = "BITCOINCASH"
    now = dt.now() # current date and time
    date_time_str = now.strftime("%Y%m%d_%H%M%S")
    filename = ".\\StreamTicks\\" + symbol_str + "_ticks_" + date_time_str + ".csv"    
    print(filename)      
    symbol_prices = pd.DataFrame(columns=["symbol","ask","bid","low","high", "askVolume","bidVolume","spreadRaw","timestamp","datetime","rsiM1","signal","signal_price"])
    symbol_prices.to_csv(filename, mode='x', header=True, index=False)
    
    while True:
        try:            
            async with await xapi.connect(**credentials) as x:
                symbol = Symbol(x.socket, symbol_str)

                await x.stream.getTickPrices(symbol_str)
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
                    await buy_sell_with_rsi(symbol, 1000, False, symbol_prices, "ask", 14, 50, 45)
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