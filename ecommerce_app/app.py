#!/usr/bin/env python3
"""
Minimal e-commerce demo site backed by the synthetic reviews CSV.

Run:
    pip install -r requirements.txt
    python3 app.py
Then open http://localhost:5000

API:
    GET /reviews
        query params (all optional):
          product     - product_id (e.g. P0001)
          name        - exact product name
          brand       - brand name
          category    - category name
          sentiment   - positive | neutral | negative
          rating      - 1-5
          min_rating  - 1-5
          page        - default 1
          per_page    - default 20, max 100
        returns: {"page", "per_page", "total", "total_pages", "reviews": [...]}

    GET /reviews/<review_id>
        returns a single review, or 404

    GET /products
        returns the product catalog with aggregate rating stats

    GET /products/<product_id>
        returns one product's info + aggregate rating stats

    GET /products/<product_id>/reviews
        shortcut for /reviews?product=<product_id>
"""
import math
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request, abort

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "reviews.csv"

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Load data once at startup. For a dataset in the hundreds-of-thousands-of-rows
# range this comfortably fits in memory; swap for a real DB for larger data.
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA_PATH)
df["reviews.didPurchase"] = df["reviews.didPurchase"].astype(bool)
df["reviews.doRecommend"] = df["reviews.doRecommend"].astype(bool)

# Stable product_id derived from name+brand (mirrors generate_data.py's catalog)
_product_ids = {name: f"P{idx+1:04d}" for idx, name in enumerate(sorted(df["name"].unique()))}
df["product_id"] = df["name"].map(_product_ids)


def _review_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "product_id": row["product_id"],
        "product_name": row["name"],
        "brand": row["brand"],
        "category": row["categories"].split(";")[0].strip(),
        "date": row["reviews.date"],
        "did_purchase": bool(row["reviews.didPurchase"]),
        "do_recommend": bool(row["reviews.doRecommend"]),
        "num_helpful": int(row["reviews.numHelpful"]),
        "rating": int(row["reviews.rating"]),
        "title": row["reviews.title"],
        "text": row["reviews.text"],
        "username": row["reviews.username"],
        "sentiment": row["sentiment"],
    }


CATEGORY_COLORS = {
    "Smart Home": "#2F6FED", "Chargers & Power": "#E8A700", "E-Readers": "#1E3A70",
    "Headphones": "#142A54", "Streaming Devices": "#2F6FED", "Smart Speakers": "#E8A700",
    "Monitors": "#1E3A70", "Tablets": "#142A54", "Keyboards": "#2F6FED", "Mice": "#E8A700",
}


def _initials(name: str) -> str:
    words = [w for w in name.split() if w[0].isalnum()]
    return "".join(w[0] for w in words[:2]).upper()


def _product_summary(product_id: str, pdf: pd.DataFrame) -> dict:
    first = pdf.iloc[0]
    category = first["categories"].split(";")[0].strip()
    name = first["name"]
    return {
        "product_id": product_id,
        "name": name,
        "brand": first["brand"],
        "manufacturer": first["manufacturer"],
        "category": category,
        "primary_category": first["primaryCategories"],
        "price": round(float(pdf["productPrice"].mean()), 2),
        "review_count": int(len(pdf)),
        "avg_rating": round(float(pdf["reviews.rating"].mean()), 2),
        "tile_color": CATEGORY_COLORS.get(category, "#2F6FED"),
        "initials": _initials(name),
    }


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------
@app.route("/reviews")
def list_reviews():
    q = df

    product_id = request.args.get("product")
    if product_id:
        q = q[q["product_id"] == product_id]

    name = request.args.get("name")
    if name:
        q = q[q["name"].str.lower() == name.lower()]

    brand = request.args.get("brand")
    if brand:
        q = q[q["brand"].str.lower() == brand.lower()]

    category = request.args.get("category")
    if category:
        q = q[q["categories"].str.contains(category, case=False, na=False)]

    sentiment = request.args.get("sentiment")
    if sentiment:
        q = q[q["sentiment"].str.lower() == sentiment.lower()]

    rating = request.args.get("rating", type=int)
    if rating:
        q = q[q["reviews.rating"] == rating]

    min_rating = request.args.get("min_rating", type=int)
    if min_rating:
        q = q[q["reviews.rating"] >= min_rating]

    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)
    except ValueError:
        per_page = 20

    total = len(q)
    total_pages = max(math.ceil(total / per_page), 1)
    start = (page - 1) * per_page
    page_rows = q.iloc[start:start + per_page]

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "reviews": [_review_to_dict(row) for _, row in page_rows.iterrows()],
    })


@app.route("/reviews/<review_id>")
def get_review(review_id):
    match = df[df["id"] == review_id]
    if match.empty:
        abort(404, description="Review not found")
    return jsonify(_review_to_dict(match.iloc[0]))


@app.route("/products")
def list_products():
    out = []
    for product_id, pdf in df.groupby("product_id"):
        out.append(_product_summary(product_id, pdf))
    out.sort(key=lambda p: p["product_id"])
    return jsonify(out)


@app.route("/products/<product_id>")
def get_product(product_id):
    pdf = df[df["product_id"] == product_id]
    if pdf.empty:
        abort(404, description="Product not found")
    return jsonify(_product_summary(product_id, pdf))


@app.route("/products/<product_id>/reviews")
def product_reviews(product_id):
    # convenience alias -> reuse the main /reviews logic
    with app.test_request_context(f"/reviews?product={product_id}&{request.query_string.decode()}"):
        return list_reviews()


# ---------------------------------------------------------------------------
# Simple storefront pages (server-rendered, fetch reviews via the API above)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    products = [_product_summary(pid, pdf) for pid, pdf in df.groupby("product_id")]
    categories = sorted({p["category"] for p in products})

    q = request.args.get("q", "").strip().lower()
    if q:
        products = [p for p in products if q in p["name"].lower() or q in p["brand"].lower()
                    or q in p["category"].lower()]

    category = request.args.get("category", "").strip()
    if category:
        products = [p for p in products if p["category"] == category]

    sort = request.args.get("sort", "featured")
    if sort == "price_asc":
        products.sort(key=lambda p: p["price"])
    elif sort == "price_desc":
        products.sort(key=lambda p: -p["price"])
    elif sort == "rating":
        products.sort(key=lambda p: -p["avg_rating"])
    else:
        products.sort(key=lambda p: p["product_id"])

    total_reviews = int(df.shape[0])
    avg_rating_all = round(float(df["reviews.rating"].mean()), 2)

    return render_template(
        "index.html", products=products, categories=categories,
        active_category=category, sort=sort,
        total_reviews=total_reviews, avg_rating_all=avg_rating_all,
    )


@app.route("/product/<product_id>")
def product_page(product_id):
    pdf = df[df["product_id"] == product_id]
    if pdf.empty:
        abort(404)
    product = _product_summary(product_id, pdf)
    rating_counts = pdf["reviews.rating"].value_counts().to_dict()
    rating_breakdown = [{"stars": s, "count": int(rating_counts.get(s, 0))} for s in [5, 4, 3, 2, 1]]
    return render_template("product.html", product=product, rating_breakdown=rating_breakdown)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
