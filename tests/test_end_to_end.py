"""
End-to-End Integration Test: Simulates a complete police cyber fraud tracing workflow
from victim complaint to CEX detection and Section 94 BNSS Legal Freeze Requisition.
"""

import os
import unittest
from src.core.canvas import WhiteboardCanvas
from src.core.taint_engine import TaintEngine
from src.attribution.entity_resolver import EntityResolver
from src.algorithms.priority_search import PrioritySearchEngine
from src.fetchers.mock_generator import MockFraudScenarioGenerator
from src.reporting.dossier_generator import LegalDossierGenerator, CaseDetails
from src.reporting.visualizer import WhiteboardVisualizer


class TestEndToEndForensics(unittest.TestCase):

    def test_complete_investigation_pipeline(self):
        # 1. Setup Framework
        canvas = WhiteboardCanvas(canvas_id="MHA_Case_SIH_26183")
        taint_engine = TaintEngine()
        entity_resolver = EntityResolver()
        search_engine = PrioritySearchEngine(canvas, taint_engine, entity_resolver)

        # 2. Register Scam Incident Root (Victim sent 50,000 USDT to Wallet S)
        canvas.set_incident_root(
            address="0xwallet_s",
            stolen_amount=50000.0,
            timestamp=1700000000
        )

        # 3. Load Problem Statement Money Flow Graph
        mock_graph = MockFraudScenarioGenerator.generate_problem_statement_case()

        def fetcher(addr: str):
            return mock_graph.get(addr.lower(), [])

        # 4. Execute Priority Best-First Search
        actionable_cex_nodes = search_engine.run_trace(fetcher)

        # 5. Verification: Both Binance and CoinDCX must be located
        self.assertEqual(len(actionable_cex_nodes), 2)
        cex_names = [n.entity_tag for n in actionable_cex_nodes]
        self.assertTrue(any("Binance" in name for name in cex_names))
        self.assertTrue(any("CoinDCX" in name for name in cex_names))

        stats = canvas.summary_stats()
        self.assertEqual(stats["total_funds_at_exchanges"], 35000.0)
        self.assertEqual(stats["recovery_potential_pct"], 70.0) # (20k + 15k) / 50k = 70%

        # 6. Generate Section 94 BNSS Police Requisition Notice
        dossier_gen = LegalDossierGenerator(canvas)
        case = CaseDetails(
            ack_number="NCRP/2026/881230",
            fir_number="FIR 109/2026 (Cyber Police Station)",
            investigating_officer="Insp. Arvind Kumar",
            loss_inr=4250000.0,
            loss_crypto_str="50,000 USDT"
        )
        
        binance_node = [n for n in actionable_cex_nodes if "Binance" in (n.entity_tag or "")][0]
        binance_entity = entity_resolver.resolve(binance_node.address)
        notice_text = dossier_gen.generate_section_94_bnss_notice(case, binance_node, binance_entity)

        self.assertIn("SECTION 94 OF BHARATIYA NAGARIK SURAKSHA SANHITA", notice_text)
        self.assertIn("IMMEDIATELY FREEZE / PLACE A RESTRICTIVE LIEN", notice_text)
        self.assertIn("20,000.00 USDT", notice_text)
        self.assertIn("0xtx_s_b", notice_text)
        self.assertIn("0xtx_b_d", notice_text)
        self.assertIn("0xtx_d_binance", notice_text)

        # 7. Generate Interactive Whiteboard HTML
        visualizer = WhiteboardVisualizer(canvas)
        test_html_path = "tests/test_whiteboard.html"
        generated_file = visualizer.export_html(test_html_path)
        
        self.assertTrue(os.path.exists(generated_file))
        self.assertGreater(os.path.getsize(generated_file), 1000)

        # Clean up test artifact
        if os.path.exists(test_html_path):
            os.remove(test_html_path)


if __name__ == "__main__":
    unittest.main()
