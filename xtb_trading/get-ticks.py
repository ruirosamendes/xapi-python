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
            symbol_prices = pd.DataFrame(columns=["symbol","ask","bid","low","high", "askVolume","bidVolume","spreadRaw","rsi"])
            async with await xapi.connect(**credentials) as x:
                await x.stream.getTickPrices(symbol, 1)

                async for message in x.stream.listen():              
                    data = pd.json_normalize(message['data'])
                    
                    # RSI com os tick prices e ver divergências!## de ALTA ou de BAIXA!
                    # mais regra do risco retorno (MAX 2%)  de todo o capital em risco (youtube)
                    # Sinal de compra: RSI > 30 
                    # Sinal de Venda: RSI < 70                                                        
                    tick_prices = data[["symbol","ask","bid","low", "high", "askVolume","bidVolume","spreadRaw"]]
                    symbol_prices = pd.concat([symbol_prices, tick_prices], ignore_index=True)
                    symbol_prices["rsi"] = ta.rsi(symbol_prices["bid"], length=14)                    
                    print(symbol_prices)
                    

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