from typing import List, Optional
from backend.models import Product

# Seed products for merchant catalog
SEED_PRODUCTS = [
    Product(
        id="prod_mouse_01",
        name="Ergonomic Wireless Mouse",
        category="Electronics",
        price=899.0,
        stock=15,
        description="2.4GHz ultra-silent wireless optical mouse with adjustable DPI (800/1200/1600) and rechargeable battery.",
        rating=4.7,
        image_url="https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=400"
    ),
    Product(
        id="prod_keyboard_02",
        name="RGB Mechanical Gaming Keyboard",
        category="Electronics",
        price=2499.0,
        stock=8,
        description="Tactile blue switch mechanical keyboard with per-key RGB backlighting and detachable USB-C cable.",
        rating=4.8,
        image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400"
    ),
    Product(
        id="prod_hub_03",
        name="7-in-1 USB-C Multiport Hub",
        category="Accessories",
        price=1299.0,
        stock=20,
        description="Aluminum USB-C dock with 4K HDMI, 100W Power Delivery, 3x USB 3.0 ports, and SD/TF card readers.",
        rating=4.5,
        image_url="https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400"
    ),
    Product(
        id="prod_headphones_04",
        name="Active Noise Cancelling Headphones",
        category="Audio",
        price=3499.0,
        stock=0,  # OUT OF STOCK item to trigger realistic agent recovery!
        description="Over-ear Bluetooth 5.2 headphones with hybrid active noise cancellation and 40-hour playtime.",
        rating=4.9,
        image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400"
    ),
    Product(
        id="prod_speaker_05",
        name="Portable Waterproof Bluetooth Speaker",
        category="Audio",
        price=999.0,
        stock=12,
        description="IPX7 waterproof wireless speaker with deep bass, 12-hour battery life, and compact travel lanyard.",
        rating=4.6,
        image_url="https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400"
    )
]
