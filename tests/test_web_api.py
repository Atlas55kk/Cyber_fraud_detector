"""
Unit tests for the FastAPI Web Server and REST API endpoints.
"""

import unittest
from fastapi.testclient import TestClient
from src.web.app import app


class TestWebAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertIn("MHA", data["jurisdiction"])

    def test_dashboard_html_serving(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Crypto Fraud Tracing Engine", response.text)
        self.assertIn("cytoscape", response.text)

    def test_evm_trace_api(self):
        payload = {
            "wallet_address": "0xwallet_s",
            "chain": "evm",
            "stolen_amount": 50000.0,
            "token_symbol": "USDT"
        }
        response = self.client.post("/api/trace", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["chain"], "EVM")
        self.assertIn("is_live", data)
        self.assertIn("data_source", data)
        self.assertGreater(len(data["elements"]), 0)
        self.assertGreater(len(data["actionable_cex"]), 0)
        self.assertEqual(data["stats"]["total_funds_at_exchanges"], 35000.0)
        self.assertIn("ml_intelligence", data)
        self.assertIn("campaign_name", data["ml_intelligence"])
        self.assertGreaterEqual(data["ml_intelligence"]["overall_risk_score"], 0)

    def test_tron_trace_api(self):
        payload = {
            "wallet_address": "TScamSyndicate_Alpha_910283",
            "chain": "tron",
            "stolen_amount": 50000.0,
            "token_symbol": "USDT"
        }
        response = self.client.post("/api/trace", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["chain"], "TRON")
        self.assertIn("is_live", data)
        self.assertIn("data_source", data)
        self.assertGreater(len(data["elements"]), 0)
        self.assertGreater(len(data["actionable_cex"]), 0)

    def test_generate_notice_api(self):
        payload = {
            "ack_number": "NCRP/2026/771029",
            "fir_number": "FIR 112/2026",
            "target_address": "0x28c6c06298d514db089934071355e5743bf21d60"
        }
        response = self.client.post("/api/generate_notice", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("SECTION 94 OF BHARATIYA NAGARIK SURAKSHA SANHITA", data["notice_text"])

    def test_download_notice_pdf_api(self):
        payload = {
            "ack_number": "NCRP/2026/771029",
            "fir_number": "FIR 112/2026",
            "target_address": "0x28c6c06298d514db089934071355e5743bf21d60"
        }
        response = self.client.post("/api/download_notice_pdf", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertGreater(len(response.content), 1000)


if __name__ == "__main__":
    unittest.main()
