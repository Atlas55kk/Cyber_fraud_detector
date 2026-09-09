"""
Module: node_box.py
Represents an individual wallet account as an attributed forensic node ("Box")
on the investigative whiteboard canvas.

Design Decision:
- Uses __slots__ for maximum memory efficiency, allowing hundreds of thousands
  of nodes to reside in memory with minimal RAM usage (~150 bytes per node).
"""

from enum import Enum
from typing import List, Dict, Any, Optional


class NodeRole(str, Enum):
    """
    Forensic classification of a wallet address within the fraud flow.
    """
    VICTIM = "VICTIM"                  # The victim reporting the stolen funds
    SCAMMER = "SCAMMER"                # The primary syndicate / scam ingress wallet
    MULE_TRANSIT = "MULE_TRANSIT"      # Intermediate laundering wallet (fan-out / transit)
    PEEL_CHANGE = "PEEL_CHANGE"        # Fresh ephemeral address receiving bulk remainder in peel chain
    CEX_DEPOSIT = "CEX_DEPOSIT"        # Centralized exchange deposit address (actionable off-ramp / freeze target)
    DEX_ROUTER = "DEX_ROUTER"          # Decentralized exchange router / swap contract (Uniswap, PancakeSwap)
    MIXER_POOL = "MIXER_POOL"          # Privacy pool or mixer contract (e.g., Tornado Cash)
    BRIDGE_CONTRACT = "BRIDGE_CONTRACT"# Cross-chain bridge contract (Hop, Across, ThorChain)
    UNKNOWN = "UNKNOWN"                # Unclassified account


class ForensicNodeBox:
    """
    Compact, attributed node representation of a blockchain account on the forensic canvas.
    """
    __slots__ = (
        "address",
        "role",
        "current_balance",
        "stolen_taint_ratio",
        "stolen_amount_held",
        "gas_burned_total",
        "first_seen_timestamp",
        "last_seen_timestamp",
        "in_degree",
        "out_degree",
        "incoming_wire_hashes",
        "outgoing_wire_hashes",
        "entity_tag",
        "cluster_id",
        "metadata"
    )

    def __init__(
        self,
        address: str,
        role: NodeRole = NodeRole.UNKNOWN,
        current_balance: float = 0.0,
        stolen_taint_ratio: float = 0.0,
        stolen_amount_held: float = 0.0,
        gas_burned_total: float = 0.0,
        first_seen_timestamp: Optional[int] = None,
        last_seen_timestamp: Optional[int] = None,
        entity_tag: Optional[str] = None,
        cluster_id: Optional[str] = None
    ):
        self.address: str = address.lower()
        self.role: NodeRole = role
        self.current_balance: float = float(current_balance)
        self.stolen_taint_ratio: float = float(stolen_taint_ratio)  # 0.0 to 1.0
        self.stolen_amount_held: float = float(stolen_amount_held)
        self.gas_burned_total: float = float(gas_burned_total)
        self.first_seen_timestamp: Optional[int] = first_seen_timestamp
        self.last_seen_timestamp: Optional[int] = last_seen_timestamp
        
        self.in_degree: int = 0
        self.out_degree: int = 0
        self.incoming_wire_hashes: List[str] = []
        self.outgoing_wire_hashes: List[str] = []
        
        self.entity_tag: Optional[str] = entity_tag      # e.g., "Binance Deposit", "CoinDCX Hot Wallet"
        self.cluster_id: Optional[str] = cluster_id      # e.g., "Syndicate_Cluster_Alpha"
        self.metadata: Dict[str, Any] = {}

    def update_timestamps(self, timestamp: int) -> None:
        """
        Maintains the temporal bounding interval [first_seen, last_seen].
        """
        if self.first_seen_timestamp is None or timestamp < self.first_seen_timestamp:
            self.first_seen_timestamp = timestamp
        if self.last_seen_timestamp is None or timestamp > self.last_seen_timestamp:
            self.last_seen_timestamp = timestamp

    def add_incoming_wire(self, tx_hash: str) -> None:
        if tx_hash not in self.incoming_wire_hashes:
            self.incoming_wire_hashes.append(tx_hash)
            self.in_degree = len(self.incoming_wire_hashes)

    def add_outgoing_wire(self, tx_hash: str) -> None:
        if tx_hash not in self.outgoing_wire_hashes:
            self.outgoing_wire_hashes.append(tx_hash)
            self.out_degree = len(self.outgoing_wire_hashes)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the node box into a JSON-compatible dictionary for UI canvas rendering.
        """
        return {
            "address": self.address,
            "role": self.role.value,
            "current_balance": self.current_balance,
            "stolen_taint_ratio": round(self.stolen_taint_ratio, 4),
            "stolen_amount_held": round(self.stolen_amount_held, 4),
            "gas_burned_total": round(self.gas_burned_total, 6),
            "first_seen_timestamp": self.first_seen_timestamp,
            "last_seen_timestamp": self.last_seen_timestamp,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "incoming_wires_count": len(self.incoming_wire_hashes),
            "outgoing_wires_count": len(self.outgoing_wire_hashes),
            "entity_tag": self.entity_tag,
            "cluster_id": self.cluster_id,
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        return (
            f"<NodeBox {self.address[:8]}...{self.address[-4:]} | "
            f"Role={self.role.value} | Taint={self.stolen_taint_ratio*100:.1f}% | "
            f"Held={self.stolen_amount_held:.2f}>"
        )
