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
            response = await x.socket.getTrades()
            if response['status'] == True:
                trades = response['returnData']
                data = pd.json_normalize(trades)
                print(data)
                # print(data.columns.values)
                openPositions = data[["symbol","volume","sl","tp","open_price","close_price","profit","open_timeString","nominalValue","commission","margin_rate","spread","closed","taxes","storage"]].sort_values("symbol")                                
                openPositions.insert(2, "market_value", 0.0)
                openPositions["market_value"] = round(openPositions["nominalValue"] + openPositions["profit"], 2)
                # now = dt.now() # current date and time
                # dateTimeStr = now.strftime("%Y%m%d_%H%M%S")
                # filename = "MyTrades_" + dateTimeStr + ".csv"
                #print(filename)
                filename = "MyTrades.csv"                                
                openPositions.to_csv(filename)  
                print(openPositions)              
            else:
                print("Failed to get trades", response)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())