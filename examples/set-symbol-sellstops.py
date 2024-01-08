import logging
import asyncio
import json
import xapi
from xapi import Socket, TradeCmd, TradeType, TradeStatus
import pandas as pd

logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    CREDENTIALS = json.load(f)

async def SetSellStop(socket: Socket, position: int, percentage: int):    
    # Calculate Sell Stop
    response = await socket.getTradeRecords([position])
    if response['status'] == True:
        tradeRecords = response['returnData']
        data = pd.json_normalize(tradeRecords)
        buyTradeRecords = data[["order", "symbol","volume","open_price","close_price","profit","open_timeString","nominalValue","cmd","position"]].query("cmd==0")

        symbol = buyTradeRecords["symbol"].values[0]
        openPrice = buyTradeRecords["open_price"].values[0]
        closePrice = buyTradeRecords["close_price"].values[0]
        buyVolume = buyTradeRecords["volume"].values[0]
        
        referencePrice = openPrice
        # Chose close price as reference if close price is higher than open price and negative percentage requested
        if ((percentage < 0) and (closePrice > openPrice)):
            referencePrice = closePrice
        
        sellStop = round(referencePrice * (1 + percentage/100),2)        
        
        print("Symbol: " + symbol)
        print("Reference Price: " + str(referencePrice))
        print("Volume: " + str(buyVolume))
        if percentage < 0:
            customComment = "Minus " + str(percentage)  
        else:
            customComment = "Plus " + str(percentage) 
        customComment = customComment + "%, price: " + str(sellStop)
        print(customComment + "\n")                
    else:
        print("Failed to get trade records", response)
    
    # Confirm sell stop order
    user_input = input("Do you want to order the sell stop: " + customComment +  "? ")

    if user_input.lower() == 'yes':
        print("Opening sell stop order\n")
        # Set sell Stops!
        response = await socket.tradeTransaction(
                symbol=symbol,
                cmd=TradeCmd.SELL_STOP,
                type=TradeType.OPEN,
                order=0,
                price=sellStop,
                volume=buyVolume,
                customComment=customComment
            )

        if response['status'] != True:
            print("Failed to trade a transaction", response)
            return

        order = response['returnData']['order']

        response = await socket.tradeTransactionStatus(order)
        if response['status'] != True:
            print("Failed to trade a transaction", response)
            return

        requestStatus = response['returnData']['requestStatus']
        if requestStatus == TradeStatus.ERROR.value:
            print(f"The transaction finished with error: {response['returnData']['message']}")
        elif requestStatus == TradeStatus.PENDING.value:
            print(f"The transaction is pending")
        elif requestStatus == TradeStatus.ACCEPTED.value:
            print(f"The transaction has been executed successfully")
        elif requestStatus == TradeStatus.REJECTED.value:
            print(f"The transaction has been rejected: {response['returnData']['message']}")
    
    else:
        print("NO sell stop ordered\n")   


async def main():
    try:
        async with await xapi.connect(**CREDENTIALS) as x:            
            position = 1177105528            
            await SetSellStop(x.socket, position, -8)
            await SetSellStop(x.socket, position, 16)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())