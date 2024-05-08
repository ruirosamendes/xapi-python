import pandas as pd
from xapi import Socket, TradeCmd, TradeType, TradeStatus
from typing import cast

class Symbol:
    def __init__(self, socket: Socket, symbol:str):
        self.socket = socket
        self.symbol = symbol

    async def __return_order_status(self, order:int):
        """Return order status"""
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
        symbol_data = []
        if response['status'] is True:            
            data = pd.json_normalize(response['returnData'])            
            symbol_data = data[["symbol", "description", "categoryName", "currency", "bid","ask", "time", "precision", "spreadRaw"]]
        else:
            symbol_data = []
            print("Failed to get symbol", response)
        return symbol_data
    
    async def __get_order_data(self, order:int):
        response = await self.socket.getTradeRecords([order])
        order_data = []
        if response['status'] is True:
            print(response['returnData'])
            data = pd.json_normalize(response['returnData'])
            print(data)
            #order_data = data[["symbol", "description", "categoryName", "currency", "bid","ask", "time"]]
        else:
            order_data = []
            print("Failed to get order", response)
        return order_data
    
    async def __make_trade(self, order:int, cmd:TradeCmd, trade_type:TradeType, volume:int,
                            price:float, stop_loss:float=0.0, take_profit:float=0.0, custom_comment:str=None):
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
        if response['status'] is True:            
            print("Transaction done")
            order = response['returnData']['order']
            print(order)       
            # Wait until the order is executed
            pending = True
            while pending:
                status_response = await self.__return_order_status(order)           
                if status_response['returnData']['requestStatus'] != TradeStatus.PENDING.value:
                    pending = False
        else:
            order = None
            print("Failed to make the transaction")        
        return order



    async def set_sell_stop_price_by_percentage(self, percentage: int, commit: bool = False):
        """Calculate Sell Stop and set it."""
        # Calculate Sell Stop    
        response = await self.socket.getTrades(True)
        if response['status'] is True and len(response['returnData']) > 0:
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
        
    async def open_short_buy(self, investment_value_reference:int, commit:bool = False, loss_margin:float = 1.0, gain_margin:float = 2.5):
        """Open short buy."""        
        print("Get current negotiation data")                             
        symbol_data = await self.get_data()        
        category_name = symbol_data["categoryName"].loc[0]
        precision = symbol_data["precision"].loc[0]
        current_ask = round(symbol_data["ask"].loc[0],precision)
        current_bid = round(symbol_data["bid"].loc[0],precision)        
        # Buy strategy data
        buy_price = current_ask        
        sell_stop_price = round(current_bid * (1 - loss_margin/100),precision-1)        
        stop_loss_price = sell_stop_price        
        take_profit_price = round(current_ask * (1 + gain_margin/100),precision-1)        
        # Investment, loss and profit values
        if(investment_value_reference > current_ask):
            volume = round(investment_value_reference / current_ask, 0)        
        else:
            volume = round(investment_value_reference / current_ask, precision)        
        buy_value = round(buy_price * volume, 2)
        sell_stop_value = round(sell_stop_price * volume, 2)
        stop_loss_value = round(stop_loss_price * volume, 2)
        take_profit_value = round(take_profit_price * volume, 2)       

        print("Symbol: " + self.symbol)
        print("Volume: " + str(volume))
        print("Ask price: " + str(current_ask))
        print("Bid price: " + str(current_bid) + "\n")        
        print("Buy strategy data")        
        print("buy price: " + str(buy_price))
        print("Sell stop price: " + str(sell_stop_price))
        print("Stop loss price: " + str(stop_loss_price))
        print("Take profit price: " + str(take_profit_price))
        
        
        print("Investment Reference: " + str(investment_value_reference))
        print("Buy value: " + str(buy_value))

        if(category_name == "CRT" or category_name == "IND"):
            print("Stop loss value: " + str(stop_loss_value))
            print("Max loss value: " + str(round(buy_value - stop_loss_value,2)))
            print("Take profit value: " + str(take_profit_value))
            print("Potential gain value: " + str(round(take_profit_value - buy_value,2)))
        elif(category_name == "STC"):
            print("Sell stop value: " + str(sell_stop_value))
            print("Max loss value: " + str(round(buy_value - sell_stop_value,2)))

        print("\n")        
        print("Opening a buy short position using the ask price and the investment reference")                              
        if (commit):               
            if(category_name == "CRT" or category_name == "IND"):
                print("Cripto or Index order, so set the stop loss and the take profit")                    
                order = await self.__make_trade(0, TradeCmd.BUY, TradeType.OPEN, volume, buy_price, sell_stop_price, take_profit_price, "open short buy")
            elif(category_name == "STC"):
                print("Stock order")              
                order = await self.__make_trade(0, TradeCmd.BUY, TradeType.OPEN, volume, buy_price, "open short buy")
            # The order was accepted?
            status_response = await self.__return_order_status(order)
            request_status = status_response['returnData']['requestStatus']
            if request_status == TradeStatus.ACCEPTED.value:
                if(category_name == "STC"):
                    print("Buy order accepted, so now lets set the sell stop with the bid price and the same volume")                    
                    await self.__make_trade(0, TradeCmd.SELL_STOP, TradeType.OPEN, volume, sell_stop_price, "sell stop short buy")
        else:
            print("No buy ordered executed.\n")


    async def __close_all_trades(self, trades: pd.DataFrame, commit: bool = False):
        """Close all trades in the array"""                
        if (commit):         
                # Is there any Sell Stop orders for this symbol?
            if(len(trades) > 0):                    
                # Update them
                for index, row in trades.iterrows():                    
                    print(row)
                    trade_cmd = TradeCmd(row["cmd"])  # Replace "cast" with "int"
                    trade_order = row["order"]                    
                    trade_volume = row["volume"]                        
                    trade_price = row["open_price"]
                    # Close sell stop order!
                    print("Closing position: " + str(trade_order) + "\n")                        
                    order = await self.__close_trade(trade_order, trade_cmd, trade_volume, trade_price)
                    await self.__return_order_status(order)                        
        else:
            print("No close orders executed.\n")    


    async def close_short_buy(self, commit: bool = False):
        """Close short buy."""        
        
        print("Closing a buy short position\n")                                     
        response = await self.socket.getTrades(False)
        if response['status'] is True and len(response['returnData']) > 0:
            trades = response['returnData']
            data = pd.json_normalize(trades)                 
            print(data.columns.values)
            # SELL                
            cmd = TradeCmd.SELL
            trades = data[["order", "symbol","volume","open_price","close_price","cmd"]].query("cmd==@cmd and symbol==@self.symbol")
            print(trades)
            await self.__close_all_trades(trades, commit)
            # # SELL_STOP                
            cmd = TradeCmd.SELL_STOP
            trades = data[["order", "symbol","volume","open_price","close_price","position","cmd"]].query("cmd==@cmd and symbol==@self.symbol")            
            await self.__close_all_trades(trades, commit)
            # BUY
            cmd = TradeCmd.BUY
            trades = data[["order", "symbol","volume","open_price","close_price","position","cmd"]].query("cmd==@cmd and symbol==@self.symbol")    
            await self.__close_all_trades(trades, commit)
        else:
            print("Failed to get trades", response) 

    async def set_sell_stop_price_to_close(self, commit: bool = False):
        """Set Sell Stop and to force the position close."""
        # Calculate Sell Stop    
        response = await self.socket.getTrades(True)
        if response['status'] is True and len(response['returnData']) > 0:
            trade_records = response['returnData']
            data = pd.json_normalize(trade_records)        
            buy_trade_records = data[["order", "symbol","volume","open_price","close_price","profit","open_timeString","nominalValue","cmd","position"]].query("cmd==0 and symbol == @self.symbol")
            print(buy_trade_records)        
            open_price = buy_trade_records["open_price"].values[0]
            close_price = buy_trade_records["close_price"].values[0]
            buy_volume = buy_trade_records["volume"].values[0]
            # # Chose close price as reference if close price is higher
            # # than open price and negative percentage requested
            # sell_stop_price = open_price 
            # if (close_price > open_price):
            #     sell_stop_price = close_price   
            # else:
            #     print"Close
            #     user_input = input("Closing price below the open price. Do you update current sell stop prices to force the closing?")
            #     if user_input.lower() == 'yes':     
            #         sell_stop_price = close_price
            #     else:
            #         return
            sell_stop_price = close_price
            print("Symbol: " + self.symbol)
            print("Volume: " + str(buy_volume))
            print("Sell Stop Price: " + str(sell_stop_price))
            custom_comment = "Closing at price: " + str(sell_stop_price)
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
            return
        else:
            print("Failed to get trade records", response)
            return

    async def get_buy_positions(self):
        """Set Sell Stop and to force the position close."""
        buy_trade_records = []
        # Calculate Sell Stop    
        response = await self.socket.getTrades(True)
        if response['status'] is True and len(response['returnData']) > 0:
            trade_records = response['returnData']
            data = pd.json_normalize(trade_records)        
            buy_trade_records = data[["order", "symbol","volume","open_price","close_price","profit","open_timeString","nominalValue","cmd","position"]].query("cmd==0 and symbol == @self.symbol")          
            return buy_trade_records
        else:
            print("Failed to get buy trade records", response)
            return buy_trade_records