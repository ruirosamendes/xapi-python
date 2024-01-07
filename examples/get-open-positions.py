import logging
import asyncio
import json
import xapi
import pandas as pd

logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    CREDENTIALS = json.load(f)

# start from the first day of a current year
from datetime import datetime as dt

async def main():
    try:
        async with await xapi.connect(**CREDENTIALS) as x:
            response = await x.socket.getTrades(False)
            if response['status'] == True:
                trades = response['returnData']
                data = pd.json_normalize(trades)                              
                print(data.columns.values)
                                
                buyTrades = data[["order", "symbol","volume","open_price","close_price","profit","open_timeString","nominalValue","cmd","position"]].query("cmd==0")
                print(buyTrades)              
                
                sellStopTrades = data[["order", "symbol","volume","open_price","cmd"]].query("cmd==5")
                print(sellStopTrades)              
                                
                openPositions = pd.merge(buyTrades, sellStopTrades, "inner", "symbol").drop(columns=["cmd_x", "cmd_y"])
                openPositions = openPositions.rename(columns={"order_x":"buy_order","volume_x":"buy_volume","open_price_x":"buy_open_price","order_y":"sell_stop_order","volume_y":"sell_stop_volume","open_price_y":"sell_stop_open_price"})                         
                openPositions.insert(2, "market_value", 0.0)
                openPositions["market_value"] = round(openPositions["nominalValue"] + openPositions["profit"], 2)
                
                                            
                print(openPositions.sort_values("symbol",ascending=True))              
                # OUTPUT TO FILE
                # now = dt.now() # current date and time
                # dateTimeStr = now.strftime("%Y%m%d_%H%M%S")
                # filename = "MyTrades_" + dateTimeStr + ".csv"
                #print(filename)
                # filename = "MyTrades.csv"                                
                # openPositions.to_csv(filename)  
                
            else:
                print("Failed to get trades", response)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())