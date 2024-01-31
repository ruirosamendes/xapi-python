import logging
import asyncio
import json
import time
import pandas as pd
import xapi
from xapi import Socket, TradeCmd, TradeType, TradeStatus

logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    CREDENTIALS = json.load(f)


async def return_order_status(socket: Socket, order:int):
    """Return roder status"""
    response = await socket.tradeTransactionStatus(order)
    if response['status'] is not True: 
        print("Failed to trade a transaction", response)
        return response
    request_status = response['returnData']['requestStatus']
    if request_status == TradeStatus.ERROR.value:
        print(f"The transaction finished with error: {response['returnData']['message']}")
    elif request_status == TradeStatus.PENDING.value:
        print("The transaction is pending")
    elif request_status == TradeStatus.ACCEPTED.value:
        print("The transaction has been executed successfully")
    elif request_status == TradeStatus.REJECTED.value:
        print(f"The transaction has been rejected: {response['returnData']['message']}")
    return response


async def open_sell_stop_order(socket: Socket, symbol:str, volume:int, 
                               sell_stop_price:float, custom_comment:str):
    """Open a new set stop order."""
    response = await socket.tradeTransaction(
                    symbol=symbol,
                    cmd=TradeCmd.SELL_STOP,
                    type=TradeType.OPEN,
                    order=0,
                    price=sell_stop_price,
                    volume=volume,
                    customComment=custom_comment
                )
    if response['status'] is not True:
        print("Failed to trade a transaction", response)
        return response
    order = response['returnData']['order']
    return await return_order_status(socket, order)
    
async def modify_sell_stop_order(socket: Socket, order:int, symbol:str, volume:int,
                               sell_stop_price:float, custom_comment:str):
    """Modify an existent set stop order."""
    response = await socket.tradeTransaction(
                    symbol=symbol,
                    cmd=TradeCmd.SELL_STOP,
                    type=TradeType.MODIFY,
                    order=order,
                    price=sell_stop_price,
                    volume=volume,
                    customComment=custom_comment
                )
    if response['status'] is not True:
        print("Failed to trade a transaction", response)
        return
    order = response['returnData']['order']
    return await return_order_status(socket, order)

async def set_sell_stop_price(socket: Socket, symbol: str, percentage: int, commit: bool = False):
    """Calculate Sell Stop and set it."""
    # Calculate Sell Stop    
    response = await socket.getTrades(True)
    if response['status'] is True:
        trade_records = response['returnData']
        data = pd.json_normalize(trade_records)        
        buy_trade_records = data[["order", "symbol","volume","open_price","close_price","profit","open_timeString","nominalValue","cmd","position"]].query("cmd==0 and symbol == @symbol")
        print(buy_trade_records)
        symbol = buy_trade_records["symbol"].values[0]
        open_price = buy_trade_records["open_price"].values[0]
        close_price = buy_trade_records["close_price"].values[0]
        buy_volume = buy_trade_records["volume"].values[0]
        reference_price = open_price
        # Chose close price as reference if close price is higher
        # than open price and negative percentage requested
        if ((percentage < 0) and (close_price > open_price)):
            reference_price = close_price        
        sell_stop_price = round(reference_price * (1 + percentage/100),1)
        print("Symbol: " + symbol)
        print("Reference Price: " + str(reference_price))
        print("Volume: " + str(buy_volume))
        print("Sell Stop Price: " + str(sell_stop_price))
        if percentage < 0:
            custom_comment = "Minus " + str(percentage)
        else:
            custom_comment = "Plus " + str(percentage)
        custom_comment = custom_comment + "%, price: " + str(sell_stop_price)
        print(custom_comment + "\n")
        sell_stop_trades = data[["order", "symbol", "volume", "open_price", "cmd"]].query("cmd==5 and symbol == @symbol")
        # Is there any Sell Stop orders for this symbol?
        if(len(sell_stop_trades) > 0):
            print(sell_stop_trades) 
            # Update them
            for index, row in sell_stop_trades.iterrows():
                sell_stop_order = row["order"]
                sell_stop_symbol = row["symbol"]
                sell_stop_volume = row["volume"]                
                # user_input = input("Do you update current sell stop order:" + str(sell_stop_order) + "? ")
                # if user_input.lower() == 'yes': 
                if (commit):
                    # Modify sell stop order!
                    print("Modify sell stop order: " + str(sell_stop_order) + "\n")
                    await modify_sell_stop_order(socket, sell_stop_order, sell_stop_symbol, sell_stop_volume, sell_stop_price, custom_comment)                    
                else:
                    print("Sell stop order: " + str(sell_stop_order) + " not modified\n")
        else:
            # Confirm sell stop order
            # user_input = input("Do you want to order the sell stop: " + custom_comment +  "? ")
            # if user_input.lower() == 'yes':
            if (commit):
                print("Opening sell stop order\n")
                # Set sell Stops!
                await open_sell_stop_order(socket, symbol, buy_volume, sell_stop_price, custom_comment)                
            else:                
                print("No sell stop ordered\n")
        return    
    else:
        print("Failed to get trade records", response)
        return
    
async def set_open_positions_sell_stop_price(percentage:int, commit:bool = False):
    """Set the sell stop_price all open positions."""
    try:
        async with await xapi.connect(**CREDENTIALS) as x:
            response = await x.socket.getTrades(True)
            if response['status'] is True:
                trade_records = response['returnData']
                data = pd.json_normalize(trade_records)        
                buy_trade_records = data[["order", "symbol","cmd"]].query("cmd==0")
                for index, row in buy_trade_records.iterrows():
                    await set_sell_stop_price(x.socket, row["symbol"], percentage, commit)
                    time.sleep(15)
            else:
                print("Failed to get trade records", response)
                return
            # await set_sell_stop_price(x.socket, "IFX.DE_9", -5, True)
            # await set_sell_stop_price(x.socket, "BBVA.ES_9", -5, True)
            # await set_sell_stop_price(x.socket, "STLAM.IT", -5, True)
            # await set_sell_stop_price(x.socket, "VAR1.DE_9", -5, True)
            # await set_sell_stop_price(x.socket, "MBG.DE_9", -5, True)
            # await set_sell_stop_price(x.socket, "IFX.DE_9", -5, True)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

async def main():
    """Main."""
    await set_open_positions_sell_stop_price(-2, True)

if __name__ == "__main__":
    asyncio.run(main())
