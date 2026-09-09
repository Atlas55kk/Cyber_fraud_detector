"""
Unit tests for the Core Forensic Engine (NodeBox, WireEdge, TaintEngine, WhiteboardCanvas).
"""

import unittest
from src.core.node_box import ForensicNodeBox, NodeRole
from src.core.wire_edge import ForensicWire, TokenType
from src.core.taint_engine import TaintEngine, TaintModel
from src.core.canvas import WhiteboardCanvas


class TestCoreForensicEngine(unittest.TestCase):

    def setUp(self):
        self.canvas = WhiteboardCanvas(canvas_id="Test_Case_01")
        self.taint_engine = TaintEngine(model=TaintModel.HAIRCUT, min_taint_threshold=0.02)

    def test_node_box_creation_and_memory(self):
        node = ForensicNodeBox(
            address="0x1111222233334444555566667777888899990000",
            role=NodeRole.SCAMMER,
            current_balance=100.0,
            stolen_taint_ratio=1.0,
            stolen_amount_held=100.0
        )
        self.assertEqual(node.address, "0x1111222233334444555566667777888899990000")
        self.assertEqual(node.role, NodeRole.SCAMMER)
        self.assertEqual(node.stolen_taint_ratio, 1.0)
        self.assertEqual(node.stolen_amount_held, 100.0)

    def test_proportional_haircut_taint_propagation(self):
        # Scenario:
        # Wallet A has 100 USDT stolen (100% taint).
        # Wallet A sends 40 USDT to Wallet B (which had 0 balance).
        # Wallet A sends 60 USDT to Wallet C (which already had 40 clean USDT).
        
        node_a = self.canvas.set_incident_root(
            address="0xAAAA000000000000000000000000000000000000",
            stolen_amount=100.0,
            timestamp=1700000000
        )
        node_b = self.canvas.get_or_create_node(
            address="0xBBBB000000000000000000000000000000000000",
            role=NodeRole.MULE_TRANSIT,
            initial_balance=0.0
        )
        node_c = self.canvas.get_or_create_node(
            address="0xCCCC000000000000000000000000000000000000",
            role=NodeRole.MULE_TRANSIT,
            initial_balance=40.0, # Existing clean funds
            stolen_taint=0.0
        )

        wire_1 = self.canvas.add_wire(
            tx_hash="0xtx1111",
            from_address=node_a.address,
            to_address=node_b.address,
            value=40.0,
            gas_fee=0.05,
            timestamp=1700000100
        )
        taint_val_1, ratio_b, pruned_1 = self.taint_engine.propagate_taint(node_a, node_b, wire_1)

        self.assertFalse(pruned_1)
        self.assertEqual(taint_val_1, 40.0)
        self.assertEqual(node_b.stolen_amount_held, 40.0)
        self.assertEqual(node_b.current_balance, 40.0)
        self.assertEqual(node_b.stolen_taint_ratio, 1.0)
        self.assertEqual(node_a.gas_burned_total, 0.05)

        wire_2 = self.canvas.add_wire(
            tx_hash="0xtx2222",
            from_address=node_a.address,
            to_address=node_c.address,
            value=60.0,
            gas_fee=0.05,
            timestamp=1700000200
        )
        taint_val_2, ratio_c, pruned_2 = self.taint_engine.propagate_taint(node_a, node_c, wire_2)

        self.assertFalse(pruned_2)
        self.assertEqual(taint_val_2, 60.0)
        # Total balance in C = 40 (clean) + 60 (stolen) = 100 USDT
        self.assertEqual(node_c.current_balance, 100.0)
        self.assertEqual(node_c.stolen_amount_held, 60.0)
        # Taint ratio in C = 60 / 100 = 0.60 (60%)
        self.assertEqual(node_c.stolen_taint_ratio, 0.60)

    def test_multi_hop_peel_chain_to_binance(self):
        # Scenario from problem statement:
        # Wallet S (100 USDT) -> Wallet B (40 USDT) -> Wallet D (40 USDT) -> Binance Deposit (40 USDT)
        
        node_s = self.canvas.set_incident_root("0xScammerWallet", 100.0, 1700000000)
        node_b = self.canvas.get_or_create_node("0xWalletB", NodeRole.MULE_TRANSIT)
        node_d = self.canvas.get_or_create_node("0xWalletD", NodeRole.MULE_TRANSIT)
        node_binance = self.canvas.get_or_create_node(
            "0xBinanceDeposit491",
            role=NodeRole.CEX_DEPOSIT,
            entity_tag="Binance: Hot/Deposit"
        )

        w1 = self.canvas.add_wire("0xhash1", "0xScammerWallet", "0xWalletB", 40.0, timestamp=1700000010)
        self.taint_engine.propagate_taint(node_s, node_b, w1)

        w2 = self.canvas.add_wire("0xhash2", "0xWalletB", "0xWalletD", 40.0, timestamp=1700000020)
        self.taint_engine.propagate_taint(node_b, node_d, w2)

        w3 = self.canvas.add_wire("0xhash3", "0xWalletD", "0xBinanceDeposit491", 40.0, timestamp=1700000030)
        self.taint_engine.propagate_taint(node_d, node_binance, w3)

        # Check endpoints
        cex_nodes = self.canvas.find_all_cex_endpoints()
        self.assertEqual(len(cex_nodes), 1)
        self.assertEqual(cex_nodes[0].address, "0xbinancedeposit491")
        self.assertEqual(cex_nodes[0].stolen_amount_held, 40.0)

        # Trace path
        paths = self.canvas.trace_paths_to_address("0xBinanceDeposit491")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0], ["0xhash1", "0xhash2", "0xhash3"])

        stats = self.canvas.summary_stats()
        self.assertEqual(stats["total_funds_at_exchanges"], 40.0)
        self.assertEqual(stats["recovery_potential_pct"], 40.0)


if __name__ == "__main__":
    unittest.main()
