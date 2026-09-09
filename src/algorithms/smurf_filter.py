"""
Module: smurf_filter.py
Detects Fan-Out / Smurfing (Structuring) laundering topologies.

Formal Definition:
A wallet breaks down a large stolen sum into N smaller, near-equal payments
broadcasted in a short burst window to avoid triggering automated AML threshold alerts.
"""

import numpy as np
from typing import List, Dict, Set, Optional
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import ForensicNodeBox, NodeRole
from src.core.wire_edge import ForensicWire


class SmurfingCluster:
    """
    Forensic grouping representing an identified smurfing / structuring fan-out operation.
    """
    def __init__(self, source_address: str):
        self.source_address = source_address
        self.fan_out_wires: List[ForensicWire] = []
        self.mule_addresses: List[str] = []
        self.total_structured_amount: float = 0.0
        self.mean_amount: float = 0.0
        self.std_dev_amount: float = 0.0
        self.temporal_span_seconds: int = 0

    def calculate_metrics(self) -> None:
        if not self.fan_out_wires:
            return
        
        amounts = [w.value for w in self.fan_out_wires]
        timestamps = [w.timestamp for w in self.fan_out_wires]
        
        self.total_structured_amount = float(sum(amounts))
        self.mean_amount = float(np.mean(amounts))
        self.std_dev_amount = float(np.std(amounts))
        self.temporal_span_seconds = max(timestamps) - min(timestamps)
        self.mule_addresses = [w.to_address for w in self.fan_out_wires]


class SmurfingFilter:
    """
    Identifies smurfing structures and tags recipient accounts as MULE_TRANSIT.
    """

    def __init__(
        self,
        min_fan_out_degree: int = 4,             # At least 4 split recipients
        max_time_window_seconds: int = 3600,     # Within 1 hour
        max_coefficient_of_variation: float = 0.30 # Low variance in amount (< 30% CV)
    ):
        self.min_fan_out_degree = min_fan_out_degree
        self.max_time_window_seconds = max_time_window_seconds
        self.max_cv = max_coefficient_of_variation

    def detect_smurfing_clusters(self, canvas: WhiteboardCanvas) -> List[SmurfingCluster]:
        clusters: List[SmurfingCluster] = []

        for addr, node in canvas.nodes.items():
            outgoing = canvas.get_outgoing_wires(addr)
            if len(outgoing) < self.min_fan_out_degree:
                continue

            # Sort by timestamp
            outgoing_sorted = sorted(outgoing, key=lambda w: w.timestamp)
            t_span = outgoing_sorted[-1].timestamp - outgoing_sorted[0].timestamp
            
            if t_span <= self.max_time_window_seconds:
                amounts = [w.value for w in outgoing_sorted]
                mean_val = np.mean(amounts)
                std_val = np.std(amounts)
                
                # Check Coefficient of Variation (CV = std / mean)
                cv = (std_val / mean_val) if mean_val > 0 else 1.0
                if cv <= self.max_cv:
                    cluster = SmurfingCluster(source_address=addr)
                    cluster.fan_out_wires = outgoing_sorted
                    cluster.calculate_metrics()
                    clusters.append(cluster)
                    
                    # Tag nodes on canvas
                    node.role = NodeRole.SCAMMER
                    for mule_addr in cluster.mule_addresses:
                        mule_node = canvas.nodes.get(mule_addr)
                        if mule_node and mule_node.role == NodeRole.UNKNOWN:
                            mule_node.role = NodeRole.MULE_TRANSIT
                            mule_node.entity_tag = f"Structured Mule (Fan-Out {addr[:6]})"

        return clusters
