import os
import json
from typing import Dict, Any, Optional


class GroundTruthStore:
    """
    Deterministic Ground-Truth Reference Data Store.
    Loads approved synthetic banking product rates, FAQs, and effective dates.
    """

    DEFAULT_DATA_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "approved_ground_truth.json")
    )

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or self.DEFAULT_DATA_PATH
        self.data: Dict[str, Any] = {}
        self.load_data()

    def load_data(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Ground-truth reference data file not found at '{self.data_path}'")

        with open(self.data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    @property
    def version(self) -> str:
        return self.data.get("dataset_metadata", {}).get("version", "unknown")

    @property
    def status(self) -> str:
        return self.data.get("dataset_metadata", {}).get("status", "INACTIVE")

    def get_product(self, product_key: str) -> Optional[Dict[str, Any]]:
        return self.data.get("products", {}).get(product_key)

    def get_product_rate(self, product_key: str) -> Optional[str]:
        product = self.get_product(product_key)
        if product:
            return product.get("supported_fields", {}).get("interest_rate")
        return None

    def get_product_numeric_rate(self, product_key: str) -> Optional[float]:
        product = self.get_product(product_key)
        if product:
            return product.get("supported_fields", {}).get("rate_numeric")
        return None

    def get_faq(self, faq_key: str) -> Optional[str]:
        return self.data.get("approved_faqs", {}).get(faq_key)
