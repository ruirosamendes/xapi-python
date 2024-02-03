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
        symbolData = data[["symbol","bid","ask",]]
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
                closedTrades.insert(11, "current_ask", 0.0)
                closedTrades.insert(12, "current_bid", 0.0)
                closedTrades.insert(13, "current_time", None)

                # Update current  bid, ask  and timeString
                for index, row in closedTrades.iterrows():
                    symbol_data = await get_symbol_data(x.socket, row["symbol"])
                    closedTrades.at[index, "current_ask"] = round(symbol_data["ask"].loc[0],3)
                    closedTrades.at[index, "current_bid"] = round(symbol_data["bid"].loc[0],3)


                print (closedTrades)


                # closedTrades["after_se"]
                #openPositions.insert(11, "sell_stop_percentage", 0.0)
                # openPositions["sell_stop_percentage"] = -(100 - round((openPositions["sell_stop_price"] / openPositions["buy_open_price"]) * 100, 2))
                # openPositions.insert(12, "sell_stop_value", 0.0)
                # openPositions["sell_stop_value"] = openPositions["sell_stop_price"] * openPositions["volume"]
                # openPositions.insert(13, "sell_stop_lost", 0.0)
                # openPositions["sell_stop_lost"] = (openPositions["buy_open_price"] * openPositions["volume"]) - openPositions["sell_stop_value"]
                # openPositions.insert(14, "alert_price_2", 0.0)
                # openPositions["alert_price_2"] =  round(openPositions["buy_open_price"] * (1 + 2/100), 2)
                # openPositions.insert(15, "alert_price_3", 0.0)
                # openPositions["alert_price_3"] =  round(openPositions["buy_open_price"] * (1 + 3/100), 2)
                # openPositions.insert(16, "alert_price_4", 0.0)
                # openPositions["alert_price_4"] =  round(openPositions["buy_open_price"] * (1 + 4/100), 2)


                # print(openPositions.sort_values("symbol",ascending=True))
                # # OUTPUT TO FILE
                # # now = dt.now() # current date and time
                # # dateTimeStr = now.strftime("%Y%m%d_%H%M%S")
                # # filename = "MyTrades_" + dateTimeStr + ".csv"
                # #print(filename)
                # # filename = "MyTrades.csv"
                # # openPositions.to_csv(filename)

            else:
                print("Failed to get trades", response)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())