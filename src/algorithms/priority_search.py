"""
Module: priority_search.py
Implements Heuristic-Guided Best-First Search with Taint Pruning (H-BFSTP)
over directed temporal blockchain transaction multigraphs.

Objective Function:
f(e) = alpha * T(e) + beta * V(w) + gamma * Delta(tau) + delta * A(v)

Guarantees:
- Strictly bounds graph exploration to prevent O(b^d) combinatorial explosion.
- Terminates branches that hit known CEX deposit addresses or drop below minimum taint.
"""

import math
import heapq
from typing import List, Dict, Set, Optional, Tuple, Callable, Any
from src.core.node_box import ForensicNodeBox, NodeRole
from src.core.wire_edge import ForensicWire
from src.core.canvas import WhiteboardCanvas
from src.core.taint_engine import TaintEngine
from src.attribution.entity_resolver import EntityResolver
from src.attribution.deposit_sweeper import DepositSweeper


class SearchConfig:
    """
    Hyperparameters governing heuristic search traversal and pruning cutoffs.
    """
    def __init__(
        self,
        max_hops: int = 5,
        max_nodes_budget: int = 500,
        alpha_taint: float = 0.35,      # Weight for taint ratio
        beta_value: float = 0.25,       # Weight for absolute stolen value
        gamma_time: float = 0.20,       # Weight for temporal proximity
        delta_attr: float = 0.20,       # Weight for known exchange attribution
        time_decay_half_life_days: float = 7.0,
        min_taint_ratio: float = 0.02,  # 2% minimum taint cutoff
        min_transfer_usd: float = 1.0   # $1.0 minimum dust filter
    ):
        self.max_hops = max_hops
        self.max_nodes_budget = max_nodes_budget
        self.alpha_taint = alpha_taint
        self.beta_value = beta_value
        self.gamma_time = gamma_time
        self.delta_attr = delta_attr
        self.lambda_decay = math.log(2) / (time_decay_half_life_days * 86400)
        self.min_taint_ratio = min_taint_ratio
        self.min_transfer_usd = min_transfer_usd


