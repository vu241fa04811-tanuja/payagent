import sqlite3
import json
from typing import List, Optional, Dict, Any
from backend.models import Product, RazorpayOrder, RazorpayPaymentLink, DecisionLogEntry
from backend.catalog import SEED_PRODUCTS

DB_PATH = "payagent.db"

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self._seed_catalog()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                description TEXT NOT NULL,
                rating REAL NOT NULL,
                image_url TEXT
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT NOT NULL,
                receipt TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_links (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                short_url TEXT NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                session_id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                final_status TEXT NOT NULL,
                purchased_item_id TEXT,
                order_id TEXT,
                payment_id TEXT,
                amount_spent REAL,
                decision_trail_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()

    def _seed_catalog(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for prod in SEED_PRODUCTS:
                cursor.execute("""
                INSERT OR IGNORE INTO products (id, name, category, price, stock, description, rating, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (prod.id, prod.name, prod.category, prod.price, prod.stock, prod.description, prod.rating, prod.image_url))
            conn.commit()

    # Catalog operations

    def get_products(self) -> List[Product]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
            rows = cursor.fetchall()
            return [Product(**dict(r)) for r in rows]

    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            if row:
                return Product(**dict(row))
            return None

    def search_products(self, query: str, max_price: Optional[float] = None) -> List[Product]:
        products = self.get_products()
        query_lower = query.lower()
        results = []
        for p in products:
            matches_query = (
                query_lower in p.name.lower() or 
                query_lower in p.description.lower() or 
                query_lower in p.category.lower()
            )
            if matches_query:
                if max_price is None or p.price <= max_price:
                    results.append(p)
        return results

    def update_stock(self, product_id: str, new_stock: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
            conn.commit()
            return cursor.rowcount > 0

    def decrement_stock(self, product_id: str, quantity: int = 1) -> bool:
        product = self.get_product_by_id(product_id)
        if product and product.stock >= quantity:
            return self.update_stock(product_id, product.stock - quantity)
        return False

    # Order operations
    def save_order(self, order: RazorpayOrder):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO orders (id, product_id, amount, currency, receipt, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order.id, order.product_id, order.amount, order.currency, order.receipt, order.status, order.created_at))
            conn.commit()

    def get_order(self, order_id: str) -> Optional[RazorpayOrder]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            if row:
                return RazorpayOrder(**dict(row))
            return None

    def get_all_orders(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT o.*, p.name as product_name, p.price as product_price
            FROM orders o
            JOIN products p ON o.product_id = p.id
            ORDER BY o.created_at DESC
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # Payment link operations
    def save_payment_link(self, link: RazorpayPaymentLink):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO payment_links (id, order_id, short_url, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (link.id, link.order_id, link.short_url, link.amount, link.status, link.created_at))
            conn.commit()

    # Agent Run log operations
    def save_agent_run(self, session_id: str, prompt: str, final_status: str, purchased_item_id: Optional[str],
                       order_id: Optional[str], payment_id: Optional[str], amount_spent: float, decision_trail: List[DecisionLogEntry]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            trail_json = json.dumps([d.dict() for d in decision_trail])
            cursor.execute("""
            INSERT OR REPLACE INTO agent_runs 
            (session_id, prompt, final_status, purchased_item_id, order_id, payment_id, amount_spent, decision_trail_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, prompt, final_status, purchased_item_id, order_id, payment_id, amount_spent, trail_json))
            conn.commit()

    def get_agent_runs(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_runs ORDER BY created_at DESC")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item['decision_trail'] = json.loads(item['decision_trail_json'])
                del item['decision_trail_json']
                results.append(item)
            return results

db = Database()
