"""
Module: wire_edge.py
Represents a directed transaction as an attributed "Wire" connecting two Node Boxes.

Design Decision:
- Implements physical execution properties: gas fees burned, nonces, and time deltas.
- Uses __slots__ for high-performance in-memory graph traversal.
"""

from enum import Enum
from typing import Dict, Any, Optional


class TokenType(str, Enum):
    """
    Categorization of the cryptocurrency transferred across the wire.
    """
    NATIVE = "NATIVE"    # Native base asset: ETH, TRX, MATIC, BTC
    ERC20 = "ERC20"      # Smart contract fungible token on EVM (e.g. USDT, USDC, DAI)
    TRC20 = "TRC20"      # Smart contract fungible token on TRON (USDT-TRC20)
    INTERNAL = "INTERNAL"# Internal call transfer originating from smart contract execution


class ForensicWire:
    """
    Compact, attributed directed edge representing a transaction between two wallet nodes.
    """
    __slots__ = (
        "tx_hash",
        "from_address",
        "to_address",
        "value",
        "token_symbol",
        "token_type",
        "gas_fee",
        "timestamp",
        "block_number",
        "tainted_value",
        "taint_ratio",
        "priority_score",
        "is_contract_call",
        "method_signature",
        "metadata"
    )

    def __init__(
        self,
        tx_hash: str,
        from_address: str,
        to_address: str,
        value: float,
        token_symbol: str = "USDT",
        token_type: TokenType = TokenType.ERC20,
        gas_fee: float = 0.0,
        timestamp: int = 0,
        block_number: int = 0,
        tainted_value: float = 0.0,
        taint_ratio: float = 0.0,
        priority_score: float = 0.0,
        is_contract_call: bool = False,
        method_signature: Optional[str] = None
    ):
        clean_from = from_address.strip()
        clean_to = to_address.strip()
        self.tx_hash: str = tx_hash.lower()
        self.from_address: str = clean_from.lower() if clean_from.lower().startswith("0x") else clean_from
        self.to_address: str = clean_to.lower() if clean_to.lower().startswith("0x") else clean_to
        self.value: float = float(value)
        self.token_symbol: str = token_symbol.upper()
        self.token_type: TokenType = token_type
        self.gas_fee: float = float(gas_fee)
        self.timestamp: int = int(timestamp)
        self.block_number: int = int(block_number)
        
        # Taint metrics
        self.tainted_value: float = float(tainted_value)
        self.taint_ratio: float = float(taint_ratio)          # Tainted fraction of this specific transfer
        self.priority_score: float = float(priority_score)    # Calculated f(e) priority score
        
        self.is_contract_call: bool = is_contract_call
        self.method_signature: Optional[str] = method_signature # e.g., "transfer(address,uint256)"
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the wire into a JSON-compatible dictionary for DAG visualization.
        """
        return {
            "tx_hash": self.tx_hash,
            "from": self.from_address,
            "to": self.to_address,
            "value": round(self.value, 4),
            "token_symbol": self.token_symbol,
            "token_type": self.token_type.value,
            "gas_fee": round(self.gas_fee, 6),
            "timestamp": self.timestamp,
            "block_number": self.block_number,
            "tainted_value": round(self.tainted_value, 4),
            "taint_ratio": round(self.taint_ratio, 4),
            "priority_score": round(self.priority_score, 4),
            "is_contract_call": self.is_contract_call,
            "method_signature": self.method_signature,
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        return (
            f"<Wire {self.from_address[:6]}... -> {self.to_address[:6]}... | "
            f"Val={self.value:.2f} {self.token_symbol} | TaintVal={self.tainted_value:.2f} | "
            f"Time={self.timestamp}>"
        )
