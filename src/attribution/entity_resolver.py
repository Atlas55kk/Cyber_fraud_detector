"""
Module: entity_resolver.py
Resolves on-chain blockchain addresses against verified entity registries:
- Centralized Exchanges (CEX Hot/Deposit addresses)
- Decentralized Exchanges (Uniswap, 1inch routers)
- Privacy Mixers (Tornado Cash denomination pools)
- Cross-Chain Bridges (Across, Hop)

Implements Friedhelm Victor's (2020) Deposit Address Forwarding heuristic to
attribute individual deposit proxies to major exchanges.
"""

import os
import json
from typing import Optional, Dict, Any
from src.core.node_box import NodeRole


class EntityInfo:
    """
    Forensic metadata regarding a recognized on-chain entity.
    """
    __slots__ = (
        "name",
        "category",
        "node_role",
        "jurisdiction",
        "compliance_email",
        "fiu_registered",
        "is_actionable_freeze_target"
    )

    def __init__(
        self,
        name: str,
        category: str,
        node_role: NodeRole,
        jurisdiction: str = "Unknown",
        compliance_email: Optional[str] = None,
        fiu_registered: bool = False,
        is_actionable_freeze_target: bool = False
    ):
        self.name: str = name
        self.category: str = category
        self.node_role: NodeRole = node_role
        self.jurisdiction: str = jurisdiction
        self.compliance_email: Optional[str] = compliance_email
        self.fiu_registered: bool = fiu_registered
        self.is_actionable_freeze_target: bool = is_actionable_freeze_target

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "node_role": self.node_role.value,
            "jurisdiction": self.jurisdiction,
            "compliance_email": self.compliance_email,
            "fiu_registered": self.fiu_registered,
            "is_actionable_freeze_target": self.is_actionable_freeze_target
        }


class EntityResolver:
    """
    High-speed in-memory attribution registry.
    """

    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            # Default to data/known_entities/registry.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            registry_path = os.path.join(base_dir, "data", "known_entities", "registry.json")
        
        self.registry_path = registry_path
        self.address_map: Dict[str, EntityInfo] = {}
        self.exchange_hot_wallets: Dict[str, str] = {} # address -> exchange_name
        self.load_registry()

    def load_registry(self) -> None:
        if not os.path.exists(self.registry_path):
            return

        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Exchanges
        for ex in data.get("exchanges", []):
            name = ex["name"]
            jurisdiction = ex.get("jurisdiction", "Global")
            email = ex.get("compliance_email")
            fiu = ex.get("fiu_registered", False)
            for hw in ex.get("hot_wallets", []):
                clean_hw = hw.lower()
                info = EntityInfo(
                    name=f"{name}: Hot Wallet",
                    category="CEX_HOT_WALLET",
                    node_role=NodeRole.CEX_DEPOSIT,
                    jurisdiction=jurisdiction,
                    compliance_email=email,
                    fiu_registered=fiu,
                    is_actionable_freeze_target=True
                )
                self.address_map[clean_hw] = info
                self.exchange_hot_wallets[clean_hw] = name

        # 2. DEX Routers
        for dex in data.get("dex_routers", []):
            clean_addr = dex["address"].lower()
            self.address_map[clean_addr] = EntityInfo(
                name=dex["name"],
                category="DEX_ROUTER",
                node_role=NodeRole.DEX_ROUTER,
                is_actionable_freeze_target=False
            )

        # 3. Mixers
        for mix in data.get("mixers", []):
            clean_addr = mix["address"].lower()
            self.address_map[clean_addr] = EntityInfo(
                name=mix["name"],
                category="PRIVACY_MIXER",
                node_role=NodeRole.MIXER_POOL,
                is_actionable_freeze_target=False
            )

        # 4. Bridges
        for br in data.get("bridges", []):
            clean_addr = br["address"].lower()
            self.address_map[clean_addr] = EntityInfo(
                name=br["name"],
                category="CROSS_CHAIN_BRIDGE",
                node_role=NodeRole.BRIDGE_CONTRACT,
                is_actionable_freeze_target=False
            )

    def resolve(self, address: str) -> Optional[EntityInfo]:
        """
        Looks up an address in the verified registry.
        """
        return self.address_map.get(address.lower())

    def register_custom_deposit(
        self,
        deposit_address: str,
        exchange_name: str,
        compliance_email: Optional[str] = None
    ) -> EntityInfo:
        """
        Allows investigators or forward-heuristic clustering to tag an address
        as a verified user deposit address for a specific exchange.
        """
        clean = deposit_address.lower()
        info = EntityInfo(
            name=f"{exchange_name}: User Deposit Proxy",
            category="CEX_USER_DEPOSIT",
            node_role=NodeRole.CEX_DEPOSIT,
            compliance_email=compliance_email,
            is_actionable_freeze_target=True
        )
        self.address_map[clean] = info
        return info
