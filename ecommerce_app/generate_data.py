#!/usr/bin/env python3
"""
Generate a synthetic e-commerce product-reviews dataset, structurally similar
to the reference file (synthetic_ecommerce_reviews_300k.csv):

    id, dateAdded, dateUpdated, name, brand, manufacturer, categories,
    primaryCategories, reviews.date, reviews.didPurchase, reviews.doRecommend,
    reviews.numHelpful, reviews.rating, reviews.title, reviews.text,
    reviews.username, sentiment, productPrice

Usage:
    python3 generate_data.py --rows 30000 --out data/reviews.csv
    python3 generate_data.py --rows 300000 --out data/reviews.csv   # match original scale
"""
import argparse
import csv
import random
from datetime import date, timedelta

random.seed(42)

# ---------------------------------------------------------------------------
# Product catalog: 10 brands x 2 products each, spread across 10 categories.
# (Brand/product names are invented for this synthetic set.)
# ---------------------------------------------------------------------------
CATALOG = [
    dict(brand="NimbusTech", manufacturer="NimbusTech Home", category="Smart Home",
         products=[("NimbusTech Hub X1", 79.99), ("NimbusTech Motion Sensor 3-Pack", 34.50)]),
    dict(brand="Corevolt", manufacturer="Corevolt Power", category="Chargers & Power",
         products=[("Corevolt 65W GaN Charger", 39.99), ("Corevolt PowerBank 20K", 49.99)]),
    dict(brand="Litherum", manufacturer="Litherum Reading", category="E-Readers",
         products=[("Litherum Page One", 99.99), ("Litherum Page One Glow", 129.99)]),
    dict(brand="Sonave", manufacturer="Sonave Audio", category="Headphones",
         products=[("Sonave Air Buds 2", 119.99), ("Sonave Quiet Max ANC", 189.99)]),
    dict(brand="Streamora", manufacturer="Streamora Media", category="Streaming Devices",
         products=[("Streamora Stick 4K", 34.99), ("Streamora Box Pro", 74.99)]),
    dict(brand="Echofield", manufacturer="Echofield Audio", category="Smart Speakers",
         products=[("Echofield Mini 2", 44.99), ("Echofield Home Max", 89.99)]),
    dict(brand="Visicore", manufacturer="Visicore Display", category="Monitors",
         products=[("Visicore View 24", 149.99), ("Visicore View 27Q", 229.99)]),
    dict(brand="Slabtronic", manufacturer="Slabtronic Imaging", category="Tablets",
         products=[("Slabtronic Tab 8", 139.99), ("Slabtronic Tab 10 Pro", 259.99)]),
    dict(brand="Keyforge", manufacturer="Keyforge Computing", category="Keyboards",
         products=[("Keyforge Glide M2", 39.99), ("Keyforge K78 Wireless", 59.99)]),
    dict(brand="Trackline", manufacturer="Trackline Computing", category="Mice",
         products=[("Trackline Glide Mouse", 24.99), ("Trackline Pro Wireless", 44.99)]),
]

PRIMARY_CATEGORY = {
    "Smart Home": "Electronics", "Chargers & Power": "Electronics", "E-Readers": "Electronics",
    "Headphones": "Electronics", "Streaming Devices": "Electronics", "Smart Speakers": "Electronics",
    "Monitors": "Computers", "Tablets": "Electronics", "Keyboards": "Computers", "Mice": "Computers",
}

# Category-specific noun used inside templated review text.
CATEGORY_NOUN = {
    "Smart Home": "smart home", "Chargers & Power": "charger", "E-Readers": "e-reader",
    "Headphones": "headphones", "Streaming Devices": "streaming", "Smart Speakers": "smart speaker",
    "Monitors": "monitor", "Tablets": "tablet", "Keyboards": "keyboard", "Mice": "mouse",
}

TITLES = {
    "positive": ["Highly recommended", "Great purchase", "Excellent value", "Works very well",
                 "Solid product", "Happy with it", "Very impressed", "Better than expected"],
    "negative": ["Frustrating to use", "Disappointed", "Would not recommend", "Poor experience",
                 "Too many issues", "Not worth the price", "Underwhelming"],
    "neutral": ["Does the job", "It is okay", "Acceptable product", "Fine for casual use",
                "Average experience", "Decent but basic", "Mixed results"],
}

OPENERS = {
    "positive": ["The device handles normal use without lag.", "The product arrived in good condition and works as described.",
                 "Setup was quick and the build quality feels solid."],
    "negative": ["The product arrived with a minor defect.", "Setup took longer than expected and support was slow to respond.",
                 "After a few weeks the performance started to drop off."],
    "neutral": ["The product arrived in good condition.", "Setup was straightforward, nothing stood out either way.",
                "It performs as expected for the price point."],
}

