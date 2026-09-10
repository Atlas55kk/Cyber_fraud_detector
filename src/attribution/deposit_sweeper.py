"""
Module: deposit_sweeper.py
Implements Friedhelm Victor's (Financial Cryptography 2020) Deposit Address Forwarding
and Sweeping Heuristic for on-the-fly Centralized Exchange (CEX) clustering.

Theoretical Foundation:
When a user or scammer deposits cryptocurrency into a centralized exchange (Binance, CoinDCX, WazirX),
the exchange assigns a unique, ephemeral "User Deposit Proxy" address.
Shortly after receiving funds, the exchange's automated treasury daemon executes a "Sweep Transaction":
    UserDepositProxy --(Sweep ~100% of balance)--> Exchange Hot Wallet

The Sweeping Heuristic:
If an unclassified address 'u':
1. Receives tainted stolen funds.
2. Has an outgoing transaction where >= 90% of its incoming balance is forwarded
   directly into a known Exchange Hot Wallet.
3. Has low out-degree (typically 1 sweep transaction) and near-zero remaining balance.

Then 'u' is dynamically clustered as a verified CEX User Deposit Address for that exchange,
allowing law enforcement to immediately serve a Section 94 BNSS freeze order on the account
associated with that specific deposit proxy!
"""

from typing import List, Optional, Tuple, Dict, Any
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import ForensicNodeBox, NodeRole
from src.core.wire_edge import ForensicWire
from src.attribution.entity_resolver import EntityResolver, EntityInfo


class SweepAttributionResult:
    """
    Forensic record of a detected exchange deposit sweep.
    """
    __slots__ = (
        "deposit_proxy_address",
        "exchange_name",
        "hot_wallet_address",
        "swept_amount",
        "sweep_tx_hash",
        "sweep_ratio",
        "is_clustered"
    )

    def __init__(
        self,
        deposit_proxy_address: str,
        exchange_name: str,
        hot_wallet_address: str,
        swept_amount: float,
        sweep_tx_hash: str,
        sweep_ratio: float,
        is_clustered: bool = True
    ):
        self.deposit_proxy_address = deposit_proxy_address.lower()
        self.exchange_name = exchange_name
        self.hot_wallet_address = hot_wallet_address.lower()
        self.swept_amount = float(swept_amount)
        self.sweep_tx_hash = sweep_tx_hash
        self.sweep_ratio = float(sweep_ratio)
        self.is_clustered = is_clustered

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deposit_proxy_address": self.deposit_proxy_address,
            "exchange_name": self.exchange_name,
            "hot_wallet_address": self.hot_wallet_address,
            "swept_amount": round(self.swept_amount, 2),
            "sweep_tx_hash": self.sweep_tx_hash,
            "sweep_ratio": round(self.sweep_ratio, 4),
            "is_clustered": self.is_clustered
        }


class DepositSweeper:
    """
    Evaluates candidate transit nodes to detect exchange sweeping signatures in real time.
    """

    def __init__(
        self,
        entity_resolver: EntityResolver,
        min_sweep_ratio: float = 0.85 # At least 85% of balance forwarded to hot wallet
    ):
        self.entity_resolver = entity_resolver
        self.min_sweep_ratio = min_sweep_ratio

    def evaluate_node_for_sweep(
        self,
        candidate_node: ForensicNodeBox,
        outgoing_wires: List[ForensicWire]
    ) -> Optional[SweepAttributionResult]:
        """
        Inspects outgoing wires from an unclassified candidate node.
        If an outgoing wire feeds directly into a recognized exchange hot wallet,
        clusters the candidate node as an Actionable CEX Deposit Proxy.
        """
        if not outgoing_wires:
            return None

        # If already classified as CEX_DEPOSIT, skip
        if candidate_node.role == NodeRole.CEX_DEPOSIT:
            return None

        total_received = candidate_node.current_balance + sum(w.value for w in outgoing_wires)
        if total_received <= 0:
            return None

        for wire in outgoing_wires:
            dest_entity = self.entity_resolver.resolve(wire.to_address)
            
            # Check if destination is a recognized Exchange Hot Wallet
            if dest_entity and "Hot Wallet" in dest_entity.name:
                sweep_ratio = wire.value / total_received if total_received > 0 else 0.0
                
                if sweep_ratio >= self.min_sweep_ratio:
                    exchange_name = dest_entity.name.split(":")[0].strip()
                    
                    # 1. Dynamically update candidate node role
                    candidate_node.role = NodeRole.CEX_DEPOSIT
                    candidate_node.entity_tag = f"{exchange_name}: User Deposit Proxy"
                    
                    # 2. Register into entity resolver so future queries recognize this proxy
                    self.entity_resolver.register_custom_deposit(
                        deposit_address=candidate_node.address,
                        exchange_name=exchange_name,
                        compliance_email=dest_entity.compliance_email
                    )

                    return SweepAttributionResult(
                        deposit_proxy_address=candidate_node.address,
                        exchange_name=exchange_name,
                        hot_wallet_address=wire.to_address,
                        swept_amount=wire.value,
                        sweep_tx_hash=wire.tx_hash,
                        sweep_ratio=sweep_ratio,
                        is_clustered=True
                    )

        return None