class PrioritySearchEngine:
    """
    Executes Priority-Queue Best-First Graph Traversal to follow stolen funds
    to Centralized Exchange deposit off-ramps.
    """

    def __init__(
        self,
        canvas: WhiteboardCanvas,
        taint_engine: TaintEngine,
        entity_resolver: EntityResolver,
        config: Optional[SearchConfig] = None
    ):
        self.canvas: WhiteboardCanvas = canvas
        self.taint_engine: TaintEngine = taint_engine
        self.entity_resolver: EntityResolver = entity_resolver
        self.config: SearchConfig = config or SearchConfig()
        self.deposit_sweeper: DepositSweeper = DepositSweeper(self.entity_resolver)

    def compute_edge_priority(
        self,
        wire: ForensicWire,
        sender_node: ForensicNodeBox,
        receiver_node: ForensicNodeBox,
        incident_time: int,
        initial_stolen_amount: float
    ) -> float:
        """
        Calculates f(e) priority score for candidate edge.
        Higher score = earlier queue expansion.
        """
        # 1. Taint Ratio Component (0.0 to 1.0)
        taint_score = wire.taint_ratio

        # 2. Value Significance Component (0.0 to 1.0)
        if initial_stolen_amount > 0:
            value_score = min(1.0, wire.tainted_value / initial_stolen_amount)
        else:
            value_score = 0.0

        # 3. Temporal Decay Component (exp(-lambda * dt))
        dt = max(0, wire.timestamp - incident_time)
        time_score = math.exp(-self.config.lambda_decay * dt)

        # 4. Attribution Prior Component
        attr_score = 0.0
        entity = self.entity_resolver.resolve(receiver_node.address)
        if entity:
            receiver_node.role = entity.node_role
            receiver_node.entity_tag = entity.name
            if entity.is_actionable_freeze_target:
                attr_score = 1.0  # Strong boost to CEX deposit targets!
            elif entity.node_role == NodeRole.MIXER_POOL:
                attr_score = 0.8

        f_e = (
            self.config.alpha_taint * taint_score +
            self.config.beta_value * value_score +
            self.config.gamma_time * time_score +
            self.config.delta_attr * attr_score
        )
        wire.priority_score = f_e
        return f_e

    def run_trace(
        self,
        fetch_outgoing_wires_func: Callable[[str], List[ForensicWire]],
        on_step: Optional[Callable[[str, Any], None]] = None
    ) -> List[ForensicNodeBox]:
        """
        Runs the priority search starting from the canvas incident root.
        
        Args:
            fetch_outgoing_wires_func: Function taking an address and returning its outgoing wires
                                       (can be live API fetcher or mock generator).
            on_step: Optional callback for streaming discovery events (event_type, data).
        
        Returns:
            List of identified actionable CEX deposit nodes where stolen funds landed.
        """
        root_addr = self.canvas.incident_root_address
        if not root_addr:
            raise ValueError("Canvas incident root must be set prior to running trace.")

        root_node = self.canvas.nodes[root_addr]
        incident_time = self.canvas.incident_timestamp or 0
        initial_stolen = self.canvas.initial_stolen_amount

        if on_step:
            on_step("node", self.canvas.node_to_cytoscape(root_node))

        # Priority Queue holds: (-priority_score, hop_count, wire_hash, sender_addr, receiver_addr)
        # Note: heapq in Python is a min-heap, so negative score gives max-priority.
        pq: List[Tuple[float, int, str, str, str]] = []
        
        visited_nodes: Set[str] = {root_addr}
        visited_wires: Set[str] = set()
        actionable_cex_found: List[ForensicNodeBox] = []

        # Bootstrap: Fetch initial wires from root
        initial_wires = fetch_outgoing_wires_func(root_addr)
        for w in initial_wires:
            self.canvas.add_wire(
                tx_hash=w.tx_hash,
                from_address=w.from_address,
                to_address=w.to_address,
                value=w.value,
                token_symbol=w.token_symbol,
                token_type=w.token_type,
                gas_fee=w.gas_fee,
                timestamp=w.timestamp,
                block_number=w.block_number
            )
            receiver_node = self.canvas.get_or_create_node(w.to_address)
            self.taint_engine.propagate_taint(root_node, receiver_node, w)
            
            score = self.compute_edge_priority(w, root_node, receiver_node, incident_time, initial_stolen)
            heapq.heappush(pq, (-score, 1, w.tx_hash, root_addr, w.to_address))

            if on_step:
                on_step("node", self.canvas.node_to_cytoscape(receiver_node))
                on_step("wire", self.canvas.wire_to_cytoscape(w))

        expanded_node_count = 1

        # Traversal Loop
        while pq and expanded_node_count < self.config.max_nodes_budget:
            neg_score, hop, tx_h, sender_addr, current_addr = heapq.heappop(pq)
            score = -neg_score
            visited_wires.add(tx_h)

            curr_node = self.canvas.nodes.get(current_addr)
            if not curr_node:
                continue

            # Check if this node is an attributed Exchange Deposit Address
            entity = self.entity_resolver.resolve(current_addr)
            if entity and entity.is_actionable_freeze_target:
                curr_node.role = NodeRole.CEX_DEPOSIT
                curr_node.entity_tag = entity.name
                if curr_node not in actionable_cex_found and curr_node.stolen_amount_held > 0:
                    actionable_cex_found.append(curr_node)
                # Terminal condition: We found the cash-out off-ramp, stop expanding this branch!
                continue

            # Check hop limit
            if hop >= self.config.max_hops:
                continue

            # If node already expanded, skip re-expansion
            if current_addr in visited_nodes:
                continue
            visited_nodes.add(current_addr)
            expanded_node_count += 1

            # Fetch outgoing wires for current node
            outgoing_wires = fetch_outgoing_wires_func(current_addr)
            
            # Check for Exchange Deposit Sweeping Heuristic (Victor 2020)
            sweep_result = self.deposit_sweeper.evaluate_node_for_sweep(curr_node, outgoing_wires)
            if sweep_result and curr_node not in actionable_cex_found and curr_node.stolen_amount_held > 0:
                actionable_cex_found.append(curr_node)

            if on_step:
                on_step("hop", {"hop": hop, "address": current_addr, "nodes_count": len(self.canvas.nodes), "wires_count": len(self.canvas.wires)})

            for w in outgoing_wires:
                if w.tx_hash in visited_wires:
                    continue

                # Add to canvas and propagate taint
                registered_wire = self.canvas.add_wire(
                    tx_hash=w.tx_hash,
                    from_address=w.from_address,
                    to_address=w.to_address,
                    value=w.value,
                    token_symbol=w.token_symbol,
                    token_type=w.token_type,
                    gas_fee=w.gas_fee,
                    timestamp=w.timestamp,
                    block_number=w.block_number
                )
                rec_node = self.canvas.get_or_create_node(w.to_address)
                tainted_val, rec_ratio, is_pruned = self.taint_engine.propagate_taint(curr_node, rec_node, registered_wire)

                if on_step:
                    on_step("node", self.canvas.node_to_cytoscape(rec_node))
                    on_step("wire", self.canvas.wire_to_cytoscape(registered_wire))

                # Dynamic Pruning: If taint is negligible or dust, discard branch!
                if is_pruned:
                    continue

                # Compute priority and push to heap
                edge_score = self.compute_edge_priority(registered_wire, curr_node, rec_node, incident_time, initial_stolen)
                heapq.heappush(pq, (-edge_score, hop + 1, w.tx_hash, current_addr, w.to_address))

        return actionable_cex_found
