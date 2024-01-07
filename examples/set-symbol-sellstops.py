import logging
import asyncio
import json
import xapi
from xapi import Socket, TradeCmd, TradeType, TradeStatus
import pandas as pd

logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    CREDENTIALS = json.load(f)


#     buy_order      symbol  market_value  buy_volume  buy_open_price  close_price  profit               open_timeString  nominalValue    position  sell_stop_order  sell_stop_volume  sell_stop_open_price
# 1  1181731000   BAYN.DE_9        987.84        28.0          34.635        35.28   18.06  Wed Jan 03 10:24:10 CET 2024        969.78  1181731000       1181735830              28.0                31.125
# 0  1183943868   CSCO.US_9        910.83        20.0          50.080        50.07   -7.63  Thu Jan 04 16:25:55 CET 2024        918.46  1183943868       1183960445              20.0                45.550
# 2  1185646856    DIS.US_9        991.81        12.0          90.570        90.87   -5.41  Fri Jan 05 18:23:05 CET 2024        997.22  1185646856       1185760054              12.0                82.600
# 4  1177105528  GOOGC.US_9        124.93         1.0         143.060       137.35   -4.87  Wed Dec 27 15:30:41 CET 2023        129.80  1177105528       1185756194               1.0               130.000
# 3  1185747057   SMCI.US_9        796.31         3.0         294.000       291.83  -12.98  Fri Jan 05 19:47:10 CET 2024        809.29  1185747057       1185750074               1.0               271.800
    


async def SetSellStop(socket: Socket, position: str, percentage: int):
    response = await socket.getTradeRecords([1181731000])
    if response['status'] == True:
        tradeRecords = response['returnData']
        data = pd.json_normalize(tradeRecords)
        buyTradeRecords = data[["order", "symbol","volume","open_price","close_price","profit","open_timeString","nominalValue","cmd","position"]].query("cmd==0")

        symbol = buyTradeRecords["symbol"].values[0]
        buyOpenPrice = buyTradeRecords["open_price"].values[0]
        buyVolume = buyTradeRecords["volume"].values[0]
        sellStop = round(buyOpenPrice * (1 + percentage/100),2)        
        
        print("Symbol: " + symbol)
        print("Open Price: " + str(buyOpenPrice))
        print("Volume: " + str(buyVolume))
        if percentage < 0:
            customComment = "Minus " + str(percentage) 
            print(customComment + "% : " + str(sellStop))            
        else:
            customComment = "Plus " + str(percentage) 
            print(customComment + "% : " + str(sellStop))
        
    else:
        print("Failed to get trade records", response)
    
    # # Set sell Stops!
    # response = await connection.socket.tradeTransaction(
    #         symbol="symbol",
    #         cmd=TradeCmd.SELL_STOP,
    #         type=TradeType.OPEN,
    #         order=0,
    #         price=sellStopMinus8,
    #         volume=buyVolume,
    #         customComment="-8%"
    #     )

    # if response['status'] != True:
    #     print("Failed to trade a transaction", response)
    #     return

    # order = response['returnData']['order']

    # response = await x.socket.tradeTransactionStatus(order)
    # if response['status'] != True:
    #     print("Failed to trade a transaction", response)
    #     return

    # requestStatus = response['returnData']['requestStatus']
    # if requestStatus == TradeStatus.ERROR.value:
    #     print(f"The transaction finished with error: {response['returnData']['message']}")
    # elif requestStatus == TradeStatus.PENDING.value:
    #     print(f"The transaction is pending")
    # elif requestStatus == TradeStatus.ACCEPTED.value:
    #     print(f"The transaction has been executed successfully")
    # elif requestStatus == TradeStatus.REJECTED.value:
    #     print(f"The transaction has been rejected: {response['returnData']['message']}")


async def main():
    try:
        async with await xapi.connect(**CREDENTIALS) as x:            
            position = "1181731000"            
            await SetSellStop(x.socket, position, -8)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())