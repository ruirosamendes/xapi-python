from trade_symbol import Symbol
from datetime import datetime as dt
import pandas as pd
import pandas_ta as ta


async def buy_sell_with_rsi(symbol:Symbol, investment:int, commit:bool, prices:pd.DataFrame, ref_price_str:str, rsi_period = 14, sell_rsi = 70, buy_rsi = 30):
    # RSI com os tick prices e ver divergências!## de ALTA ou de BAIXA!
    # mais regra do risco retorno (MAX 2%)  de todo o capital em risco (youtube)
    # Sinal de compra: RSI > 30 
    # Sinal de Venda: RSI < 70                                                                                                       
    prices["rsiM1"] = ta.rsi(prices[ref_price_str], length=rsi_period)                                             
    last_price = prices.tail(1)                                     
    has_signal = False                    
    filter_sell = (prices["rsiM1"].shift(1) < sell_rsi) & (last_price["rsiM1"] > sell_rsi)
    print(filter_sell.tail(rsi_period))                    
    if(filter_sell.tail(rsi_period).any()):                    
        print ("Sell signal")
        print ("above " + str(sell_rsi))                            
        print("RSI: " + str(last_price["rsiM1"].iloc[0]))
        print(ref_price_str + ":" + str(last_price[ref_price_str].iloc[0]))                                                      
        prices.loc[prices.index[-1], "signal"] = "SELL"        
        symbol_data = await symbol.get_data()
        prices.loc[prices.index[-1], "signal_price"] = symbol_data["bid"].loc[0]
        print(symbol_data)
         # Is there any position open?
        buy_positions = await symbol.get_buy_positions()
        if(len(buy_positions) > 0):
            print("Set sell stop prices to quickly close open buy position.")
            await symbol.set_sell_stop_price_to_close(commit)
        else:
            print("There are no buy open positions to close")
            
        has_signal = True
    else:                            
        print ("No sell signal")
        prices.loc[prices.index[-1], "signal"] = "HOLD"
    # Let's check if we have a buy signal
    if(not has_signal):
        # buy signal        
        filter_buy = (prices["rsiM1"].shift(1) > buy_rsi) & (last_price["rsiM1"] < buy_rsi)                                        
        if(filter_buy.tail(rsi_period).any()):
            print ("Buy signal")
            print ("below " + str(buy_rsi))                            
            print("RSI: " + str(last_price["rsiM1"].iloc[0]))
            print(ref_price_str + ":" + str(last_price[ref_price_str].iloc[0]))  
            prices.loc[prices.index[-1], "signal"] = "BUY"
            symbol_data = await symbol.get_data()                
            prices.loc[prices.index[-1], "signal_price"] = symbol_data["ask"].loc[0]
            print(symbol_data)            
            # Is there any position open?
            buy_positions = await symbol.get_buy_positions()
            if(len(buy_positions) > 0):
                print("There are already open positions. We will not open a new one.")
            else:
                print("There are no open positions. We will open a new one.")
                await symbol.open_short_buy(investment, commit)            
        else:                            
            print ("No buy signal")                        
            prices.loc[prices.index[-1], "signal"] = "HOLD"
