"""
Data Manager for OnlyVeda Nutraceutical Products
Handles loading, validating, adding, importing, and exporting product data.
"""

import json
import os
import csv
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")


class ProductDataManager:
    def __init__(self, data_file: str = DEFAULT_PRODUCTS_FILE):
        self.data_file = data_file
        self.products: List[Dict[str, Any]] = []
        self.load_products()

    def load_products(self) -> List[Dict[str, Any]]:
        """Load products from JSON file."""
        if not os.path.exists(self.data_file):
            self.products = []
            return self.products

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.products = json.load(f)
        except Exception as e:
            print(f"Error loading products from {self.data_file}: {e}")
            self.products = []
        return self.products

    def save_products(self) -> bool:
        """Persist products to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving products to {self.data_file}: {e}")
            return False

    def get_all_products(self) -> List[Dict[str, Any]]:
        return self.products

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        for prod in self.products:
            if prod.get("product_id") == product_id:
                return prod
        return None

    def get_categories(self) -> List[str]:
        cats = {p.get("category", "General") for p in self.products if p.get("category")}
        return sorted(list(cats))

    def validate_product(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate required fields in product data."""
        required_fields = ["name", "category", "key_ingredients", "benefits", "dosage_and_usage"]
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: '{field}'"
        return True, "Valid"

    def add_product(self, product_data: Dict[str, Any]) -> tuple[bool, str]:
        """Add a single product to catalog."""
        is_valid, msg = self.validate_product(product_data)
        if not is_valid:
            return False, msg

        # Generate product ID if not provided
        if not product_data.get("product_id"):
            count = len(self.products) + 1
            product_data["product_id"] = f"OV-NUT-{count:03d}"

        # Ensure lists are lists
        if isinstance(product_data.get("key_ingredients"), str):
            product_data["key_ingredients"] = [i.strip() for i in product_data["key_ingredients"].split(",")]
        if isinstance(product_data.get("health_concerns"), str):
            product_data["health_concerns"] = [i.strip() for i in product_data["health_concerns"].split(",")]
        if isinstance(product_data.get("tags"), str):
            product_data["tags"] = [i.strip() for i in product_data["tags"].split(",")]

        # Check duplicate ID
        for idx, prod in enumerate(self.products):
            if prod.get("product_id") == product_data["product_id"]:
                self.products[idx] = product_data
                self.save_products()
                return True, f"Updated existing product {product_data['product_id']}"

        self.products.append(product_data)
        self.save_products()
        return True, f"Product {product_data['product_id']} added successfully"

    def import_from_csv(self, csv_filepath: str) -> tuple[int, List[str]]:
        """Import products from CSV file."""
        added = 0
        errors = []
        if not os.path.exists(csv_filepath):
            return 0, [f"File {csv_filepath} does not exist"]

        with open(csv_filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                try:
                    product_data = {
                        "product_id": row.get("product_id") or f"OV-NUT-{len(self.products) + 1:03d}",
                        "name": row.get("name", "").strip(),
                        "category": row.get("category", "General Wellness").strip(),
                        "key_ingredients": [i.strip() for i in row.get("key_ingredients", "").split(";") if i.strip()],
                        "benefits": row.get("benefits", "").strip(),
                        "health_concerns": [i.strip() for i in row.get("health_concerns", "").split(";") if i.strip()],
                        "dosage_and_usage": row.get("dosage_and_usage", "").strip(),
                        "contraindications": row.get("contraindications", "").strip(),
                        "price_inr": float(row.get("price_inr", 0)) if row.get("price_inr") else 0,
                        "size": row.get("size", "").strip(),
                        "in_stock": True if str(row.get("in_stock", "true")).lower() in ["true", "1", "yes"] else False,
                        "image_url": row.get("image_url", "").strip(),
                        "tags": [i.strip() for i in row.get("tags", "").split(";") if i.strip()]
                    }
                    ok, msg = self.add_product(product_data)
                    if ok:
                        added += 1
                    else:
                        errors.append(f"Row {idx+1}: {msg}")
                except Exception as e:
                    errors.append(f"Row {idx+1}: {str(e)}")

        return added, errors

    def export_to_csv(self, output_path: str) -> bool:
        """Export current products to a CSV file."""
        if not self.products:
            return False

        fieldnames = [
            "product_id", "name", "category", "key_ingredients", "benefits",
            "health_concerns", "dosage_and_usage", "contraindications",
            "price_inr", "size", "in_stock", "image_url", "tags"
        ]

        try:
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for prod in self.products:
                    row = dict(prod)
                    # Convert list fields to semicolon-separated strings for CSV
                    if isinstance(row.get("key_ingredients"), list):
                        row["key_ingredients"] = "; ".join(row["key_ingredients"])
                    if isinstance(row.get("health_concerns"), list):
                        row["health_concerns"] = "; ".join(row["health_concerns"])
                    if isinstance(row.get("tags"), list):
                        row["tags"] = "; ".join(row["tags"])
                    writer.writerow(row)
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
