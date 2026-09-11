"""
Module: rpc_client.py
Direct Raw Blockchain JSON-RPC Client for EVM and Direct Node Interrogation.

Allows law enforcement forensic workstations to query local geth/erigon nodes
or decentralized public RPC relays directly, eliminating reliance on third-party
web explorer APIs (Etherscan/Blockscout) and defending against API outages.
"""

import os
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from src.core.wire_edge import ForensicWire, TokenType

ERC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378d5795503048344301f459ff7335787a130f"

DEFAULT_EVM_RPCS = [
    "https://cloudflare-eth.com",
    "https://rpc.ankr.com/eth",
    "https://ethereum-rpc.publicnode.com"
]


class DirectNodeRPCClient:
    """
    Direct Web3 JSON-RPC client with multi-provider failover, timeout protection,
    and automatic wire conversion for EVM blockchains.
    """

    def __init__(
        self,
        rpc_endpoints: Optional[List[str]] = None,
        timeout_seconds: float = 6.0,
        cache_dir: Optional[str] = None
    ):
        self.endpoints = rpc_endpoints or list(DEFAULT_EVM_RPCS)
        self.active_endpoint_index = 0
        self.timeout = timeout_seconds
        
        if cache_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_dir = os.path.join(base_dir, "data", "cache", "rpc")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    @property
    def current_endpoint(self) -> str:
        return self.endpoints[self.active_endpoint_index]

    def _rotate_endpoint(self) -> None:
        self.active_endpoint_index = (self.active_endpoint_index + 1) % len(self.endpoints)

    def call_rpc(self, method: str, params: List[Any]) -> Any:
        """
        Executes a raw JSON-RPC 2.0 call with failover across configured endpoints.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "User-Agent": "CyberFraudForensics/1.0"}

        last_error = None
        for _ in range(len(self.endpoints)):
            endpoint = self.current_endpoint
            try:
                req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    if "error" in resp_json:
                        raise RuntimeError(f"RPC error from {endpoint}: {resp_json['error']}")
                    return resp_json.get("result")
            except Exception as e:
                last_error = e
                self._rotate_endpoint()

        raise ConnectionError(f"All RPC endpoints failed. Last error: {last_error}")

    def get_block_number(self) -> int:
        """Returns the latest block number."""
        res = self.call_rpc("eth_blockNumber", [])
        return int(res, 16) if isinstance(res, str) else 0

    def get_balance(self, address: str) -> float:
        """Returns the native balance in ETH."""
        res = self.call_rpc("eth_getBalance", [address.lower(), "latest"])
        if isinstance(res, str):
            return int(res, 16) / 1e18
        return 0.0

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Fetches raw transaction details by hash."""
        return self.call_rpc("eth_getTransactionByHash", [tx_hash])

    def fetch_erc20_transfer_logs(
        self,
        target_address: str,
        from_block: str = "earliest",
        to_block: str = "latest",
        token_contract: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries logs for ERC-20 transfers originating from target_address.
        """
        clean_addr = target_address.lower().replace("0x", "")
        padded_from = "0x000000000000000000000000" + clean_addr

        filter_params: Dict[str, Any] = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": [
                ERC20_TRANSFER_TOPIC,
                padded_from
            ]
        }
        if token_contract:
            filter_params["address"] = token_contract.lower()

        logs = self.call_rpc("eth_getLogs", [filter_params])
        return logs if isinstance(logs, list) else []

    def parse_log_to_wire(self, log_entry: Dict[str, Any], token_symbol: str = "USDT") -> Optional[ForensicWire]:
        """
        Converts an on-chain ERC-20 Transfer log into a ForensicWire instance.
        """
        try:
            tx_hash = log_entry.get("transactionHash", "")
            topics = log_entry.get("topics", [])
            if len(topics) < 3:
                return None

            from_addr = "0x" + topics[1][-40:]
            to_addr = "0x" + topics[2][-40:]
            data_hex = log_entry.get("data", "0x0")
            raw_value = int(data_hex, 16) if isinstance(data_hex, str) else 0

            # Default to USDT (6 decimals) if symbol is USDT, else 18
            decimals = 6 if token_symbol.upper() in ["USDT", "USDC"] else 18
            token_val = raw_value / (10 ** decimals)

            return ForensicWire(
                tx_hash=tx_hash,
                from_address=from_addr.lower(),
                to_address=to_addr.lower(),
                value=token_val,
                token_symbol=token_symbol.upper(),
                token_type=TokenType.ERC20,
                gas_fee=0.0,
                block_number=int(log_entry.get("blockNumber", "0x0"), 16),
                is_contract_call=False
            )
        except Exception:
            return None
