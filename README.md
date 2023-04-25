# xStation5 API Python Library

[![Test xapi-python](https://github.com/pawelkn/xapi-python/actions/workflows/test-xapi-python.yml/badge.svg)](https://github.com/pawelkn/xapi-python/actions/workflows/test-xapi-python.yml)

The xStation5 API Python library provides a simple and easy-to-use API for interacting with the xStation5 trading platform. With this library, you can connect to the xStation5 platform, retrieve market data, and execute trades.

This library may be used for [BFB Capital](https://bfb.capital) and [XTB](https://www.xtb.com) xStation5 accounts.

API documentation: <http://developers.xstore.pro/documentation>

## Disclaimer

This xStation5 API Python library is not affiliated with, endorsed by, or in any way officially connected to the xStation5 trading platform or its parent company. The library is provided as-is and is not guaranteed to be suitable for any particular purpose. The use of this library is at your own risk, and the author(s) of this library will not be liable for any damages arising from the use or misuse of this library. Please refer to the license file for more information.

## Installation

You can install xAPI using pip. Simply run the following command:

```shell
pip install xapi-python
```

## Usage

To use xAPI, you will need to have an active account with the xStation5 trading platform. Once you have an account, you can use the xStation5 library to connect to the platform and begin trading.

Here is an example of how to use the xAPI library to connect to the xStation5 platform:

```python
import asyncio
import xapi

# Replace these values with your own credentials
credentials = {
    "accountId": "<your_client_id>",
    "password": "<your_password>",
    "host": "ws.xtb.com",
    "type": "real",
    "safe": False
}

async def main():
    try:
        # Create a new xAPI object and connect to the xStation5 platform
        x = await xapi.connect(**credentials)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

Once you have connected to the platform, you can use the xAPI object to retrieve market data and execute trades.

Here is an example of how to subscribe to market data using the xAPI library:

```python
import asyncio
import xapi

# Replace these values with your own credentials
credentials = {
    "accountId": "<your_client_id>",
    "password": "<your_password>",
    "host": "ws.xtb.com",
    "type": "real",
    "safe": False
}

async def main():
    while True:
        try:
            x = await xapi.connect(**credentials)

            # Subscribe for the current price of BITCOIN and ETHEREUM
            await x.stream.getTickPrices("BITCOIN")
            await x.stream.getTickPrices("ETHEREUM")

            # Listen for coming price ticks
            async for message in x.stream.listen():
                print(message['data'])

        except xapi.LoginFailed as e:
            print(f"Log in failed: {e}")
            return

        except xapi.ConnectionClosed as e:
            print(f"Connection closed: {e}, reconnecting ...")
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass
```

And here is an example of how to execute a trade using the xAPI library:

```python
import asyncio
import xapi
from xapi import TradeCmd, TradeType, TradeStatus

# Replace these values with your own credentials
credentials = {
    "accountId": "<your_client_id>",
    "password": "<your_password>",
    "host": "ws.xtb.com",
    "type": "real",
    "safe": False
}

async def main():
    try:
        x = await xapi.connect(**credentials)

        # Open a new trade for BITCOIN
        response = await x.socket.tradeTransaction(
            symbol="BITCOIN",
            cmd=TradeCmd.BUY_LIMIT,
            type=TradeType.OPEN,
            price=10.00,
            volume=1
        )

        if response['status'] == True:
            print("Transaction sent to market")
        else:
            print("Failed to trade a transaction", response)

    except xapi.LoginFailed as e:
        print(f"Log in failed: {e}")

    except xapi.ConnectionClosed as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Examples

To run the examples for the xAPI library, you will need to have an account with the xStation5 trading platform.

Before running the examples, you should create a file called _credentials.json_ in the project directory. This file should contain your account credentials, like this:

### credentials.json

```json
{
    "accountId": "<your_client_id>",
    "password": "<your_password>",
    "host": "ws.xtb.com",
    "type": "demo",
    "safe": true
}
```

Once you have created the _credentials.json_ file, you can run an example using the following command:

```shell
python3 examples/get-balance.py
```

## Unit Tests

This will run all of the unit tests in the tests directory:

```shell
python3 -m unittest discover tests
```