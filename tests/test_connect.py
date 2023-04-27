import unittest
from unittest.mock import AsyncMock, patch

import websockets.client
import websockets.exceptions
import json

from xapi import Connection, ConnectionClosed

class TestConnection(unittest.IsolatedAsyncioTestCase):

    async def test_connect_timeout_error(self):
        c = Connection()
        with self.assertRaises(ConnectionClosed) as cm:
            await c.connect("ws://localhost:9000")
        self.assertEqual(str(cm.exception), "Connection refused")

    async def test_connect_refused_error(self):
        conn = Connection()
        with patch("websockets.client.connect", new_callable=AsyncMock) as mocked_connect:
            mocked_connect.side_effect = ConnectionRefusedError()
            with self.assertRaises(ConnectionClosed) as cm:
                await conn.connect("ws://localhost:9000")
            self.assertEqual(str(cm.exception), "Connection refused")

    async def test_disconnect(self):
        c = Connection()
        c._conn = AsyncMock(spec=websockets.client.WebSocketClientProtocol)
        await c.disconnect()
        self.assertIsNone(c._conn)

    async def test_listen_with_connection(self):
        c = Connection()
        c._conn = AsyncMock()
        c._conn.__aiter__.return_value = iter(['{"message": "Hello, world!"}'])
        messages = []
        async for message in c.listen():
            messages.append(message)
        self.assertEqual(messages, [{"message": "Hello, world!"}])

    async def test_listen_without_connection(self):
        c = Connection()
        with self.assertRaises(ConnectionClosed) as cm:
            async for _ in c.listen():
                pass
        self.assertEqual(str(cm.exception), "Not connected")

    async def test_listen_connection_closed(self):
        c = Connection()
        c._conn = AsyncMock()
        c._conn.__aiter__.side_effect = websockets.exceptions.ConnectionClosed(None, None)
        with self.assertRaises(ConnectionClosed) as cm:
            async for _ in c.listen():
                pass
        self.assertEqual(str(cm.exception), "Connection unexpectedly closed")

    async def test_request_with_connection(self):
        conn = Connection()
        conn._conn = AsyncMock()
        command = {"command": "test"}
        await conn._request(command)
        conn._conn.send.assert_called_once_with(json.dumps(command))

    async def test_request_without_connection(self):
        conn = Connection()
        command = {"command": "test"}
        with self.assertRaises(ConnectionClosed) as cm:
            await conn._request(command)
        self.assertEqual(str(cm.exception), "Not connected")

    async def test_request_connection_closed(self):
        conn = Connection()
        conn._conn = AsyncMock()
        conn._conn.send.side_effect = websockets.exceptions.ConnectionClosed(None, None)
        command = {"command": "test"}
        with self.assertRaises(ConnectionClosed) as cm:
            await conn._request(command)
        self.assertEqual(str(cm.exception), "Connection unexpectedly closed")

    async def test_response_with_connection(self):
        conn = Connection()
        conn._conn = AsyncMock()
        response = {"response": "test"}
        conn._conn.recv.return_value = json.dumps(response)
        result = await conn._response()
        conn._conn.recv.assert_called_once()
        self.assertEqual(result, response)

    async def test_response_without_connection(self):
        conn = Connection()
        with self.assertRaises(ConnectionClosed) as cm:
            await conn._response()
        self.assertEqual(str(cm.exception), "Not connected")

    async def test_response_connection_closed(self):
        conn = Connection()
        conn._conn = AsyncMock()
        conn._conn.recv.side_effect = websockets.exceptions.ConnectionClosed(None, None)
        with self.assertRaises(ConnectionClosed) as cm:
            await conn._response()
        self.assertEqual(str(cm.exception), "Connection unexpectedly closed")

    async def test_transaction_with_connection(self):
        conn = Connection()
        conn._conn = AsyncMock()
        command = {"command": "test"}
        response = {"response": "test"}
        conn._conn.recv.return_value = json.dumps(response)
        result = await conn._transaction(command)
        conn._conn.send.assert_called_once_with(json.dumps(command))
        conn._conn.recv.assert_called_once()
        self.assertEqual(result, response)

    async def test_transaction_without_connection(self):
        conn = Connection()
        command = {"command": "test"}
        with self.assertRaises(ConnectionClosed) as cm:
            await conn._transaction(command)
        self.assertEqual(str(cm.exception), "Not connected")

    async def test_transaction_connection_closed(self):
        conn = Connection()
        conn._conn = AsyncMock()
        conn._conn.send.side_effect = websockets.exceptions.ConnectionClosed(None, None)
        command = {"command": "test"}
        with self.assertRaises(ConnectionClosed) as cm:
            await conn._transaction(command)
        self.assertEqual(str(cm.exception), "Connection unexpectedly closed")
