# Tahoe Bear Jerky - E-Commerce Website

A humorous e-commerce website for Tahoe Bear Jerky merchandise, featuring a database-driven product catalog and REST API.

## Features

- **Database-Driven Product Catalog**: SQLite database with full e-commerce schema
- **REST API**: Flask-based API for products, orders, and customers
- **Responsive Design**: Beautiful, modern UI with smooth animations
- **Shopping Cart**: Full cart functionality with local storage
- **Product Management**: Easy-to-update product catalog via database
- **Order Management**: Complete order processing and tracking
- **Newsletter**: Email subscription system

## Project Structure

```
tahoebearjerky/
├── index.html              # Main website
├── styles.css              # Styling
├── script.js               # Frontend JavaScript (API integration)
├── api.py                  # Flask REST API server
├── requirements.txt        # Python dependencies
├── database/
│   ├── schema.sql          # Database schema
│   ├── init_db.py          # Database initialization script
│   └── tahoe_bear_jerky.db # SQLite database (created after init)
└── README.md               # This file
```

## Setup Instructions

### 1. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Initialize the Database

```powershell
python database/init_db.py
```

This will create the database and seed it with initial product data.

To reset the database (delete and recreate):
```powershell
python database/init_db.py --reset
```

### 3. Start the API Server

```powershell
python api.py
```

The API will run on `http://localhost:5000`

### 4. Start the Frontend Server

In a separate terminal:

```powershell
python -m http.server 8000
```

The website will be available at `http://localhost:8000`

## API Endpoints

### Products
- `GET /api/products` - Get all active products
- `GET /api/products?category=<slug>` - Get products by category
- `GET /api/products/<id>` - Get a single product

### Categories
- `GET /api/categories` - Get all categories

### Orders
- `POST /api/orders` - Create a new order
- `GET /api/orders/<order_number>` - Get order details

### Newsletter
- `POST /api/newsletter/subscribe` - Subscribe to newsletter

### Health
- `GET /api/health` - Health check

## Database Schema

The database includes the following tables:

- **categories**: Product categories (T-Shirts, Sweaters, Hats, Stickers)
- **products**: Product catalog with prices, descriptions, images
- **customers**: Customer information
- **addresses**: Shipping and billing addresses
- **orders**: Order records
- **order_items**: Individual items in each order
- **newsletter_subscribers**: Email subscribers
- **product_images**: Multiple images per product
- **inventory_transactions**: Inventory tracking

## Managing Products

### Adding a New Product

1. Connect to the database:
```python
import sqlite3
conn = sqlite3.connect('database/tahoe_bear_jerky.db')
cursor = conn.cursor()
```

2. Insert a new product:
```python
cursor.execute('''
    INSERT INTO products 
    (name, slug, category_id, description, price, image_url, emoji, stock_quantity, is_active, featured)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'New Product Name',
    'new-product-slug',
    1,  # category_id (1=T-Shirts, 2=Sweaters, 3=Hats, 4=Stickers)
    'Product description',
    29.99,
    None,  # image_url (or path to image)
    '👕',  # emoji fallback
    50,    # stock_quantity
    1,     # is_active
    0      # featured
))
conn.commit()
conn.close()
```

### Updating Product Images

Products can use either:
- **Emoji**: Set the `emoji` field (e.g., '👕', '🧥')
- **Image URL**: Set the `image_url` field to a local or remote image path

### Updating Stock

Stock is automatically updated when orders are placed. To manually adjust:

```python
cursor.execute('UPDATE products SET stock_quantity = ? WHERE id = ?', (new_quantity, product_id))
```

## Development

### Frontend (script.js)
- Fetches products from API on page load
- Filters products by category
- Manages shopping cart state
- Handles checkout flow

### Backend (api.py)
- Flask REST API
- SQLite database integration
- CORS enabled for local development
- Full CRUD operations for products and orders

## Production Deployment

For production deployment:

1. **Database**: Consider migrating to PostgreSQL or MySQL
2. **API**: Deploy Flask app with Gunicorn/uWSGI
3. **Frontend**: Serve static files via Nginx or CDN
4. **Environment Variables**: Move API_BASE_URL to environment config
5. **HTTPS**: Enable SSL/TLS
6. **Payment Integration**: Add Stripe/PayPal for real payments

## Contributing

This is a parody website for educational purposes. No actual bears were harmed in the making of this site!

## License

© 2025 Tahoe Bear Jerky. All rights reserved.
