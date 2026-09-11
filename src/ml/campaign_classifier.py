"""
Module: campaign_classifier.py
Tier 2: High-Level Macro-Model for Campaign & Subgraph Topology Classification.

Evaluates graph-wide structural features:
- Subgraph topology (peel chain depth, smurfing branches, fan-in/fan-out)
- Temporal dispersion across multi-hop paths
- Cross-chain bridge and privacy mixer entanglement
- Terminal convergence towards FIU-IND registered CEX off-ramps
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import NodeRole


@dataclass
class MacroCampaignAssessment:
    campaign_name: str
    overall_risk_score: int # 0 to 100
    investigation_priority: str # CRITICAL, HIGH, MEDIUM, LOW
    topological_fingerprint: str # SMURFING_TREE, PEEL_CHAIN_CONVERGENCE, MIXER_CYCLE, DIRECT_OFFRAMP
    cex_offramps_detected: List[str]
    is_cross_chain_involved: bool
    summary: str


class CampaignMacroClassifier:
    """
    Tier 2 Macro-Level graph topology intelligence model.
    Synthesizes the entire forensic canvas into an actionable threat profile.
    """

    def __init__(self):
        pass

    def evaluate_canvas(self, canvas: WhiteboardCanvas) -> MacroCampaignAssessment:
        """
        Extracts subgraph topological indicators and calculates campaign-level risk.
        """
        nodes = list(canvas.nodes.values())
        wires = list(canvas.wires.values())

        total_nodes = len(nodes)
        total_wires = len(wires)

        # Count specific node roles
        mule_nodes = [n for n in nodes if n.role in (NodeRole.MULE_TRANSIT, NodeRole.PEEL_CHANGE)]
        cex_nodes = [n for n in nodes if n.role == NodeRole.CEX_DEPOSIT]
        mixer_nodes = [n for n in nodes if n.role == NodeRole.MIXER_POOL]
        bridge_nodes = [n for n in nodes if n.role == NodeRole.BRIDGE_CONTRACT]

        # Trace maximum hop depth
        max_depth = 1
        for node in nodes:
            paths = canvas.trace_paths_to_address(node.address)
            for path in paths:
                if len(path) > max_depth:
                    max_depth = len(path)

        # Identify target CEX entities
        cex_names = []
        for c in cex_nodes:
            name = c.entity_tag or c.address[:10]
            if name not in cex_names:
                cex_names.append(name)

        # Topological Fingerprint & Campaign Determination
        has_mixer = len(mixer_nodes) > 0
        has_bridge = len(bridge_nodes) > 0
        is_smurfing = len(mule_nodes) >= 3
        is_peel = max_depth >= 3 and total_wires >= 3

        # Base scoring calculation
        risk_score = 40 # Base baseline for flagged crime incident
        risk_score += min(len(mule_nodes) * 8, 25)
        risk_score += min(max_depth * 6, 20)

        if has_mixer:
            risk_score += 25
            fingerprint = "MIXER_OBFUSCATION_CYCLE"
            campaign_type = "DEFI_EXPLOIT_TORNADO_LOOP"
            summary = (
                f"Advanced laundering campaign detected involving {len(mixer_nodes)} privacy mixer pools "
                f"across a {max_depth}-hop topology designed to sever on-chain provenance."
            )
        elif has_bridge:
            risk_score += 20
            fingerprint = "CROSS_CHAIN_HOPPING"
            campaign_type = "CROSS_CHAIN_BRIDGE_EVASION"
            summary = (
                f"Multi-chain flight detected across bridge infrastructure with {len(cex_nodes)} identified "
                f"terminal cash-out off-ramps."
            )
        elif is_smurfing:
            risk_score += 20
            fingerprint = "SMURFING_TREE_DISPERSION"
            campaign_type = "ORGANIZED_PIG_BUTCHERING_SYNDICATE"
            summary = (
                f"Syndicate smurfing tree detected: stolen funds dispersed across {len(mule_nodes)} intermediary "
                f"mule wallets to evade FIU cash-out thresholds before hitting CEX deposits ({', '.join(cex_names) or 'CEX'})."
            )
        elif is_peel:
            risk_score += 15
            fingerprint = "PEEL_CHAIN_CONVERGENCE"
            campaign_type = "RAPID_PEEL_CHAIN_CONSOLIDATION"
            summary = (
                f"Sequential peel chain identified traversing {max_depth} hops and terminating at exchange deposit "
                f"points ({', '.join(cex_names) or 'Exchange Hot Wallets'})."
            )
        else:
            fingerprint = "DIRECT_OFFRAMP"
            campaign_type = "OPPORTUNISTIC_DIRECT_THEFT"
            summary = f"Direct transfer trail across {max_depth} hops terminating at known destinations."

        risk_score = min(max(risk_score, 10), 100)

        # Assign priority tier
        if risk_score >= 80:
            priority = "CRITICAL"
        elif risk_score >= 60:
            priority = "HIGH"
        elif risk_score >= 40:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return MacroCampaignAssessment(
            campaign_name=campaign_type,
            overall_risk_score=risk_score,
            investigation_priority=priority,
            topological_fingerprint=fingerprint,
            cex_offramps_detected=cex_names,
            is_cross_chain_involved=has_bridge,
            summary=summary
        )
