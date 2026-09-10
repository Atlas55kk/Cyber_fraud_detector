"""
Module: tron_fetcher.py
Live and cached blockchain explorer ingestion module for the TRON (TRX / TRC-20) network.

Why this matters for SIH / MHA:
Over 90% of cryptocurrency fraud reported on India's 1930 / cybercrime.gov.in portal
involves USDT transfers on the TRON network (TRC-20), due to negligible transaction fees (<$1)
and high P2P liquidity on offshore exchanges.

Features:
- Ingests TRC-20 USDT transfer events (contract: TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t).
- Normalizes TRON Base58Check addresses into unified ForensicWire objects.
- Built-in Local File Caching in data/cache/tron/ to eliminate redundant API calls.
- Automatic rate-limit throttling (Max 3 calls/sec for TronGrid/Tronscan public tiers).
"""

import os
import json
import time
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from src.core.wire_edge import ForensicWire, TokenType

# The official Tether USD (USDT) contract address on TRON
TRON_USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


class TronFetcher:
    """
    Ingests live TRON transaction history focusing on TRC-20 USDT transfers.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://apilist.tronscanapi.com/api",
        cache_dir: Optional[str] = None
    ):
        self.api_key = api_key
        self.base_url = base_url
        
        if cache_dir is None:
            base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_dir = os.path.join(base_project_dir, "data", "cache", "tron")
        
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.last_call_time = 0.0
        self.min_delay_seconds = 0.35 # ~3 req/sec safe limit for Tronscan

    def _get_cache_path(self, address: str, contract: str) -> str:
        safe_addr = "".join(c for c in address if c.isalnum())
        safe_contract = "".join(c for c in contract if c.isalnum())[:10]
        return os.path.join(self.cache_dir, f"{safe_addr}_{safe_contract}.json")

    def _rate_limit_throttle(self) -> None:
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_delay_seconds:
            time.sleep(self.min_delay_seconds - elapsed)
        self.last_call_time = time.time()

    def fetch_outgoing_transactions(self, address: str) -> List[ForensicWire]:
        """
        Unified interface matching EtherscanFetcher for seamless engine integration.
        """
        return self.fetch_outgoing_trc20_transfers(address)

    def fetch_outgoing_trc20_transfers(
        self,
        address: str,
        token_contract: str = TRON_USDT_CONTRACT
    ) -> List[ForensicWire]:
        """
        Fetches outgoing TRC-20 transfers (defaulting to USDT) from the given TRON address.
        """
        wires: List[ForensicWire] = []
        raw_transfers = self._fetch_tronscan_transfers(address, token_contract)

        for item in raw_transfers:
            # Tronscan transfer/trc20 schema
            from_addr = item.get("from", "") or item.get("from_address", "")
            to_addr = item.get("to", "") or item.get("to_address", "")
            
            # We are tracing forward outgoing flow
            if from_addr.strip() == address.strip():
                raw_amount = float(item.get("amount", 0) or item.get("quant", 0))
                decimals = int(item.get("decimals", 6) or 6)
                value_usdt = raw_amount / (10 ** decimals)
                
                tx_hash = item.get("hash", "") or item.get("transaction_id", "")
                ts_ms = int(item.get("block_timestamp", 0) or item.get("block_ts", 0))
                timestamp_s = ts_ms // 1000 if ts_ms > 1e11 else ts_ms
                block_num = int(item.get("block", 0))
                
                # Default TRON energy fee ~13.5 TRX equivalent or from fee
                fee_sun = float(item.get("fee", 0) or 0)
                fee_trx = (fee_sun / 1e6) if fee_sun > 0 else 13.5

                if value_usdt > 0 and tx_hash:
                    wire = ForensicWire(
                        tx_hash=tx_hash,
                        from_address=from_addr,
                        to_address=to_addr,
                        value=value_usdt,
                        token_symbol="USDT",
                        token_type=TokenType.TRC20,
                        gas_fee=fee_trx,
                        timestamp=timestamp_s,
                        block_number=block_num,
                        is_contract_call=True
                    )
                    wires.append(wire)

        return wires

    def _fetch_tronscan_transfers(self, address: str, contract: str) -> List[Dict[str, Any]]:
        cache_file = self._get_cache_path(address, contract)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Throttle live network request
        self._rate_limit_throttle()

        # Tronscan TRC-20 verified endpoint
        params = {
            "address": address,
            "trc20Id": contract,
            "limit": 50,
            "start": 0,
            "direction": "1"  # Outgoing
        }
        url = f"{self.base_url}/transfer/trc20?{urllib.parse.urlencode(params)}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MHA-Forensics/1.0",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["TRON-PRO-API-KEY"] = self.api_key

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Tronscan returns list under 'data' or 'token_transfers'
                result = data.get("data", []) or data.get("token_transfers", [])
                if isinstance(result, list):
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2)
                    return result
        except Exception:
            # Fallback on empty list if network is unavailable
            pass

        return []

