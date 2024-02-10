import logging
import asyncio
import json
import xapi
import pandas as pd
from xapi import Socket
from datetime import datetime as dt

logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    CREDENTIALS = json.load(f)


# start from the first day of a current year
START = round(dt.today().replace(month=1, day=1).timestamp() * 1000)


async def get_symbol_data(socket: Socket, symbol:str):
    response = await socket.getSymbol(symbol)
    if response['status'] is True:
        data = pd.json_normalize(response['returnData'])
        symbolData = data[["symbol", "description", "categoryName", "currency", "bid","ask", "time"]]
    else:
        symbolData = None
        print("Failed to get symbol", response)
    return symbolData

async def main():
    try:
        async with await xapi.connect(**CREDENTIALS) as x:
            response = await x.socket.getTradesHistory(START)
            if response['status'] == True:
                trades = response['returnData']
                data = pd.json_normalize(trades)
                print(data.columns.values)
                closedTrades = data[["order", "symbol","volume","open_price","close_price","profit","open_time","close_time", "nominalValue","cmd"]]
                closedTrades.insert(10, "opened_days", 0)
                closedTrades["opened_days"] = round(((closedTrades["close_time"] - closedTrades["open_time"]) / 86400000), 1)
                closedTrades.insert(11, "description", "")
                closedTrades.insert(12, "category", "")
                closedTrades.insert(13, "currency", "")
                closedTrades.insert(14, "current_ask", 0.0)
                closedTrades.insert(15, "current_bid", 0.0)
                closedTrades.insert(16, "current_time", 0)
                
                # Update current  bid, ask  and timeString
                for index, row in closedTrades.iterrows():
                    symbol_data = await get_symbol_data(x.socket, row["symbol"])
                    closedTrades.at[index, "description"] = symbol_data["description"].loc[0]
                    closedTrades.at[index, "category"] = symbol_data["categoryName"].loc[0]
                    closedTrades.at[index, "currency"] = symbol_data["currency"].loc[0]
                    closedTrades.at[index, "current_ask"] = round(symbol_data["ask"].loc[0],3)
                    closedTrades.at[index, "current_bid"] = round(symbol_data["bid"].loc[0],3)
                    closedTrades.at[index, "current_time"] = symbol_data["time"].loc[0]
                    
                closedTrades.insert(17, "afterclosing_days", 0)           
                closedTrades["afterclosing_days"] = round(((closedTrades["current_time"] - closedTrades["close_time"]) / 86400000), 1)
                closedTrades.insert(18, "potential_profit", 0)
                closedTrades["potential_profit"] = round((closedTrades["current_ask"] * closedTrades["volume"]) - (closedTrades["open_price"] * closedTrades["volume"]), 2)
                closedTrades.insert(19, "open_date", 0)
                closedTrades["open_date"] = pd.to_datetime(closedTrades["open_time"], unit='ms')
                closedTrades.insert(20, "close_date", 0)
                closedTrades["close_date"] = pd.to_datetime(closedTrades["close_time"], unit='ms')
                closedTrades.insert(21, "current_date", 0)
                closedTrades["current_date"] = pd.to_datetime(closedTrades["current_time"], unit='ms')
                closedTrades.insert(22, "profit_percentage", 0)
                closedTrades["profit_percentage"] = round((closedTrades["profit"] / (closedTrades["open_price"] * closedTrades["volume"])) * 100, 2)
                closedTrades.insert(23, "potential_profit_percentage", 0)
                closedTrades["potential_profit_percentage"] = round((closedTrades["potential_profit"] /(closedTrades["open_price"] * closedTrades["volume"])) * 100, 2)

                print (closedTrades)                   
                # now = dt.now() # current date and time
                # dateTimeStr = now.strftime("%Y%m%d_%H%M%S")
                # filename = "MyTrades_" + dateTimeStr + ".csv"
                # print(filename)
                filename = "ClosedTrades.csv"
                closedTrades.to_csv(filename)
            else:
                print("Failed to get trades history", response)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())