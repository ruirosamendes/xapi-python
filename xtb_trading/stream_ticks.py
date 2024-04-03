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
            symbol = "BITCOIN"
            symbol_prices = pd.DataFrame(columns=["symbol","ask","bid","low","high", "askVolume","bidVolume","spreadRaw","timestamp","datetime","rsiM1","signal"])
            now = dt.now() # current date and time
            date_time_str = now.strftime("%Y%m%d_%H%M%S")
            filename = symbol + "_ticks_" + date_time_str + ".csv"
            print(filename)        
            async with await xapi.connect(**credentials) as x:
                await x.stream.getTickPrices(symbol)

                async for message in x.stream.listen():
                    data = pd.json_normalize(message['data'])
                    tick_prices = data[["symbol","ask","bid","low","high","askVolume","bidVolume","spreadRaw", "timestamp"]]
                    datetime = dt.fromtimestamp(tick_prices["timestamp"][0]/1000)
                    tick_prices.insert(9, "datetime", datetime)

                    # RSI com os tick prices e ver divergências!## de ALTA ou de BAIXA!
                    # mais regra do risco retorno (MAX 2%)  de todo o capital em risco (youtube)
                    # Sinal de compra: RSI > 30
                    # Sinal de Venda: RSI < 70
                    rsi_period = 5
                    symbol_prices = pd.concat([symbol_prices, tick_prices], ignore_index=True)
                    symbol_prices["rsiM1"] = ta.rsi(symbol_prices["bid"], length=rsi_period)
                    last_price = symbol_prices.tail(1)
        
                    # sell signal
                    sell_rsi = 80
                    filter_sell = (symbol_prices["rsiM1"].shift(1) < sell_rsi) & (last_price["rsiM1"] > sell_rsi)
                    print(filter_sell.tail(rsi_period))


                    if(filter_sell.tail(rsi_period).any()):
                        print ("Sell signal")
                        print ("above " + str(sell_rsi))
                        print("RSI: " + str(last_price["rsiM1"].iloc[0]))
                        print("ASK: " + str(last_price["ask"].iloc[0]))
                        symbol_prices.loc[symbol_prices.index[-1], "signal"] = "SELL"
                    else:
                        print ("No sell signal")
                        # print ("below " + str(sell_rsi))
                        # print("RSI: " + str(last_price["rsiM1"].iloc[0]))
                        # print("ASK: " + str(last_price["ask"].iloc[0]))
                        symbol_prices.loc[symbol_prices.index[-1], "signal"] = "HOLD"
                    # buy signal
                    buy_rsi = 20
                    filter_buy = (symbol_prices["rsiM1"].shift(1) > buy_rsi) & (last_price["rsiM1"] < buy_rsi)
                    print(filter_buy.tail(rsi_period))
                    # last_price = symbol_prices.tail(1)
                    if(filter_buy.tail(rsi_period).any()):
                        print ("Buy signal")
                        print ("below " + str(buy_rsi))
                        print("RSI: " + str(last_price["rsiM1"].iloc[0]))
                        print("ASK: " + str(last_price["ask"].iloc[0]))
                        symbol_prices.loc[symbol_prices.index[-1], "signal"] = "BUY"
                    else:
                        print ("No buy signal")
                        # print ("Above " + str(buy_rsi))
                        # print("RSI: " + str(last_price["rsiM1"].iloc[0]))
                        # print("ASK: " + str(last_price["ask"].iloc[0]))
                        symbol_prices.loc[symbol_prices.index[-1], "signal"] = "HOLD"
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