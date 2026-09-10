"""
Unit tests for the Deposit Sweeping and Forward Clustering Heuristic (Victor 2020).
"""

import unittest
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import NodeRole
from src.core.wire_edge import ForensicWire, TokenType
from src.core.taint_engine import TaintEngine
from src.attribution.entity_resolver import EntityResolver
from src.attribution.deposit_sweeper import DepositSweeper
from src.algorithms.priority_search import PrioritySearchEngine


class TestDepositSweeper(unittest.TestCase):

    def setUp(self):
        self.canvas = WhiteboardCanvas(canvas_id="Deposit_Sweeper_Test")
        self.taint_engine = TaintEngine()
        self.entity_resolver = EntityResolver()
        self.sweeper = DepositSweeper(self.entity_resolver)

    def test_direct_deposit_sweep_detection(self):
        # Scenario:
        # 0xUserDepositProxy receives 20,000 USDT stolen funds.
        # It has 1 outgoing transaction forwarding 19,998 USDT into Binance Hot Wallet (0x28c6c062...)
        
        binance_hot = "0x28c6c06298d514db089934071355e5743bf21d60"
        deposit_proxy_addr = "0xEphemeralUserDepositProxy991"

        proxy_node = self.canvas.get_or_create_node(
            address=deposit_proxy_addr,
            role=NodeRole.UNKNOWN,
            initial_balance=0.0,
            stolen_taint=1.0,
            stolen_held=20000.0
        )

        sweep_wire = ForensicWire(
            tx_hash="0xsweep_tx_hash_123",
            from_address=deposit_proxy_addr,
            to_address=binance_hot,
            value=19998.0,
            timestamp=1700000500
        )

        sweep_result = self.sweeper.evaluate_node_for_sweep(proxy_node, [sweep_wire])

        self.assertIsNotNone(sweep_result)
        self.assertEqual(sweep_result.exchange_name, "Binance")
        self.assertEqual(proxy_node.role, NodeRole.CEX_DEPOSIT)
        self.assertEqual(proxy_node.entity_tag, "Binance: User Deposit Proxy")

        # Verify that entity_resolver now recognizes this custom deposit address
        resolved = self.entity_resolver.resolve(deposit_proxy_addr)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.node_role, NodeRole.CEX_DEPOSIT)

    def test_priority_search_with_sweep_heuristic(self):
        # Full graph scenario:
        # Crime Root (50,000 USDT) -> Mule A (25,000 USDT) -> 0xUnknownProxy (25,000 USDT)
        # 0xUnknownProxy forwards 24,990 USDT to CoinDCX Hot Wallet (0x4a475459...)
        # The search engine should flag 0xUnknownProxy as an actionable CEX Deposit Proxy!

        coindcx_hot = "0x4a4754593444053896fa231b1e93c1ef7e068777"
        scam_root = "0xCrimeRootScam"
        mule_a = "0xMuleTransitAlpha"
        unknown_proxy = "0xUnknownDepositProxy88"

        self.canvas.set_incident_root(scam_root, 50000.0, 1700000000)

        graph_db = {
            scam_root.lower(): [
                ForensicWire("0xtx_root_mule", scam_root, mule_a, 25000.0, timestamp=1700000100)
            ],
            mule_a.lower(): [
                ForensicWire("0xtx_mule_proxy", mule_a, unknown_proxy, 25000.0, timestamp=1700000200)
            ],
            unknown_proxy.lower(): [
                ForensicWire("0xtx_sweep_coindcx", unknown_proxy, coindcx_hot, 24995.0, timestamp=1700000300)
            ]
        }

        def mock_fetcher(addr: str):
            return graph_db.get(addr.lower(), [])

        search_engine = PrioritySearchEngine(self.canvas, self.taint_engine, self.entity_resolver)
        actionable_nodes = search_engine.run_trace(mock_fetcher)

        # Both the proxy and the terminal hot wallet are actionable freeze targets
        addresses_found = [n.address for n in actionable_nodes]
        self.assertTrue(any(unknown_proxy.lower() in a for a in addresses_found) or any(coindcx_hot.lower() in a for a in addresses_found))


if __name__ == "__main__":
    unittest.main()
