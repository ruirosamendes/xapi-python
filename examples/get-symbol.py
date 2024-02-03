import logging
import asyncio
import json
import xapi
import pandas as pd


logging.basicConfig(level=logging.INFO)

with open("credentials.json", "r") as f:
    CREDENTIALS = json.load(f)

from datetime import datetime as dt

async def main():
    try:
        async with await xapi.connect(**CREDENTIALS) as x:
            response = await x.socket.getSymbol("P911.DE_9")
            if response['status'] == True:
                trades = response['returnData']
                data = pd.json_normalize(trades)                              
                print(data.columns.values)
                print(data)     

                 # OUTPUT TO FILE
                now = dt.now() # current date and time
                dateTimeStr = now.strftime("%Y%m%d_%H%M%S")
                filename = "Symbol" + dateTimeStr + ".csv"
                print(filename)                             
                data.to_csv(filename)  
                
            else:
                print("Failed to get symbol", response)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())