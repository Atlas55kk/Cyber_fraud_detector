"""
Unit tests for the TRON (TRC-20 USDT) Ingestion and Forensics Engine.
"""

import os
import json
import unittest
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import NodeRole
from src.core.wire_edge import TokenType, ForensicWire
from src.core.taint_engine import TaintEngine
from src.attribution.entity_resolver import EntityResolver
from src.fetchers.tron_fetcher import TronFetcher, TRON_USDT_CONTRACT
from src.algorithms.priority_search import PrioritySearchEngine


class TestTronForensics(unittest.TestCase):

    def setUp(self):
        self.canvas = WhiteboardCanvas(canvas_id="TRON_USDT_Case_Test")
        self.taint_engine = TaintEngine()
        self.entity_resolver = EntityResolver()
        self.tron_fetcher = TronFetcher(cache_dir="data/cache/tron_test")

    def tearDown(self):
        # Clean up test cache directory
        if os.path.exists("data/cache/tron_test"):
            for f in os.listdir("data/cache/tron_test"):
                os.remove(os.path.join("data/cache/tron_test", f))
            os.rmdir("data/cache/tron_test")

    def test_tron_exchange_entity_resolution(self):
        # Binance TRON Hot Wallet
        binance_tron = "TPY9W8PnmgCJnUqUrYJ7p4G93F6r8eH1e6"
        entity = self.entity_resolver.resolve(binance_tron)
        self.assertIsNotNone(entity)
        self.assertIn("Binance", entity.name)
        self.assertEqual(entity.node_role, NodeRole.CEX_DEPOSIT)
        self.assertTrue(entity.is_actionable_freeze_target)

        # CoinDCX TRON Hot Wallet
        coindcx_tron = "TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6"
        entity_coindcx = self.entity_resolver.resolve(coindcx_tron)
        self.assertIsNotNone(entity_coindcx)
        self.assertIn("CoinDCX", entity_coindcx.name)
        self.assertTrue(entity_coindcx.fiu_registered)

        # SunSwap (TRON DEX)
        sunswap = "TKzxdSv2FZKQrEqkKVgp5DcwEXBEKMg2Ax"
        entity_dex = self.entity_resolver.resolve(sunswap)
        self.assertIsNotNone(entity_dex)
        self.assertEqual(entity_dex.node_role, NodeRole.DEX_ROUTER)

    def test_tron_cached_transfer_parsing(self):
        # Create a mock cached response matching Tronscan token_trc20/transfers API schema
        mock_tronscan_payload = [
            {
                "transaction_id": "8a39b8c049102ef1934ba98d103947ab59102834b91823901a83910283b91834",
                "from_address": "TScammerRoot99182348120384729102847291",
                "to_address": "TMuleHop1_91823948120398410293847192",
                "quant": "25000000000", # 25,000 USDT (6 decimals)
                "tokenInfo": {"tokenDecimal": 6, "tokenSymbol": "USDT"},
                "block_ts": 1700000500000,
                "block": 56000000,
                "fee": 13500000 # 13.5 TRX
            }
        ]

        test_addr = "TScammerRoot99182348120384729102847291"
        cache_file = self.tron_fetcher._get_cache_path(test_addr, TRON_USDT_CONTRACT)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(mock_tronscan_payload, f)

        wires = self.tron_fetcher.fetch_outgoing_trc20_transfers(test_addr)
        self.assertEqual(len(wires), 1)
        w = wires[0]
        self.assertEqual(w.value, 25000.0)
        self.assertEqual(w.token_symbol, "USDT")
        self.assertEqual(w.token_type, TokenType.TRC20)
        self.assertEqual(w.from_address, test_addr.lower())
        self.assertEqual(w.to_address, "TMuleHop1_91823948120398410293847192".lower())
        self.assertEqual(w.gas_fee, 13.5)

    def test_end_to_end_tron_usdt_tracing(self):
        # Scenario:
        # Victim transfers 50,000 TRC-20 USDT to TRON Scammer Wallet: TScamWallet...
        # TScamWallet -> TMuleHop... (50,000 USDT)
        # TMuleHop -> Binance TRON Hot Wallet: TPY9W8PnmgCJnUqUrYJ7p4G93F6r8eH1e6 (50,000 USDT)
        
        scam_wallet = "TScamSyndicate_Alpha_91029384"
        mule_wallet = "TMuleHop_Beta_591029384719283"
        binance_tron = "TPY9W8PnmgCJnUqUrYJ7p4G93F6r8eH1e6"

        self.canvas.set_incident_root(scam_wallet, 50000.0, 1700000000)

        graph_db = {
            scam_wallet.lower(): [
                ForensicWire("0xtx_tron_1", scam_wallet, mule_wallet, 50000.0, token_symbol="USDT", token_type=TokenType.TRC20, timestamp=1700000100)
            ],
            mule_wallet.lower(): [
                ForensicWire("0xtx_tron_2", mule_wallet, binance_tron, 50000.0, token_symbol="USDT", token_type=TokenType.TRC20, timestamp=1700000200)
            ]
        }

        def mock_fetcher(addr: str):
            return graph_db.get(addr.lower(), [])

        search_engine = PrioritySearchEngine(self.canvas, self.taint_engine, self.entity_resolver)
        actionable_cex_nodes = search_engine.run_trace(mock_fetcher)

        self.assertEqual(len(actionable_cex_nodes), 1)
        self.assertEqual(actionable_cex_nodes[0].address, binance_tron.lower())
        self.assertIn("Binance", actionable_cex_nodes[0].entity_tag)
        self.assertEqual(actionable_cex_nodes[0].stolen_amount_held, 50000.0)
        self.assertEqual(actionable_cex_nodes[0].stolen_taint_ratio, 1.0)


if __name__ == "__main__":
    unittest.main()
