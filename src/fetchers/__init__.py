"""
Fetchers package initialization.
"""
from src.fetchers.mock_generator import MockFraudScenarioGenerator
from src.fetchers.etherscan_fetcher import EtherscanFetcher

__all__ = ["MockFraudScenarioGenerator", "EtherscanFetcher"]
