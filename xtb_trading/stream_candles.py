from trade_symbol import Symbol
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
    #symbol_str = "RHM.DE_9"
    symbol_str = "MSF.DE_9"            
    # symbol_str = "PLTR.US_9"
    #symbol_str = "SMCI.US_9"
    #symbol_str = "BITCOINCASH"
    now = dt.now() # current date and time
    date_time_str = now.strftime("%Y%m%d_%H%M%S")
    filename = ".\\StreamCandles\\" + symbol_str + "_candles_" + date_time_str + ".csv"
    print(filename)            
    close_prices = pd.DataFrame(columns=["symbol","ctmString","open","close","high","low","vol","quoteId", "datetime", "rsiM1","signal"])
    close_prices.to_csv(filename, mode='x', header=True, index=False)
    
    while True:
        try:                       
            async with await xapi.connect(**credentials) as x:
                await x.stream.getCandles(symbol_str)

                async for message in x.stream.listen():                    
                    data = pd.json_normalize(message['data'])    
                    print(data)                
                    minute_data = data[["symbol","ctmString","open","close","high","low","vol","quoteId"]]                                        
                    datetime_object = dt.strptime(minute_data["ctmString"].iloc[0], '%b %d, %Y, %I:%M:%S %p')                    
                    minute_data.insert(8, "datetime", datetime_object)          
                    close_prices = pd.concat([close_prices, minute_data], ignore_index=True)                                    
                    set_rsi(close_prices,"close", 14, 74, 26)
                    print(close_prices.tail(1))
                    close_prices.tail(1).to_csv(filename, mode='a', header=False, index=False)

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