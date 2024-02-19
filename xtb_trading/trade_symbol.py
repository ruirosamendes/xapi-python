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
            print(response['returnData'])
            data = pd.json_normalize(response['returnData'])
            symbol_data = data[["symbol", "description", "categoryName", "currency", "bid","ask", "time", "precision", "spreadRaw"]]
        else:
            symbol_data = None
            print("Failed to get symbol", response)
        return symbol_data
    
    async def __get_order_data(self, order:int):
        response = await self.socket.getTradeRecords([order])
        order_data = None
        if response['status'] is True:
            print(response['returnData'])
            data = pd.json_normalize(response['returnData'])
            print(data)
            #order_data = data[["symbol", "description", "categoryName", "currency", "bid","ask", "time"]]
        else:
            order_data = None
            print("Failed to get order", response)
        return order_data
    
    async def __make_trade(self, order:int, cmd:TradeCmd, trade_type:TradeType, volume:int, price:float, custom_comment:str):
        """Open a new set stop order."""
        response = await self.socket.tradeTransaction(
                        symbol=self.symbol,
                        order=order,
                        cmd=cmd,
                        type=trade_type,
                        price=price,
                        volume=volume,
                        customComment=custom_comment
                    )
        order = response['returnData']['order']
        print(order)
        if response['status'] is True:
            print("Transaction done")
             # Wait until the order is executed
            pending = True
            while pending:
                status_response = await self.__return_order_status(order)           
                if status_response['returnData']['requestStatus'] != TradeStatus.PENDING.value:
                    pending = False
        else:
            print("Failed to make the transaction")        
        return order

    async def __close_trade(self, order:int, cmd:TradeCmd, volume:int, price:float):
        """close order."""
        response = await self.socket.tradeTransaction(
                        symbol=self.symbol,
                        order=order,
                        cmd=cmd,
                        type=TradeType.CLOSE,
                        price=price,
                        volume=volume                        
                    )
        order = response['returnData']['order']
        print(order)
        if response['status'] is True:
            print("Transaction done")
             # Wait until the order is executed
            pending = True
            while pending:
                status_response = await self.__return_order_status(order)           
                if status_response['returnData']['requestStatus'] != TradeStatus.PENDING.value:
                    pending = False
        else:
            print("Failed to make the transaction")        
        return order



    async def set_sell_stop_price_by_percentage(self, percentage: int, commit: bool = False):
        """Calculate Sell Stop and set it."""
        # Calculate Sell Stop    
        response = await self.socket.getTrades(True)
        if response['status'] is True:
            trade_records = response['returnData']
            data = pd.json_normalize(trade_records)        
            buy_trade_records = data[["order", "symbol","volume","open_price","close_price","profit","open_timeString","nominalValue","cmd","position"]].query("cmd==0 and symbol == @self.symbol")
            print(buy_trade_records)        
            open_price = buy_trade_records["open_price"].values[0]
            close_price = buy_trade_records["close_price"].values[0]
            buy_volume = buy_trade_records["volume"].values[0]
            reference_price = open_price
            # Chose close price as reference if close price is higher
            # than open price and negative percentage requested
            if ((percentage < 0) and (close_price > open_price)):
                reference_price = close_price        
            sell_stop_price = round(reference_price * (1 + percentage/100),1)
            print("Symbol: " + self.symbol)
            print("Reference Price: " + str(reference_price))
            print("Volume: " + str(buy_volume))
            print("Sell Stop Price: " + str(sell_stop_price))
            if percentage < 0:
                custom_comment = "Minus " + str(percentage)
            else:
                custom_comment = "Plus " + str(percentage)
            custom_comment = custom_comment + "%, price: " + str(sell_stop_price)
            print(custom_comment + "\n")
            sell_stop_trades = data[["order", "symbol", "volume", "open_price", "cmd"]].query("cmd==5 and symbol == @self.symbol")
            # Is there any Sell Stop orders for this symbol?
            if(len(sell_stop_trades) > 0):
                print(sell_stop_trades) 
                # Update them
                for index, row in sell_stop_trades.iterrows():
                    print(index)
                    sell_stop_order = row["order"]        
                    sell_stop_volume = row["volume"]
                    # user_input = input("Do you update current sell stop order:" + str(sell_stop_order) + "? ")
                    # if user_input.lower() == 'yes': 
                    if (commit):
                        # Modify sell stop order!
                        print("Modify sell stop order: " + str(sell_stop_order) + "\n")                        
                        order = await self.__make_trade(sell_stop_order, TradeCmd.SELL_STOP, TradeType.MODIFY, sell_stop_volume, sell_stop_price, custom_comment)           
                        await self.__return_order_status(order)
                    else:
                        print("Sell stop order: " + str(sell_stop_order) + " not modified\n")
            else:
                # Confirm sell stop order
                # user_input = input("Do you want to order the sell stop: " + custom_comment +  "? ")
                # if user_input.lower() == 'yes':
                if (commit):
                    print("Opening sell stop order\n")                
                    # Set sell Stops!
                    order = await self.__make_trade(0, TradeCmd.SELL_STOP, TradeType.OPEN, buy_volume, sell_stop_price, custom_comment)  
                    await self.__return_order_status(order)
                else:                
                    print("No sell stop ordered\n")
            return    
        else:
            print("Failed to get trade records", response)
            return
        
    async def open_short_buy(self, investment_value_reference:int, commit: bool = False):
        """Open short buy."""        
        print("Get current negotiation data")                              
        symbol_data = await self.get_data()
        precision = symbol_data["precision"].loc[0]
        current_ask = round(symbol_data["ask"].loc[0],precision)
        current_bid = round(symbol_data["bid"].loc[0],precision)
        loss_margin = 0.04
        current_bid = round(current_bid * (1 - loss_margin/100),precision-1)
        volume = round(investment_value_reference / current_ask, 0)
        real_investment_value = round(current_ask * volume, 2)
        sell_stop_value = round(current_bid * volume, 2)
        print("Symbol: " + self.symbol)
        print("Volume: " + str(volume))
        print("Ask price: " + str(current_ask))
        print("Bid price: " + str(current_bid))
        print("Investment Reference: " + str(investment_value_reference))
        print("Real Investment: " + str(real_investment_value))
        print("Sell stop value: " + str(sell_stop_value))
        print("Opening a buy short position using tha ask price and the investment reference\n")                              
        if (commit):               
            order = await self.__make_trade(0, TradeCmd.BUY, TradeType.OPEN, volume, current_ask, "open short buy")              
            # The order was accepted?
            status_response = await self.__return_order_status(order)
            request_status = status_response['returnData']['requestStatus']
            if request_status == TradeStatus.ACCEPTED.value:
                print("Buy order accepted, so now lets set the sell stop with the bid price and the same volume")
                await self.__make_trade(0, TradeCmd.SELL_STOP, TradeType.OPEN, volume, current_bid, "sell stop short buy")               
        else:
            print("No buy ordered executed.\n")

    async def close_short_buy(self, commit: bool = False):
        """Close short buy."""        
        
        print("Closing a buy short position\n")                                     
        response = await self.socket.getTrades(False)
        if response['status'] == True:
            trades = response['returnData']
            data = pd.json_normalize(trades)                              
                            
            buyTrades = data[["order", "symbol","volume","open_price","close_price","profit","open_timeString","nominalValue","cmd"]].query("cmd==0 and symbol==@self.symbol")
            print(buyTrades)              
            
            sell_stop_trades = data[["order", "symbol","volume","open_price","cmd"]].query("cmd==5 and symbol==@self.symbol")
            print(sell_stop_trades)     

            if (commit):         
                 # Is there any Sell Stop orders for this symbol?
                if(len(sell_stop_trades) > 0):                    
                    # Update them
                    for index, row in sell_stop_trades.iterrows():
                        print(index)
                        sell_stop_order = row["order"]            
                        sell_stop_volume = row["volume"]                    
                        sell_stop_price = row["open_price"]                    
                        # Close sell stop order!
                        print("Close sell stop order: " + str(sell_stop_order) + "\n")                        
                        order = await self.__close_trade(sell_stop_order, TradeCmd.SELL_STOP, sell_stop_volume, sell_stop_price)           
                        await self.__return_order_status(order)                        
            else:
                print("No close orders executed.\n")    

        else:
            print("Failed to get trades", response)       

       
        
        