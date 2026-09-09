"""
Unit tests for the Entity Attribution Registry.
"""

import unittest
from src.attribution.entity_resolver import EntityResolver
from src.core.node_box import NodeRole


class TestEntityResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = EntityResolver()

    def test_resolve_binance_hot_wallet(self):
        # 0x28c6c06298d514db089934071355e5743bf21d60 is Binance 14
        entity = self.resolver.resolve("0x28c6c06298d514db089934071355e5743bf21d60")
        self.assertIsNotNone(entity)
        self.assertIn("Binance", entity.name)
        self.assertEqual(entity.node_role, NodeRole.CEX_DEPOSIT)
        self.assertTrue(entity.is_actionable_freeze_target)

    def test_resolve_coindcx_indian_fiu(self):
        entity = self.resolver.resolve("0x4a4754593444053896fa231b1e93c1ef7e068777")
        self.assertIsNotNone(entity)
        self.assertIn("CoinDCX", entity.name)
        self.assertTrue(entity.fiu_registered)
        self.assertEqual(entity.compliance_email, "legal@coindcx.com")

    def test_resolve_uniswap_v2_router(self):
        entity = self.resolver.resolve("0x7a250d5630b4cf539739df2c5dacb4c659f2488d")
        self.assertIsNotNone(entity)
        self.assertIn("Uniswap", entity.name)
        self.assertEqual(entity.node_role, NodeRole.DEX_ROUTER)
        self.assertFalse(entity.is_actionable_freeze_target)

    def test_resolve_tornado_cash_pool(self):
        entity = self.resolver.resolve("0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc")
        self.assertIsNotNone(entity)
        self.assertIn("Tornado.Cash", entity.name)
        self.assertEqual(entity.node_role, NodeRole.MIXER_POOL)

    def test_register_custom_user_deposit(self):
        custom_deposit = "0x9999000011112222333344445555666677778888"
        entity = self.resolver.register_custom_deposit(
            deposit_address=custom_deposit,
            exchange_name="WazirX",
            compliance_email="nodal@wazirx.com"
        )
        resolved = self.resolver.resolve(custom_deposit)
        self.assertEqual(resolved.name, "WazirX: User Deposit Proxy")
        self.assertTrue(resolved.is_actionable_freeze_target)


if __name__ == "__main__":
    unittest.main()
