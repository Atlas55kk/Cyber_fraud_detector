"""
Unit Tests for Two-Tier ML Classifiers:
- TransactionMicroClassifier (Tier 1)
- CampaignMacroClassifier (Tier 2)
"""

import unittest
from src.core.canvas import WhiteboardCanvas
from src.core.wire_edge import ForensicWire, TokenType
from src.core.node_box import ForensicNodeBox, NodeRole
from src.ml.transaction_classifier import TransactionMicroClassifier
from src.ml.campaign_classifier import CampaignMacroClassifier


class TestMLClassifiers(unittest.TestCase):

    def setUp(self):
        self.micro_classifier = TransactionMicroClassifier()
        self.macro_classifier = CampaignMacroClassifier()

    def test_tier1_rapid_relay_detection(self):
        # Wire forwarded in 15 seconds
        wire = ForensicWire(
            tx_hash="0x1111111111111111111111111111111111111111111111111111111111111111",
            from_address="0xaaaa",
            to_address="0xbbbb",
            value=250.0,
            token_symbol="USDT",
            timestamp=1700000015
        )
        assessment = self.micro_classifier.assess_wire(wire, incoming_timestamp=1700000000)
        self.assertEqual(assessment.classification, "RAPID_RELAY")
        self.assertGreaterEqual(assessment.anomaly_score, 0.70)

    def test_tier1_round_value_launder_detection(self):
        # Round 5,000 USDT transfer with 10-minute gap
        wire = ForensicWire(
            tx_hash="0x2222222222222222222222222222222222222222222222222222222222222222",
            from_address="0xbbbb",
            to_address="0xcccc",
            value=5000.0,
            token_symbol="USDT",
            timestamp=1700000600
        )
        assessment = self.micro_classifier.assess_wire(wire, incoming_timestamp=1700000000)
        self.assertEqual(assessment.classification, "ROUND_VALUE_LAUNDER")
        self.assertGreaterEqual(assessment.anomaly_score, 0.60)

    def test_tier2_macro_campaign_classification(self):
        canvas = WhiteboardCanvas(canvas_id="Test_ML_Canvas")
        canvas.set_incident_root("0xroot", stolen_amount=50000.0, timestamp=1700000000)
        
        # Add 3 mule nodes (smurfing pattern)
        for i in range(1, 4):
            mule_addr = f"0x000000000000000000000000000000000000000{i}"
            canvas.get_or_create_node(mule_addr, role=NodeRole.MULE_TRANSIT)
            canvas.add_wire(
                tx_hash=f"0x111111111111111111111111111111111111111111111111111111111111111{i}",
                from_address="0xroot",
                to_address=mule_addr,
                value=15000.0
            )

        # Add CEX deposit
        cex_addr = "0x28c6c06298d514db089934071355e5743bf21d60"
        canvas.get_or_create_node(cex_addr, role=NodeRole.CEX_DEPOSIT, entity_tag="Binance")
        mule1_addr = "0x0000000000000000000000000000000000000001"
        canvas.add_wire(
            tx_hash="0x2222222222222222222222222222222222222222222222222222222222222229",
            from_address=mule1_addr,
            to_address=cex_addr,
            value=14500.0
        )

        assessment = self.macro_classifier.evaluate_canvas(canvas)
        self.assertEqual(assessment.campaign_name, "ORGANIZED_PIG_BUTCHERING_SYNDICATE")
        self.assertEqual(assessment.topological_fingerprint, "SMURFING_TREE_DISPERSION")
        self.assertIn("Binance", assessment.cex_offramps_detected)
        self.assertIn(assessment.investigation_priority, ["HIGH", "CRITICAL"])


if __name__ == "__main__":
    unittest.main()
