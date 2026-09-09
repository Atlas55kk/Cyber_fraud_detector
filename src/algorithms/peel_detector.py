"""
Module: peel_detector.py
Implements automated Peel Chain pattern recognition and cluster collapsing for
Account-Based (EVM & TRON) transaction graphs.

Based on mathematical formalizations from:
- Kappos et al. (2022), "How to Peel a Million: Validating and Expanding Bitcoin Clusters"
- Meiklejohn et al. (IMC 2013)
"""

from typing import List, Dict, Set, Optional, Tuple
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import ForensicNodeBox, NodeRole
from src.core.wire_edge import ForensicWire


class PeelHop:
    """
    Represents an individual stage in a sequential peel chain.
    """
    def __init__(
        self,
        transit_address: str,
        peel_wire_hash: str,
        peeled_address: str,
        peeled_amount: float,
        forward_wire_hash: str,
        forward_address: str,
        forward_amount: float
    ):
        self.transit_address = transit_address
        self.peel_wire_hash = peel_wire_hash
        self.peeled_address = peeled_address
        self.peeled_amount = peeled_amount
        self.forward_wire_hash = forward_wire_hash
        self.forward_address = forward_address
        self.forward_amount = forward_amount


class PeelChain:
    """
    A sequence of peel hops representing an automated stripping operation.
    """
    def __init__(self, root_address: str):
        self.root_address = root_address
        self.hops: List[PeelHop] = []
        self.total_peeled_amount: float = 0.0
        self.total_forwarded_amount: float = 0.0

    def add_hop(self, hop: PeelHop) -> None:
        self.hops.append(hop)
        self.total_peeled_amount += hop.peeled_amount
        self.total_forwarded_amount = hop.forward_amount

    @property
    def length(self) -> int:
        return len(self.hops)

    @property
    def peeled_destinations(self) -> List[str]:
        return [h.peeled_address for h in self.hops]


class PeelChainDetector:
    """
    Scans the Whiteboard Canvas to detect, isolate, and collapse peel chains.
    """

    def __init__(
        self,
        max_peel_ratio: float = 0.35,     # The peel must be <= 35% of total outflow
        min_chain_length: int = 2          # At least 2 sequential peels to form a chain
    ):
        self.max_peel_ratio = max_peel_ratio
        self.min_chain_length = min_chain_length

    def detect_peel_chains(self, canvas: WhiteboardCanvas) -> List[PeelChain]:
        """
        Traverses the canvas graph looking for asymmetric 2-way splits that form chains.
        """
        chains: List[PeelChain] = []
        visited_nodes: Set[str] = set()

        for addr, node in canvas.nodes.items():
            if addr in visited_nodes:
                continue

            outgoing = canvas.get_outgoing_wires(addr)
            # A peel hop typically has 2 outgoing wires within a short time frame
            if len(outgoing) == 2:
                w1, w2 = outgoing[0], outgoing[1]
                tot = w1.value + w2.value
                if tot == 0:
                    continue

                # Identify smaller vs larger
                if w1.value < w2.value:
                    peel_w, bulk_w = w1, w2
                else:
                    peel_w, bulk_w = w2, w1

                ratio = peel_w.value / tot
                if ratio <= self.max_peel_ratio:
                    # Potential peel start! Trace chain forward
                    chain = self._trace_peel_sequence(canvas, addr, visited_nodes)
                    if chain.length >= self.min_chain_length:
                        chains.append(chain)

        return chains

    def _trace_peel_sequence(
        self,
        canvas: WhiteboardCanvas,
        start_addr: str,
        visited_nodes: Set[str]
    ) -> PeelChain:
        chain = PeelChain(root_address=start_addr)
        curr_addr = start_addr

        while True:
            visited_nodes.add(curr_addr)
            outgoing = canvas.get_outgoing_wires(curr_addr)
            if len(outgoing) != 2:
                break

            w1, w2 = outgoing[0], outgoing[1]
            tot = w1.value + w2.value
            if tot == 0:
                break

            if w1.value < w2.value:
                peel_w, bulk_w = w1, w2
            else:
                peel_w, bulk_w = w2, w1

            if (peel_w.value / tot) > self.max_peel_ratio:
                break

            hop = PeelHop(
                transit_address=curr_addr,
                peel_wire_hash=peel_w.tx_hash,
                peeled_address=peel_w.to_address,
                peeled_amount=peel_w.value,
                forward_wire_hash=bulk_w.tx_hash,
                forward_address=bulk_w.to_address,
                forward_amount=bulk_w.value
            )
            chain.add_hop(hop)

            # Move to next hop
            next_addr = bulk_w.to_address
            if next_addr in visited_nodes or next_addr == curr_addr:
                break
            curr_addr = next_addr

        return chain
