"""
Module: taint_engine.py
Implements formal mathematical accounting models for cryptocurrency taint propagation:
1. Proportional Haircut (Conservation of Mass)
2. FIFO (First-In, First-Out Chronological)
3. Poison (Binary Contamination)

Includes gas fee burn accounting and minimum taint threshold pruning rules.
"""

from enum import Enum
from typing import Tuple
from src.core.node_box import ForensicNodeBox
from src.core.wire_edge import ForensicWire


class TaintModel(str, Enum):
    HAIRCUT = "HAIRCUT"  # Proportional dilution (Standard forensic accounting)
    FIFO = "FIFO"        # First-In, First-Out chronological consumption
    POISON = "POISON"    # Binary 100% contamination


class TaintEngine:
    """
    Mathematical engine responsible for propagating and tracking stolen fund flow.
    """

    def __init__(
        self,
        model: TaintModel = TaintModel.HAIRCUT,
        min_taint_threshold: float = 0.02,     # Minimum taint ratio (2%) below which branches are pruned
        min_tainted_value: float = 1.0          # Minimum absolute value (e.g. 1.0 USDT) to prevent dust spam
    ):
        self.model: TaintModel = model
        self.min_taint_threshold: float = min_taint_threshold
        self.min_tainted_value: float = min_tainted_value

    def propagate_taint(
        self,
        sender_node: ForensicNodeBox,
        receiver_node: ForensicNodeBox,
        wire: ForensicWire
    ) -> Tuple[float, float, bool]:
        """
        Calculates how much taint is passed from sender to receiver across a wire.
        
        Returns:
            (tainted_value, new_receiver_taint_ratio, is_pruned)
        """
        transfer_val = wire.value
        sender_taint_ratio = sender_node.stolen_taint_ratio
        
        # 1. Calculate tainted value of the outgoing wire
        if self.model == TaintModel.HAIRCUT:
            # Proportional Haircut: wire carries exact fraction of sender's current taint
            tainted_value = transfer_val * sender_taint_ratio
            wire_taint_ratio = sender_taint_ratio
        elif self.model == TaintModel.POISON:
            # Poison: Any non-zero taint marks the whole transfer as tainted
            tainted_value = transfer_val if sender_taint_ratio > 0.0 else 0.0
            wire_taint_ratio = 1.0 if sender_taint_ratio > 0.0 else 0.0
        elif self.model == TaintModel.FIFO:
            # FIFO: Outgoing transfer consumes stolen funds up to the amount held
            tainted_value = min(transfer_val, sender_node.stolen_amount_held)
            wire_taint_ratio = (tainted_value / transfer_val) if transfer_val > 0 else 0.0
        else:
            tainted_value = transfer_val * sender_taint_ratio
            wire_taint_ratio = sender_taint_ratio

        # Deduct transfer amount from sender's held stolen funds
        sender_node.stolen_amount_held = max(0.0, sender_node.stolen_amount_held - tainted_value)
        if sender_node.current_balance > 0:
            sender_node.current_balance = max(0.0, sender_node.current_balance - transfer_val)
        
        # Track gas fee burned by sender
        if wire.gas_fee > 0:
            sender_node.gas_burned_total += wire.gas_fee
            if sender_node.current_balance > 0:
                sender_node.current_balance = max(0.0, sender_node.current_balance - wire.gas_fee)

        # 2. Check Pruning Criteria
        is_pruned = False
        if wire_taint_ratio < self.min_taint_threshold or tainted_value < self.min_tainted_value:
            is_pruned = True

        # 3. Update Wire Metrics
        wire.tainted_value = tainted_value
        wire.taint_ratio = wire_taint_ratio

        # 4. Propagate into Receiver Node (Conservation of Mass)
        new_receiver_balance = receiver_node.current_balance + transfer_val
        new_stolen_held = receiver_node.stolen_amount_held + tainted_value
        
        receiver_node.current_balance = new_receiver_balance
        receiver_node.stolen_amount_held = new_stolen_held
        
        if new_receiver_balance > 0:
            receiver_node.stolen_taint_ratio = min(1.0, new_stolen_held / new_receiver_balance)
        else:
            receiver_node.stolen_taint_ratio = 0.0

        receiver_node.update_timestamps(wire.timestamp)
        sender_node.update_timestamps(wire.timestamp)

        # Wire association
        sender_node.add_outgoing_wire(wire.tx_hash)
        receiver_node.add_incoming_wire(wire.tx_hash)

        return (tainted_value, receiver_node.stolen_taint_ratio, is_pruned)
