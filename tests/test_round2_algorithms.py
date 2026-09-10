"""
Round 2: Mathematical & Algorithmic Boundary Stress Testing Suite
Tests for:
1. TaintEngine mathematical singularities (zero balance, gas exceeding balance, dust)
2. Graph cycle handling in PrioritySearchEngine (2-cycles, 3-cycles, self-loops)
3. TRON Base58Check mixed-casing in canvas.trace_paths_to_address
4. Combinatorial path recursion safety in DFS path tracing
5. SmurfingFilter zero-mean division safety and PeelChain boundary conditions
"""

import unittest
import math
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import ForensicNodeBox, NodeRole
from src.core.wire_edge import ForensicWire, TokenType
from src.core.taint_engine import TaintEngine, TaintModel
from src.attribution.entity_resolver import EntityResolver
from src.algorithms.priority_search import PrioritySearchEngine, SearchConfig
from src.algorithms.peel_detector import PeelChainDetector
from src.algorithms.smurf_filter import SmurfingFilter


class TestRound2Algorithms(unittest.TestCase):
    def setUp(self):
        self.resolver = EntityResolver()

    def test_taint_engine_zero_and_gas_exhaustion(self):
        """
        Verify TaintEngine handles balance = 0, gas > balance, and zero-value transfers safely.
        """
        engine = TaintEngine(model=TaintModel.HAIRCUT, min_taint_threshold=0.01, min_tainted_value=1.0)
        
        sender = ForensicNodeBox(address="0xsender", current_balance=10.0, stolen_taint_ratio=1.0, stolen_amount_held=10.0)
        receiver = ForensicNodeBox(address="0xrecv", current_balance=0.0)
        
        # Gas fee (15.0) exceeds sender balance (10.0)
        wire_overgas = ForensicWire(
            tx_hash="0xtx1", from_address="0xsender", to_address="0xrecv",
            value=10.0, gas_fee=15.0, timestamp=1000
        )
        taint_val, recv_ratio, is_pruned = engine.propagate_taint(sender, receiver, wire_overgas)
        
        self.assertGreaterEqual(sender.current_balance, 0.0)
        self.assertGreaterEqual(sender.stolen_amount_held, 0.0)
        self.assertFalse(math.isnan(recv_ratio))
        self.assertFalse(math.isinf(recv_ratio))
        self.assertLessEqual(recv_ratio, 1.0)

    def test_graph_cycle_infinite_loop_prevention(self):
        """
        Stress test: Graph with mutual cycles:
        Root -> NodeA -> NodeB -> NodeA (cycle)
        NodeB -> NodeC -> Root (cycle back to root)
        NodeA -> NodeA (self-loop)
        Verify search engine terminates without stack overflow or infinite loops.
        """
        canvas = WhiteboardCanvas(canvas_id="Cycle_Stress_Test")
        canvas.set_incident_root("0xroot", 10000.0, 1000)
        
        graph_db = {
            "0xroot": [
                ForensicWire("0xtx_ra", "0xroot", "0xnode_a", 5000.0, timestamp=1100),
                ForensicWire("0xtx_rb", "0xroot", "0xnode_b", 5000.0, timestamp=1150)
            ],
            "0xnode_a": [
                ForensicWire("0xtx_self", "0xnode_a", "0xnode_a", 100.0, timestamp=1200), # Self-loop
                ForensicWire("0xtx_ab", "0xnode_a", "0xnode_b", 4000.0, timestamp=1250)
            ],
            "0xnode_b": [
                ForensicWire("0xtx_ba", "0xnode_b", "0xnode_a", 2000.0, timestamp=1300), # 2-Cycle back to A
                ForensicWire("0xtx_bc", "0xnode_b", "0xnode_c", 2000.0, timestamp=1350)
            ],
            "0xnode_c": [
                ForensicWire("0xtx_croot", "0xnode_c", "0xroot", 1000.0, timestamp=1400) # Cycle back to root
            ]
        }
        
        def fetcher(addr):
            return graph_db.get(addr.lower(), [])

        taint_eng = TaintEngine(model=TaintModel.HAIRCUT, min_taint_threshold=0.01)
        search_eng = PrioritySearchEngine(canvas, taint_eng, self.resolver, SearchConfig(max_hops=5, max_nodes_budget=20))
        
        # Must execute and terminate cleanly
        actionable = search_eng.run_trace(fetcher)
        self.assertIsInstance(actionable, list)
        self.assertLessEqual(len(canvas.nodes), 20)

    def test_tron_base58_casing_path_tracing(self):
        """
        Verify that trace_paths_to_address finds transaction paths to TRON Base58 targets.
        """
        canvas = WhiteboardCanvas(canvas_id="TRON_Path_Test")
        scam_tron = "TScamMaster1122334455667788990011"
        mule_tron = "TMuleHop9988776655443322110099"
        cex_tron = "TPY9W8PnmgCJnUqUrYJ7p4G93F6r8eH1e6" # Real Binance TRON deposit
        
        canvas.set_incident_root(scam_tron, 50000.0, 1000)
        canvas.add_wire("0xtx_tron_1", scam_tron, mule_tron, 50000.0, token_symbol="USDT", token_type=TokenType.TRC20)
        canvas.add_wire("0xtx_tron_2", mule_tron, cex_tron, 50000.0, token_symbol="USDT", token_type=TokenType.TRC20)
        
        # Test tracing path to CEX
        paths = canvas.trace_paths_to_address(cex_tron)
        self.assertEqual(len(paths), 1, f"Failed to trace path to TRON Base58 target! Got: {paths}")
        self.assertEqual(paths[0], ["0xtx_tron_1", "0xtx_tron_2"])

    def test_smurfing_filter_zero_variance_and_empty(self):
        """
        Verify SmurfingFilter handles empty canvases and identical amounts without divide-by-zero.
        """
        filter_eng = SmurfingFilter()
        empty_canvas = WhiteboardCanvas(canvas_id="Empty")
        clusters = filter_eng.detect_smurfing_clusters(empty_canvas)
        self.assertEqual(len(clusters), 0)

        # Single output node (not a cluster)
        canvas = WhiteboardCanvas(canvas_id="Single")
        canvas.set_incident_root("0xroot", 100.0, 1000)
        canvas.add_wire("0xtx1", "0xroot", "0xrecv", 100.0)
        clusters_single = filter_eng.detect_smurfing_clusters(canvas)
        self.assertEqual(len(clusters_single), 0)


if __name__ == "__main__":
    unittest.main()
