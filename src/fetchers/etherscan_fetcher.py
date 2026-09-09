"""
Module: etherscan_fetcher.py
Live blockchain explorer ingestion module for EVM networks (Ethereum, Polygon, Arbitrum, BSC).

Features:
- Built-in Local File Cache: Caches transaction responses to prevent hitting free-tier 5 req/sec rate limits.
- Normalizes Native ETH and ERC-20 token transfers (USDT, USDC) into unified ForensicWire objects.
"""

import os
import json
import time
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from src.core.wire_edge import ForensicWire, TokenType


class EtherscanFetcher:
    """
    Ingests live transaction history from Etherscan-compatible APIs with rate-limit protection.
    """

    def __init__(
        self,
        api_key: str = "YourApiKeyToken",
        base_url: str = "https://api.etherscan.io/api",
        cache_dir: Optional[str] = None
    ):
        self.api_key = api_key
        self.base_url = base_url
        
        if cache_dir is None:
            base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_dir = os.path.join(base_project_dir, "data", "cache")
        
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.last_call_time = 0.0
        self.min_delay_seconds = 0.25 # Max 4 calls/sec (safe under 5 req/sec limit)

    def _get_cache_path(self, address: str, action: str) -> str:
        clean = address.lower()
        return os.path.join(self.cache_dir, f"{clean}_{action}.json")

    def _rate_limit_throttle(self) -> None:
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_delay_seconds:
            time.sleep(self.min_delay_seconds - elapsed)
        self.last_call_time = time.time()

    def fetch_outgoing_transactions(self, address: str) -> List[ForensicWire]:
        """
        Fetches both Native ETH and ERC-20 transfers originating from the address.
        """
        wires: List[ForensicWire] = []
        clean_addr = address.lower()

        # 1. Fetch Normal Transactions
        normal_txs = self._fetch_api_data(
            address=clean_addr,
            action="txlist"
        )
        for tx in normal_txs:
            if tx.get("from", "").lower() == clean_addr and tx.get("isError", "0") == "0":
                val_eth = float(tx.get("value", 0)) / 1e18
                gas_used = float(tx.get("gasUsed", 0))
                gas_price = float(tx.get("gasPrice", 0))
                gas_fee_eth = (gas_used * gas_price) / 1e18

                if val_eth > 0:
                    wire = ForensicWire(
                        tx_hash=tx.get("hash"),
                        from_address=clean_addr,
                        to_address=tx.get("to", "").lower(),
                        value=val_eth,
                        token_symbol="ETH",
                        token_type=TokenType.NATIVE,
                        gas_fee=gas_fee_eth,
                        timestamp=int(tx.get("timeStamp", 0)),
                        block_number=int(tx.get("blockNumber", 0)),
                        is_contract_call=(tx.get("input") != "0x")
                    )
                    wires.append(wire)

        # 2. Fetch ERC-20 Token Transfers (USDT / USDC)
        token_txs = self._fetch_api_data(
            address=clean_addr,
            action="tokentx"
        )
        for tx in token_txs:
            if tx.get("from", "").lower() == clean_addr:
                dec = int(tx.get("tokenDecimal", 6))
                val_token = float(tx.get("value", 0)) / (10 ** dec)
                sym = tx.get("tokenSymbol", "TOKEN")

                wire = ForensicWire(
                    tx_hash=tx.get("hash"),
                    from_address=clean_addr,
                    to_address=tx.get("to", "").lower(),
                    value=val_token,
                    token_symbol=sym,
                    token_type=TokenType.ERC20,
                    gas_fee=0.0,
                    timestamp=int(tx.get("timeStamp", 0)),
                    block_number=int(tx.get("blockNumber", 0)),
                    is_contract_call=True
                )
                wires.append(wire)

        return wires

    def _fetch_api_data(self, address: str, action: str) -> List[Dict[str, Any]]:
        cache_file = self._get_cache_path(address, action)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Throttle live network request
        self._rate_limit_throttle()

        params = {
            "module": "account",
            "action": action,
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 50, # Get top 50 recent transactions
            "sort": "desc",
            "apikey": self.api_key
        }
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CryptoFraudForensics/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                result = data.get("result", [])
                if isinstance(result, list):
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2)
                    return result
        except Exception as e:
            # Fallback on empty if network fails or rate limited
            pass

        return []
