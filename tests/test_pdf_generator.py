"""
Unit Tests for Section 94 BNSS PDF Notice Generator (src/reporting/pdf_generator.py)
"""

import unittest
import os
import tempfile
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import ForensicNodeBox, NodeRole
from src.attribution.entity_resolver import EntityInfo
from src.reporting.dossier_generator import CaseDetails
from src.reporting.pdf_generator import LegalNoticePDFGenerator


class TestLegalNoticePDFGenerator(unittest.TestCase):

    def setUp(self):
        self.canvas = WhiteboardCanvas(canvas_id="PDF_Test_Canvas")
        self.canvas.set_incident_root("0xroot_victim_thief", stolen_amount=25000.0, timestamp=1700000000)

        self.target_cex = self.canvas.get_or_create_node(
            address="0x28c6c06298d514db089934071355e5743bf21d60",
            role=NodeRole.CEX_DEPOSIT,
            entity_tag="Binance",
            stolen_taint=0.92,
            stolen_held=23000.0
        )

        self.case = CaseDetails(
            ack_number="NCRP/2026/TEST101",
            fir_number="FIR No. 12/2026",
            police_station="State Cyber Crime Police Station",
            investigating_officer="Inspector A. Kumar",
            victim_name="Verified Complainant",
            loss_inr=2000000.0,
            loss_crypto_str="25,000 USDT"
        )

        self.entity_info = EntityInfo(
            name="Binance",
            category="EXCHANGE",
            node_role=NodeRole.CEX_DEPOSIT,
            jurisdiction="Global / FIU Registered",
            compliance_email="compliance@binance.com",
            fiu_registered=True,
            is_actionable_freeze_target=True
        )

        self.generator = LegalNoticePDFGenerator(self.canvas)

    def test_generate_pdf_bytes_header_and_length(self):
        pdf_bytes = self.generator.generate_pdf_bytes(
            case=self.case,
            target_cex_node=self.target_cex,
            entity_info=self.entity_info
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        # PDF magic bytes
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))

    def test_save_pdf_to_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "Section_94_BNSS_Notice.pdf")
            saved_path = self.generator.save_pdf(
                filepath=out_file,
                case=self.case,
                target_cex_node=self.target_cex,
                entity_info=self.entity_info
            )
            self.assertTrue(os.path.exists(saved_path))
            self.assertGreater(os.path.getsize(saved_path), 1000)


if __name__ == "__main__":
    unittest.main()
