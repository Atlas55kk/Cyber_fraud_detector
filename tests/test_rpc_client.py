"""
Unit Tests for DirectNodeRPCClient (src/fetchers/rpc_client.py)
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from src.fetchers.rpc_client import DirectNodeRPCClient, ERC20_TRANSFER_TOPIC
from src.core.wire_edge import TokenType


class TestDirectNodeRPCClient(unittest.TestCase):

    def setUp(self):
        self.client = DirectNodeRPCClient(
            rpc_endpoints=["http://mock-rpc-1.local", "http://mock-rpc-2.local"],
            timeout_seconds=2.0
        )

    @patch("urllib.request.urlopen")
    def test_get_block_number_success(self, mock_urlopen):
        # Mock response returning block 0x12a05f2 (19531250)
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x12a05f2"
        }).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        block_num = self.client.get_block_number()
        self.assertEqual(block_num, 19531250)

    @patch("urllib.request.urlopen")
    def test_failover_mechanism(self, mock_urlopen):
        # Endpoint 1 fails, Endpoint 2 succeeds
        mock_response_good = MagicMock()
        mock_response_good.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x40"
        }).encode("utf-8")
        mock_response_good.__enter__.return_value = mock_response_good

        mock_urlopen.side_effect = [Exception("Network error on primary"), mock_response_good]

        res = self.client.call_rpc("eth_blockNumber", [])
        self.assertEqual(res, "0x40")
        # Ensure active endpoint rotated
        self.assertEqual(self.client.active_endpoint_index, 1)

    def test_parse_log_to_wire(self):
        mock_log = {
            "transactionHash": "0xabc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "topics": [
                ERC20_TRANSFER_TOPIC,
                "0x0000000000000000000000001111111111111111111111111111111111111111",
                "0x0000000000000000000000002222222222222222222222222222222222222222"
            ],
            "data": hex(5000 * 10**6), # 5,000 USDT (6 decimals)
            "blockNumber": "0x1000"
        }

        wire = self.client.parse_log_to_wire(mock_log, token_symbol="USDT")
        self.assertIsNotNone(wire)
        self.assertEqual(wire.from_address, "0x1111111111111111111111111111111111111111")
        self.assertEqual(wire.to_address, "0x2222222222222222222222222222222222222222")
        self.assertEqual(wire.value, 5000.0)
        self.assertEqual(wire.token_symbol, "USDT")
        self.assertEqual(wire.token_type, TokenType.ERC20)
        self.assertEqual(wire.block_number, 4096)


if __name__ == "__main__":
    unittest.main()
