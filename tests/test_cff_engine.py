"""
Unit Tests for Crypto Forensic File (.cff) Engine (src/core/cff_engine.py)
Verifies:
- Serialization & Deserialization of cases
- Section 63 BNSS Cryptographic Seal generation
- Tamper-detection on payload modification
"""

import unittest
import json
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import NodeRole
from src.core.wire_edge import ForensicWire, TokenType
from src.reporting.dossier_generator import CaseDetails
from src.core.cff_engine import CryptoForensicFileEngine, CFF_FORMAT_VERSION


class TestCryptoForensicFileEngine(unittest.TestCase):

    def setUp(self):
        self.canvas = WhiteboardCanvas(canvas_id="Test_CFF_Canvas")
        self.canvas.set_incident_root("0xroot_thief", 100000.0, 1700000000)

        # Add mule
        self.canvas.get_or_create_node("0xmule_alpha", role=NodeRole.MULE_TRANSIT)
        self.canvas.add_wire(
            tx_hash="0xtx1_cff",
            from_address="0xroot_thief",
            to_address="0xmule_alpha",
            value=60000.0,
            token_symbol="USDT",
            timestamp=1700000100
        )

        # Add CEX off-ramp
        self.canvas.get_or_create_node(
            "0xcex_coindcx",
            role=NodeRole.CEX_DEPOSIT,
            entity_tag="CoinDCX",
            stolen_taint=1.0,
            stolen_held=59000.0
        )
        self.canvas.add_wire(
            tx_hash="0xtx2_cff",
            from_address="0xmule_alpha",
            to_address="0xcex_coindcx",
            value=59000.0,
            token_symbol="USDT",
            timestamp=1700000200
        )

        self.case = CaseDetails(
            ack_number="NCRP/2026/CFF_TEST",
            fir_number="FIR 88/2026",
            police_station="State Cyber Crime Cell",
            investigating_officer="Inspector V. Rao",
            victim_name="Aggrieved Merchant",
            loss_inr=8500000.0,
            loss_crypto_str="100,000 USDT"
        )

        self.ml_intel = {
            "campaign_name": "RAPID_PEEL_CHAIN_CONSOLIDATION",
            "overall_risk_score": 85,
            "investigation_priority": "CRITICAL",
            "topological_fingerprint": "PEEL_CHAIN_CONVERGENCE",
            "summary": "Rapid peel chain detected heading to CoinDCX deposit."
        }

    def test_export_cff_structure_and_seal(self):
        cff_data = CryptoForensicFileEngine.export_cff(
            self.canvas,
            self.case,
            self.ml_intel,
            chain="EVM",
            victim_address="0xvictim_wallet"
        )

        self.assertEqual(cff_data["cff_version"], CFF_FORMAT_VERSION)
        self.assertIn("cryptographic_seal", cff_data)
        seal = cff_data["cryptographic_seal"]
        self.assertEqual(seal["algorithm"], "SHA-256")
        self.assertEqual(len(seal["integrity_hash"]), 64)
        self.assertEqual(cff_data["metadata"]["victim_address"], "0xvictim_wallet")
        self.assertEqual(len(cff_data["graph"]["nodes"]), 3)
        self.assertEqual(len(cff_data["graph"]["wires"]), 2)

    def test_import_cff_and_verification(self):
        cff_data = CryptoForensicFileEngine.export_cff(
            self.canvas,
            self.case,
            self.ml_intel,
            chain="EVM"
        )
        json_str = json.dumps(cff_data)

        # Import back
        reconstructed_canvas, case, ml_intel, is_tamper_free, status_msg = (
            CryptoForensicFileEngine.import_cff(json_str)
        )

        self.assertTrue(is_tamper_free)
        self.assertIn("VERIFIED", status_msg)
        self.assertEqual(case.ack_number, "NCRP/2026/CFF_TEST")
        self.assertEqual(len(reconstructed_canvas.nodes), 3)
        self.assertEqual(len(reconstructed_canvas.wires), 2)
        self.assertEqual(ml_intel["overall_risk_score"], 85)

    def test_tamper_detection_flags_modification(self):
        cff_data = CryptoForensicFileEngine.export_cff(
            self.canvas,
            self.case,
            self.ml_intel,
            chain="EVM"
        )

        # Deliberately tamper with the stolen value in the wire data
        cff_data["graph"]["wires"][0]["value"] = 999999.0

        reconstructed_canvas, case, ml_intel, is_tamper_free, status_msg = (
            CryptoForensicFileEngine.import_cff(cff_data)
        )

        self.assertFalse(is_tamper_free)
        self.assertIn("TAMPER DETECTED", status_msg)


if __name__ == "__main__":
    unittest.main()
