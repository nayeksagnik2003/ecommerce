# Circuitloop — synthetic e-commerce reviews demo

A small, self-contained e-commerce demo: a synthetic reviews dataset (structured like
`synthetic_ecommerce_reviews_300k.csv`), a Flask backend that serves it, and a simple
storefront UI on top.

## 1. Setup

```bash
cd ecommerce_app
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

## 2. (Optional) regenerate or resize the dataset

A 30,000-row dataset is already included at `data/reviews.csv`. To regenerate it, or
to scale it up to match the original file's ~300,000 rows:

```bash
python3 generate_data.py --rows 30000 --out data/reviews.csv     # default, fast
python3 generate_data.py --rows 300000 --out data/reviews.csv    # matches original scale
```

## 3. Run the site

```bash
python3 app.py
```

Then open **http://localhost:5000** in a browser for the storefront, or hit the API
directly:

```bash
curl http://localhost:5000/reviews
curl "http://localhost:5000/reviews?product=P0001&page=1&per_page=10"
curl "http://localhost:5000/reviews?category=Headphones&sentiment=negative"
curl http://localhost:5000/products
curl http://localhost:5000/products/P0001
```

## API reference

### `GET /reviews`
Query params (all optional, combinable):

| param        | example        | notes                          |
|--------------|----------------|---------------------------------|
| `product`    | `P0001`        | filter by product id             |
| `name`       | `Sonave Air Buds 2` | filter by exact product name |
| `brand`      | `Sonave`       | filter by brand                  |
| `category`   | `Headphones`   | substring match on category      |
| `sentiment`  | `positive`     | `positive` \| `neutral` \| `negative` |
| `rating`     | `5`            | exact star rating (1-5)          |
| `min_rating` | `4`            | star rating >= value             |
| `page`       | `2`            | default `1`                      |
| `per_page`   | `50`           | default `20`, max `100`          |

Response:
```json
{
  "page": 1,
  "per_page": 20,
  "total": 3012,
  "total_pages": 151,
  "reviews": [ { "id": "...", "product_id": "P0001", "rating": 5, "text": "...", ... } ]
}
```

### `GET /reviews/<review_id>`
Single review by id.

### `GET /products`
All 20 products with aggregate price / rating stats.

### `GET /products/<product_id>`
One product's summary.

### `GET /products/<product_id>/reviews`
Shortcut for `/reviews?product=<product_id>` (same query params apply).

## Files

```
app.py              Flask app: API routes + storefront pages
generate_data.py     Synthetic dataset generator
data/reviews.csv      Generated dataset (30,000 rows by default)
templates/            Jinja templates for the storefront pages
static/css/style.css  Styling
requirements.txt
```
