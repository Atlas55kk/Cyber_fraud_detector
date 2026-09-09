"""
Unit tests for the Forensic Search and Pattern Recognition Algorithms.
"""

import unittest
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import NodeRole
from src.core.wire_edge import ForensicWire, TokenType
from src.core.taint_engine import TaintEngine
from src.attribution.entity_resolver import EntityResolver
from src.algorithms.priority_search import PrioritySearchEngine, SearchConfig
from src.algorithms.peel_detector import PeelChainDetector
from src.algorithms.smurf_filter import SmurfingFilter


class TestAlgorithms(unittest.TestCase):

    def setUp(self):
        self.canvas = WhiteboardCanvas(canvas_id="Algo_Test_Canvas")
        self.taint_engine = TaintEngine()
        self.entity_resolver = EntityResolver()
        self.search_engine = PrioritySearchEngine(
            canvas=self.canvas,
            taint_engine=self.taint_engine,
            entity_resolver=self.entity_resolver
        )

    def test_peel_chain_detection(self):
        # Build 3-hop peel chain:
        # S (100) -> [P1 (10) to Service1, H1 (90) to Transit1]
        # H1 (90) -> [P2 (10) to Service2, H2 (80) to Transit2]
        # H2 (80) -> [P3 (10) to Service3, H3 (70) to Transit3]
        
        self.canvas.set_incident_root("0xRootScam", 100.0, 1700000000)
        
        # Hop 1
        self.canvas.add_wire("0xp1", "0xRootScam", "0xService1", 10.0, timestamp=1700000010)
        self.canvas.add_wire("0xb1", "0xRootScam", "0xTransit1", 90.0, timestamp=1700000010)

        # Hop 2
        self.canvas.add_wire("0xp2", "0xTransit1", "0xService2", 10.0, timestamp=1700000100)
        self.canvas.add_wire("0xb2", "0xTransit1", "0xTransit2", 80.0, timestamp=1700000100)

        # Hop 3
        self.canvas.add_wire("0xp3", "0xTransit2", "0xService3", 10.0, timestamp=1700000200)
        self.canvas.add_wire("0xb3", "0xTransit2", "0xTransit3", 70.0, timestamp=1700000200)

        detector = PeelChainDetector(max_peel_ratio=0.25, min_chain_length=2)
        chains = detector.detect_peel_chains(self.canvas)

        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0].length, 3)
        self.assertEqual(chains[0].peeled_destinations, ["0xservice1", "0xservice2", "0xservice3"])
        self.assertEqual(chains[0].total_peeled_amount, 30.0)

    def test_smurfing_filter(self):
        # Build Fan-out:
        # ScamWallet splits 50,000 into 5 near-equal mule transactions of ~10,000 within 5 minutes
        self.canvas.set_incident_root("0xScamHub", 50000.0, 1700000000)
        
        mules = ["0xMule1", "0xMule2", "0xMule3", "0xMule4", "0xMule5"]
        amounts = [9950.0, 10050.0, 9900.0, 10100.0, 10000.0]
        
        for i, (m, amt) in enumerate(zip(mules, amounts)):
            self.canvas.add_wire(
                tx_hash=f"0xsmurf_{i}",
                from_address="0xScamHub",
                to_address=m,
                value=amt,
                timestamp=1700000000 + (i * 60) # 1 minute apart
            )

        smurf_filter = SmurfingFilter(min_fan_out_degree=4, max_time_window_seconds=1800, max_coefficient_of_variation=0.10)
        clusters = smurf_filter.detect_smurfing_clusters(self.canvas)

        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0].source_address, "0xscamhub")
        self.assertEqual(len(clusters[0].mule_addresses), 5)
        self.assertAlmostEqual(clusters[0].total_structured_amount, 50000.0, delta=1.0)
        
        # Verify mules were classified
        mule_node = self.canvas.nodes["0xmule1"]
        self.assertEqual(mule_node.role, NodeRole.MULE_TRANSIT)

    def test_priority_search_finds_binance(self):
        # Setup graph topology:
        # Root (100 USDT) has 2 paths:
        # Path A (High noise / dust): Root -> Noise1 (0.5 USDT) -> Noise2 (0.5 USDT)
        # Path B (Main heist flow): Root -> MuleB (99.5 USDT) -> Binance Hot Wallet (99.5 USDT)
        
        binance_hot_wallet = "0x28c6c06298d514db089934071355e5743bf21d60"
        
        self.canvas.set_incident_root("0xVictimScammer", 100.0, 1700000000)

        graph_db = {
            "0xvictimscammer": [
                ForensicWire("0xnoise_tx", "0xvictimscammer", "0xnoise1", 0.5, timestamp=1700000010),
                ForensicWire("0xmain_tx", "0xvictimscammer", "0xmuleb", 99.5, timestamp=1700000010)
            ],
            "0xmuleb": [
                ForensicWire("0xcashout_tx", "0xmuleb", binance_hot_wallet, 99.5, timestamp=1700000050)
            ],
            "0xnoise1": [
                ForensicWire("0xnoise_tx2", "0xnoise1", "0xnoise2", 0.5, timestamp=1700000020)
            ]
        }

        def mock_fetcher(addr: str):
            return graph_db.get(addr.lower(), [])

        cex_endpoints = self.search_engine.run_trace(mock_fetcher)

        self.assertEqual(len(cex_endpoints), 1)
        self.assertEqual(cex_endpoints[0].address, binance_hot_wallet)
        self.assertIn("Binance", cex_endpoints[0].entity_tag)
        self.assertEqual(cex_endpoints[0].role, NodeRole.CEX_DEPOSIT)


if __name__ == "__main__":
    unittest.main()
