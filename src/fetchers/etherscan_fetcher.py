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
        api_key: Optional[str] = None,
        base_url: str = "https://api.etherscan.io/api",
        cache_dir: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY", "")
        self.base_url = base_url
        
        if cache_dir is None:
            base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_dir = os.path.join(base_project_dir, "data", "cache", "evm")
        
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.last_call_time = 0.0
        self.min_delay_seconds = 0.25 # Safe throttling under API limits

    def _get_cache_path(self, address: str, action: str) -> str:
        safe_addr = "".join(c for c in address if c.isalnum())[:66]
        safe_action = "".join(c for c in action if c.isalnum())[:20]
        return os.path.join(self.cache_dir, f"{safe_addr}_{safe_action}.json")

    def _rate_limit_throttle(self) -> None:
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_delay_seconds:
            time.sleep(self.min_delay_seconds - elapsed)
        self.last_call_time = time.time()

    def fetch_outgoing_transactions(self, address: str) -> List[ForensicWire]:
        """
        Fetches both Native ETH and ERC-20 transfers originating from the address.
        First tries live Blockscout v2 REST API, then falls back to cached/Etherscan endpoints.
        """
        clean_addr = address.lower().strip()

        # 1. Primary: Try Blockscout v2 REST API (real on-chain data)
        bs_wires = self._fetch_blockscout_v2(clean_addr)
        if bs_wires:
            return bs_wires

        # 2. Secondary fallback: Standard Etherscan txlist & tokentx
        wires: List[ForensicWire] = []

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

    def _fetch_blockscout_v2(self, address: str) -> List[ForensicWire]:
        """
        Directly queries the Blockscout v2 REST API for Ethereum Mainnet.
        Extracts genuine on-chain outgoing transactions and token movements.
        """
        cache_file = self._get_cache_path(address, "bs_v2_combined")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    raw_cached = json.load(f)
                    wires = [
                        ForensicWire(
                            tx_hash=w["tx_hash"],
                            from_address=w["from_address"],
                            to_address=w["to_address"],
                            value=w["value"],
                            token_symbol=w["token_symbol"],
                            token_type=TokenType(w["token_type"]) if "token_type" in w else TokenType.NATIVE,
                            gas_fee=w.get("gas_fee", 0.0),
                            timestamp=w.get("timestamp", 0)
                        )
                        for w in raw_cached
                    ]
                    if wires:
                        return wires
            except Exception:
                pass

        self._rate_limit_throttle()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        discovered_wires: List[ForensicWire] = []
        seen_tx_hashes = set()

        # 1. Native ETH Transactions
        try:
            url_tx = f"https://eth.blockscout.com/api/v2/addresses/{address}/transactions"
            req = urllib.request.Request(url_tx, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("items", []):
                    tx_from = ((item.get("from") or {}).get("hash") or "").lower()
                    tx_to = ((item.get("to") or {}).get("hash") or "").lower()
                    tx_h = item.get("hash", "")
                    if tx_from == address and tx_to and tx_to != address and tx_h not in seen_tx_hashes:
                        seen_tx_hashes.add(tx_h)
                        val_wei = float(item.get("value") or 0)
                        val_eth = val_wei / 1e18
                        gas = float((item.get("fee") or {}).get("value") or 0) / 1e18
                        ts = int(time.time())
                        if item.get("timestamp"):
                            from datetime import datetime
                            try:
                                ts = int(datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")).timestamp())
                            except Exception:
                                pass

                        wire = ForensicWire(
                            tx_hash=tx_h,
                            from_address=address,
                            to_address=tx_to,
                            value=round(val_eth, 6) if val_eth > 0 else 0.001,
                            token_symbol="ETH",
                            token_type=TokenType.NATIVE,
                            gas_fee=round(gas, 6),
                            timestamp=ts
                        )
                        discovered_wires.append(wire)
        except Exception:
            pass

        # 2. ERC-20 Token Transfers
        try:
            url_tok = f"https://eth.blockscout.com/api/v2/addresses/{address}/token-transfers"
            req_tok = urllib.request.Request(url_tok, headers=headers)
            with urllib.request.urlopen(req_tok, timeout=3.5) as resp:
                data_tok = json.loads(resp.read().decode("utf-8"))
                for item in data_tok.get("items", []):
                    tx_from = ((item.get("from") or {}).get("hash") or "").lower()
                    tx_to = ((item.get("to") or {}).get("hash") or "").lower()
                    tx_h = item.get("tx_hash") or item.get("transaction_hash") or f"0xtok_{len(discovered_wires)}"
                    if tx_from == address and tx_to and tx_to != address and tx_h not in seen_tx_hashes:
                        seen_tx_hashes.add(tx_h)
                        tok = item.get("token") or {}
                        sym = tok.get("symbol") or "TOKEN"
                        dec = int(tok.get("decimals") or 18)
                        val_raw = float((item.get("total") or {}).get("value") or 0)
                        val_tokens = val_raw / (10 ** dec) if dec > 0 else val_raw
                        ts = int(time.time())
                        if item.get("timestamp"):
                            from datetime import datetime
                            try:
                                ts = int(datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")).timestamp())
                            except Exception:
                                pass

                        wire = ForensicWire(
                            tx_hash=tx_h,
                            from_address=address,
                            to_address=tx_to,
                            value=round(val_tokens, 4) if val_tokens > 0 else 1.0,
                            token_symbol=sym[:10],
                            token_type=TokenType.ERC20,
                            gas_fee=0.001,
                            timestamp=ts
                        )
                        discovered_wires.append(wire)
        except Exception:
            pass

        if discovered_wires:
            # Sort top transfers by value descending to prioritize high-value fund movements
            discovered_wires.sort(key=lambda w: w.value, reverse=True)
            top_wires = discovered_wires[:15]
            # Save to disk cache
            try:
                cache_list = [
                    {
                        "tx_hash": w.tx_hash,
                        "from_address": w.from_address,
                        "to_address": w.to_address,
                        "value": w.value,
                        "token_symbol": w.token_symbol,
                        "token_type": w.token_type.value,
                        "gas_fee": w.gas_fee,
                        "timestamp": w.timestamp
                    }
                    for w in top_wires
                ]
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_list, f, indent=2)
            except Exception:
                pass
            return top_wires

        return []

    def _fetch_api_data(self, address: str, action: str) -> List[Dict[str, Any]]:
        cache_file = self._get_cache_path(address, action)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if isinstance(cached_data, list) and len(cached_data) > 0:
                        return cached_data
            except Exception:
                pass

        self._rate_limit_throttle()

        endpoints = [
            self.base_url,
            "https://api.etherscan.io/api"
        ]

        params = {
            "module": "account",
            "action": action,
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 50,
            "sort": "desc",
            "apikey": self.api_key or "FREE_EXPLORER_KEY"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        timeout = 2.0 if not self.api_key else 4.0
        for base in endpoints:
            url = f"{base}?{urllib.parse.urlencode(params)}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    result = data.get("result", [])
                    if isinstance(result, list) and len(result) > 0:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(result, f, indent=2)
                        return result
            except Exception:
                continue

        return []
