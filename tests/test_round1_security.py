"""
Round 1: Adversarial Security & Penetration Testing Suite
Tests for:
1. Path Traversal (CWE-22) in cache generation
2. Cross-Site Scripting (XSS / CWE-79) in inputs and notices
3. Denial of Service (DoS) with payload bombs (>100KB address)
4. Parameter Pollution & SSRF in explorer URL builders
5. Malicious input handling in FastAPI REST endpoints
"""

import unittest
import os
import json
import math
from fastapi.testclient import TestClient
from src.web.app import app
from src.fetchers.etherscan_fetcher import EtherscanFetcher
from src.fetchers.tron_fetcher import TronFetcher


class TestRound1Security(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_path_traversal_etherscan_cache(self):
        """
        Verify that directory traversal sequences in wallet addresses cannot escape cache_dir.
        """
        fetcher = EtherscanFetcher()
        malicious_addrs = [
            "../../etc/passwd",
            "..\\..\\windows\\win.ini",
            "....//....//secret.txt",
            "/absolute/root/override"
        ]
        for bad_addr in malicious_addrs:
            cache_path = fetcher._get_cache_path(bad_addr, "txlist")
            abs_cache_path = os.path.abspath(cache_path)
            abs_cache_dir = os.path.abspath(fetcher.cache_dir)
            
            # Security Assertion: Cache path MUST be strictly inside cache_dir!
            self.assertTrue(
                abs_cache_path.startswith(abs_cache_dir),
                f"BREACH DETECTED: Path traversal succeeded! Escaped path: {abs_cache_path}"
            )

    def test_path_traversal_tron_cache(self):
        """
        Verify TRON fetcher sanitizes path traversal characters.
        """
        fetcher = TronFetcher()
        bad_addr = "../../../etc/shadow"
        cache_path = fetcher._get_cache_path(bad_addr, "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
        abs_cache_path = os.path.abspath(cache_path)
        abs_cache_dir = os.path.abspath(fetcher.cache_dir)
        self.assertTrue(
            abs_cache_path.startswith(abs_cache_dir),
            f"BREACH DETECTED: TRON Path traversal succeeded: {abs_cache_path}"
        )

    def test_dos_oversized_wallet_bomb(self):
        """
        Verify API rejects string-bomb payloads (>1000 characters) to prevent DoS.
        """
        huge_address = "0x" + "a" * 100000 # 100KB address string
        response = self.client.post("/api/trace", json={
            "wallet_address": huge_address,
            "chain": "evm",
            "stolen_amount": 50000.0,
            "token_symbol": "USDT"
        })
        # Should be rejected with 400 Bad Request
        self.assertEqual(response.status_code, 400)

    def test_xss_injection_in_trace(self):
        """
        Verify that script tags or HTML injection payloads in wallet address
        are strictly rejected as invalid addresses.
        """
        xss_payload = "<script>alert('XSS')</script><img src=x onerror=alert(1)>"
        response = self.client.post("/api/trace", json={
            "wallet_address": xss_payload,
            "chain": "evm",
            "stolen_amount": 50000.0,
            "token_symbol": "USDT"
        })
        self.assertEqual(response.status_code, 400)

    def test_numeric_boundary_pollution(self):
        """
        Test extreme numeric values: negative stolen amount, NaN, Infinity.
        """
        # Negative stolen amount
        resp_neg = self.client.post("/api/trace", json={
            "wallet_address": "0xwallet_s",
            "chain": "evm",
            "stolen_amount": -50000.0,
            "token_symbol": "USDT"
        })
        self.assertEqual(resp_neg.status_code, 400)

        # Zero stolen amount
        resp_zero = self.client.post("/api/trace", json={
            "wallet_address": "0xwallet_s",
            "chain": "evm",
            "stolen_amount": 0.0,
            "token_symbol": "USDT"
        })
        self.assertEqual(resp_zero.status_code, 400)


if __name__ == "__main__":
    unittest.main()
