import logging
from datetime import datetime as dt
import pandas as pd
import pandas_ta as ta
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
            close_prices = pd.DataFrame(columns=["symbol","ctmString","open","close","high","low","vol","quoteId","rsi"])
            now = dt.now() # current date and time
            date_time_str = now.strftime("%Y%m%d_%H%M%S")
            filename = symbol + "_candles_" + date_time_str + ".csv"
            print(filename)            
            async with await xapi.connect(**credentials) as x:
                await x.stream.getCandles(symbol)

                async for message in x.stream.listen():                    
                    data = pd.json_normalize(message['data'])    
                    print(data)                
                    minute_data = data[["symbol","ctmString","open","close","high","low","vol","quoteId"]]                    
                    #RSI com os tick prices                       
                    # RSI com os tick prices e ver divergências!## de ALTA ou de BAIXA!
                    # mais regra do risco retorno (MAX 2%)  de todo o capital em risco (youtube)
                    # Sinal de compra: RSI > 30 
                    # Sinal de Venda: RSI < 70           
                    close_prices = pd.concat([close_prices, minute_data], ignore_index=True)                     
                    close_prices["rsi"] = ta.rsi(close_prices["close"], length=14)      
                    print(close_prices)
                    #close_prices.to_csv(filename, mode='a', header=True, index=False)

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