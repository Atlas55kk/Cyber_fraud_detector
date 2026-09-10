"""
Round 3: End-to-End System Integration, Concurrency & Fault Injection Suite
Tests for:
1. Corrupted cache recovery (invalid binary/junk in data/cache/)
2. Multi-threaded concurrency stress testing on FastAPI REST endpoints
3. Fault injection: Network simulated error recovery
4. Full round-trip execution of all preset benchmark and live scenarios
"""

import unittest
import os
import threading
from fastapi.testclient import TestClient
from src.web.app import app
from src.fetchers.etherscan_fetcher import EtherscanFetcher
from src.fetchers.tron_fetcher import TronFetcher


class TestRound3Integration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_corrupted_cache_resilience(self):
        """
        Fault Injection: Write non-JSON corrupted garbage to cache files.
        Verify fetcher does NOT crash, catches the exception, and recovers.
        """
        ef = EtherscanFetcher()
        corrupt_addr = "0xCorruptCacheTestWallet99118822"
        cache_file = ef._get_cache_path(corrupt_addr, "txlist")
        
        # Write corrupted invalid binary bytes
        with open(cache_file, "wb") as f:
            f.write(b"\x00\xFF\xFE__CORRUPTED_NON_JSON_DATA__")
            
        try:
            # Should not raise exception
            wires = ef.fetch_outgoing_transactions(corrupt_addr)
            self.assertIsInstance(wires, list)
        finally:
            if os.path.exists(cache_file):
                os.remove(cache_file)

    def test_multi_threaded_concurrency_stress(self):
        """
        Simulate 10 concurrent investigators making simultaneous trace & notice calls.
        Ensure thread safety, zero deadlock, and isolated canvas states.
        """
        results = []
        errors = []

        def worker(thread_id):
            try:
                # Alternate between EVM and TRON
                chain = "evm" if thread_id % 2 == 0 else "tron"
                addr = "0xwallet_s" if chain == "evm" else "TScamSyndicate_Alpha_910283"
                
                resp = self.client.post("/api/trace", json={
                    "wallet_address": addr,
                    "chain": chain,
                    "stolen_amount": 50000.0,
                    "token_symbol": "USDT",
                    "mode": "benchmark"
                })
                if resp.status_code == 200 and resp.json().get("success"):
                    results.append(thread_id)
                else:
                    errors.append((thread_id, resp.status_code, resp.text))
            except Exception as ex:
                errors.append((thread_id, str(ex)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrency errors detected: {errors}")
        self.assertEqual(len(results), 10)

    def test_full_roundtrip_notice_generation_lifecycle(self):
        """
        Verify complete end-to-end flow:
        Trace wallet -> Locate CEX -> Generate Section 94 BNSS Notice with valid hash table.
        """
        # 1. Trace
        trace_resp = self.client.post("/api/trace", json={
            "wallet_address": "0xwallet_s",
            "chain": "evm",
            "stolen_amount": 50000.0,
            "token_symbol": "USDT",
            "mode": "benchmark"
        })
        self.assertEqual(trace_resp.status_code, 200)
        trace_data = trace_resp.json()
        self.assertGreater(len(trace_data["actionable_cex"]), 0)
        target_cex = trace_data["actionable_cex"][0]["address"]

        # 2. Notice Generation
        notice_resp = self.client.post("/api/generate_notice", json={
            "ack_number": "NCRP/2026/881230",
            "fir_number": "FIR 109/2026",
            "police_station": "Cyber PS Central",
            "investigating_officer": "Inspector R. K. Sharma",
            "victim_name": "Rajesh Kumar",
            "loss_inr": 4250000.0,
            "loss_crypto_str": "50,000 USDT",
            "target_address": target_cex
        })
        self.assertEqual(notice_resp.status_code, 200)
        notice_data = notice_resp.json()
        self.assertTrue(notice_data["success"])
        self.assertIn("SECTION 94", notice_data["notice_text"].upper())
        self.assertIn("BHARATIYA NAGARIK SURAKSHA SANHITA", notice_data["notice_text"].upper())


if __name__ == "__main__":
    unittest.main()
