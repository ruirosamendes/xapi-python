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
            close_prices = pd.DataFrame(columns=["symbol","ctmString","open","close","high","low","vol","quoteId", "datetime", "rsiM1","signal"])
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
                    datetime_object = dt.strptime(minute_data["ctmString"].iloc[0], '%b %d, %Y, %I:%M:%S %p')                    
                    minute_data.insert(8, "datetime", datetime_object)
                    # RSI com os tick prices e ver divergências!## de ALTA ou de BAIXA!
                    # mais regra do risco retorno (MAX 2%)  de todo o capital em risco (youtube)
                    # Sinal de compra: RSI > 30 
                    # Sinal de Venda: RSI < 70      
                    rsi_period = 7                                                                                                
                    close_prices = pd.concat([close_prices, minute_data], ignore_index=True)                          
                    close_prices["rsiM1"] = ta.rsi(close_prices["close"], length=rsi_period)                                             
                    last_price = close_prices.tail(1)                                     
                    has_signal = False                    
                     # sell signal
                    sell_rsi = 75
                    filter_sell = (close_prices["rsiM1"].shift(1) < sell_rsi) & (last_price["rsiM1"] > sell_rsi)
                    print(filter_sell.tail(rsi_period))                    
                    if(filter_sell.tail(rsi_period).any()):                    
                        print ("Sell signal")
                        print ("above " + str(sell_rsi))                            
                        print("RSI: " + str(last_price["rsiM1"].iloc[0]))
                        print("ASK: " + str(last_price["close"].iloc[0]))                                                      
                        close_prices.loc[close_prices.index[-1], "signal"] = "SELL"
                        has_signal = True
                    else:                            
                        print ("No sell signal")
                        close_prices.loc[close_prices.index[-1], "signal"] = "HOLD"

                    # Let's check if we have a buy signal
                    if(not has_signal):
                        # buy signal
                        buy_rsi = 25
                        filter_buy = (close_prices["rsiM1"].shift(1) > buy_rsi) & (close_prices["rsiM1"].tail(1) < buy_rsi)                                        
                        if(filter_buy.tail(rsi_period).any()):
                            print ("Buy signal")
                            print ("below " + str(buy_rsi))                            
                            print("RSI: " + str(last_price["rsiM1"].iloc[0]))
                            print("ASK: " + str(last_price["close"].iloc[0]))  
                            close_prices.loc[close_prices.index[-1], "signal"] = "BUY"                            
                        else:                            
                            print ("No buy signal")                        
                            close_prices.loc[close_prices.index[-1], "signal"] = "HOLD" 
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