MIDDLES = {
    "positive": ["The {noun} features are practical, and the overall experience has been reliable.",
                 "For the price, the overall value is excellent."],
    "negative": ["The {noun} features feel limited compared to similar products.",
                 "For the price, I expected more reliability."],
    "neutral": ["The {noun} features are fine, nothing special either way.",
                "After some everyday use, the product feels functional but not exceptional."],
}

CLOSERS = {
    "positive": ["Overall, this has been a great purchase.", "It exceeded my expectations.",
                 "It does what I need without unnecessary fuss.", "The difference is noticeable in everyday use."],
    "negative": ["Overall, I would not buy this again.", "It fell short of what was advertised.",
                 "I would look at other options first.", "I ran into the same issue more than once."],
    "neutral": ["I would suggest comparing a few options first.", "It is a reasonable middle-of-the-road choice.",
                "I mainly use it during the week.", "I tested it on multiple days before writing this."],
}

FIRST_NAMES = ["ananya", "priya", "aarav", "meera", "rohan", "kabir", "isha", "dev", "sara", "vikram",
               "neha", "arjun", "diya", "karan", "tanya", "rahul", "pooja", "aditya", "riya", "sanjay"]
LAST_NAMES = ["iyer", "nair", "jain", "pillai", "sharma", "gupta", "verma", "das", "kapoor", "menon"]


def rating_to_sentiment(rating: int) -> str:
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "neutral"
    return "negative"


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


def make_review_text(category: str, sentiment: str) -> str:
    noun = CATEGORY_NOUN[category]
    parts = [
        random.choice(OPENERS[sentiment]),
        random.choice(MIDDLES[sentiment]).format(noun=noun),
        random.choice(CLOSERS[sentiment]),
    ]
    return " ".join(parts)


def build_products():
    products = []
    pid = 1
    for entry in CATALOG:
        for name, base_price in entry["products"]:
            products.append(dict(
                product_id=f"P{pid:04d}",
                name=name,
                brand=entry["brand"],
                manufacturer=entry["manufacturer"],
                category=entry["category"],
                categories=f"{entry['category']}; Electronics & Accessories",
                primaryCategories=PRIMARY_CATEGORY[entry["category"]],
                base_price=base_price,
            ))
            pid += 1
    return products


RATING_WEIGHTS = [0.10, 0.12, 0.15, 0.28, 0.35]  # ratings 1..5, skewed positive like the reference set


def generate(rows: int, out_path: str):
    products = build_products()
    date_added = {p["product_id"]: random_date(date(2022, 1, 1), date(2025, 6, 1)) for p in products}

    fieldnames = ["id", "dateAdded", "dateUpdated", "name", "brand", "manufacturer", "categories",
                  "primaryCategories", "reviews.date", "reviews.didPurchase", "reviews.doRecommend",
                  "reviews.numHelpful", "reviews.rating", "reviews.title", "reviews.text",
                  "reviews.username", "sentiment", "productPrice"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(1, rows + 1):
            product = random.choice(products)
            added = date_added[product["product_id"]]
            review_date = random_date(added, date(2026, 9, 25))
            rating = random.choices([1, 2, 3, 4, 5], weights=RATING_WEIGHTS, k=1)[0]
            sentiment = rating_to_sentiment(rating)
            did_purchase = random.random() < 0.85
            # doRecommend correlates with rating but isn't fully determined by it
            do_recommend = random.random() < {"positive": 0.90, "neutral": 0.45, "negative": 0.12}[sentiment]
            num_helpful = min(int(abs(random.gauss(2.8, 3.3))), 45)
            username = f"{random.choice(FIRST_NAMES)}{random.choice(LAST_NAMES)}{random.randint(100, 999)}"
            price = round(max(product["base_price"] * random.uniform(0.85, 1.15), 4.99), 2)

            writer.writerow({
                "id": f"syn2-{i:07d}",
                "dateAdded": added.isoformat(),
                "dateUpdated": added.isoformat(),
                "name": product["name"],
                "brand": product["brand"],
                "manufacturer": product["manufacturer"],
                "categories": product["categories"],
                "primaryCategories": product["primaryCategories"],
                "reviews.date": review_date.isoformat(),
                "reviews.didPurchase": str(did_purchase).lower(),
                "reviews.doRecommend": str(do_recommend).lower(),
                "reviews.numHelpful": num_helpful,
                "reviews.rating": rating,
                "reviews.title": random.choice(TITLES[sentiment]),
                "reviews.text": make_review_text(product["category"], sentiment),
                "reviews.username": username,
                "sentiment": sentiment,
                "productPrice": price,
            })

    print(f"Wrote {rows} rows to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=30000, help="number of review rows to generate")
    parser.add_argument("--out", type=str, default="data/reviews.csv", help="output CSV path")
    args = parser.parse_args()
    generate(args.rows, args.out)
