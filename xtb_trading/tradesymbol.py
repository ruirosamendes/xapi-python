import pandas as pd
from xapi import Socket, TradeCmd, TradeType, TradeStatus

class Symbol:
    def __init__(self, socket: Socket, symbol:str):
        self.socket = socket
        self.symbol = symbol

    async def __return_order_status(self, order:int):
        """Return roder status"""
        response = await self.socket.tradeTransactionStatus(order)
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

    async def get_data(self):
        response = await self.socket.getSymbol(self.symbol)
        symbol_data = None
        if response['status'] is True:
            data = pd.json_normalize(response['returnData'])
            symbol_data = data[["symbol", "description", "categoryName", "currency", "bid","ask", "time"]]
        else:
            symbol_data = None
            print("Failed to get symbol", response)
        return symbol_data
    
    async def open_sell_stop_order(self, volume:int, sell_stop_price:float, custom_comment:str):
        """Open a new set stop order."""
        response = await self.socket.tradeTransaction(
                        symbol=self.symbol,
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
        return await self.__return_order_status(order)

    async def modify_sell_stop_order(self, order:int, volume:int, sell_stop_price:float, custom_comment:str):
        """Modify an existent set stop order."""
        response = await self.socket.tradeTransaction(
                        symbol=self.symbol,
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
        return await self.__return_order_status(order)