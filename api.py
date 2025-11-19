from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add database directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database'))
from db_config import get_db_connection, dict_from_row, DB_TYPE

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# ============= PRODUCT ENDPOINTS =============

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all active products with optional category filter"""
    category = request.args.get('category')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Use appropriate placeholder for database type
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    if category and category != 'all':
        cursor.execute(f'''
            SELECT p.*, c.name as category_name, c.slug as category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE AND c.slug = {placeholder}
            ORDER BY p.featured DESC, p.name ASC
        ''', (category,))
    else:
        cursor.execute('''
            SELECT p.*, c.name as category_name, c.slug as category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE
            ORDER BY p.featured DESC, p.name ASC
        ''')
    
    products = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    cursor.execute(f'''
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = {placeholder} AND p.is_active = TRUE
    ''', (product_id,))
    
    product = cursor.fetchone()
    conn.close()
    
    if product:
        return jsonify(dict_from_row(product))
    else:
        return jsonify({'error': 'Product not found'}), 404

# ============= CATEGORY ENDPOINTS =============

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM categories
        ORDER BY display_order ASC
    ''')
    
    categories = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(categories)

# ============= JERKY PRODUCTS ENDPOINTS =============

@app.route('/api/jerky-products', methods=['GET'])
def get_jerky_products():
    """Get all active jerky products"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM jerky_products
        WHERE is_active = TRUE
        ORDER BY display_order ASC
    ''')
    
    jerky_products = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(jerky_products)

@app.route('/api/jerky-products/<int:jerky_id>', methods=['GET'])
def get_jerky_product(jerky_id):
    """Get a single jerky product by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    cursor.execute(f'''
        SELECT * FROM jerky_products
        WHERE id = {placeholder} AND is_active = TRUE
    ''', (jerky_id,))
    
    jerky_product = cursor.fetchone()
    conn.close()
    
    if jerky_product:
        return jsonify(dict_from_row(jerky_product))
    else:
        return jsonify({'error': 'Jerky product not found'}), 404

# ============= ORDER ENDPOINTS =============

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    data = request.json
    
    # Validate required fields
    required_fields = ['customer_email', 'items', 'shipping_address']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    try:
        # Create or get customer
        if DB_TYPE == 'postgresql':
            cursor.execute(f'''
                INSERT INTO customers (email, first_name, last_name, phone)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            ''', (
                data['customer_email'],
                data.get('first_name', ''),
                data.get('last_name', ''),
                data.get('phone', '')
            ))
            customer_id = cursor.fetchone()['id']
        else:
            cursor.execute(f'''
                INSERT OR IGNORE INTO customers (email, first_name, last_name, phone)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                data['customer_email'],
                data.get('first_name', ''),
                data.get('last_name', ''),
                data.get('phone', '')
            ))
            cursor.execute(f'SELECT id FROM customers WHERE email = {placeholder}', (data['customer_email'],))
            customer_id = cursor.fetchone()['id']
        
        # Create shipping address
        shipping = data['shipping_address']
        if DB_TYPE == 'postgresql':
            cursor.execute(f'''
                INSERT INTO addresses 
                (customer_id, address_type, street_address, street_address_2, city, state, postal_code, country)
                VALUES ({placeholder}, 'shipping', {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                RETURNING id
            ''', (
                customer_id,
                shipping['street_address'],
                shipping.get('street_address_2', ''),
                shipping['city'],
                shipping['state'],
                shipping['postal_code'],
                shipping.get('country', 'USA')
            ))
            shipping_address_id = cursor.fetchone()['id']
        else:
            cursor.execute(f'''
                INSERT INTO addresses 
                (customer_id, address_type, street_address, street_address_2, city, state, postal_code, country)
                VALUES ({placeholder}, 'shipping', {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                customer_id,
                shipping['street_address'],
                shipping.get('street_address_2', ''),
                shipping['city'],
                shipping['state'],
                shipping['postal_code'],
                shipping.get('country', 'USA')
            ))
            shipping_address_id = cursor.lastrowid
        
        # Calculate totals
        subtotal = sum(item['price'] * item['quantity'] for item in data['items'])
        tax = subtotal * 0.0775  # 7.75% CA tax
        shipping_cost = 0.00 if subtotal > 50 else 5.99
        total = subtotal + tax + shipping_cost
        
        # Generate order number
        order_number = f"TBJ-{datetime.now().strftime('%Y%m%d')}-{customer_id:04d}"
        
        # Create order
        if DB_TYPE == 'postgresql':
            cursor.execute(f'''
                INSERT INTO orders 
                (order_number, customer_id, shipping_address_id, subtotal, tax, shipping_cost, total, status, payment_status)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 'pending', 'pending')
                RETURNING id
            ''', (order_number, customer_id, shipping_address_id, subtotal, tax, shipping_cost, total))
            order_id = cursor.fetchone()['id']
        else:
            cursor.execute(f'''
                INSERT INTO orders 
                (order_number, customer_id, shipping_address_id, subtotal, tax, shipping_cost, total, status, payment_status)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 'pending', 'pending')
            ''', (order_number, customer_id, shipping_address_id, subtotal, tax, shipping_cost, total))
            order_id = cursor.lastrowid
        
        # Create order items and update inventory
        for item in data['items']:
            cursor.execute(f'''
                INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, subtotal)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                order_id,
                item['id'],
                item['name'],
                item['quantity'],
                item['price'],
                item['price'] * item['quantity']
            ))
            
            cursor.execute(f'''
                UPDATE products SET stock_quantity = stock_quantity - {placeholder}
                WHERE id = {placeholder}
            ''', (item['quantity'], item['id']))
            
            cursor.execute(f'''
                INSERT INTO inventory_transactions (product_id, transaction_type, quantity_change, reference_id)
                VALUES ({placeholder}, 'sale', {placeholder}, {placeholder})
            ''', (item['id'], -item['quantity'], order_id))
        
        conn.commit()
        
        # Fetch the created order
        cursor.execute(f'''
            SELECT * FROM orders WHERE id = {placeholder}
        ''', (order_id,))
        order = dict_from_row(cursor.fetchone())
        
        conn.close()
        
        return jsonify({
            'success': True,
            'order': order,
            'message': 'Order created successfully'
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<order_number>', methods=['GET'])
def get_order(order_number):
    """Get order details by order number"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    cursor.execute(f'''
        SELECT o.*, c.email, c.first_name, c.last_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE o.order_number = {placeholder}
    ''', (order_number,))
    
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
    
    order_dict = dict_from_row(order)
    
    cursor.execute(f'''
        SELECT * FROM order_items WHERE order_id = {placeholder}
    ''', (order_dict['id'],))
    
    order_dict['items'] = [dict_from_row(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify(order_dict)

# ============= NEWSLETTER ENDPOINT =============

@app.route('/api/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    try:
        if DB_TYPE == 'postgresql':
            cursor.execute(f'''
                INSERT INTO newsletter_subscribers (email)
                VALUES ({placeholder})
                ON CONFLICT (email) DO NOTHING
            ''', (email,))
        else:
            cursor.execute(f'''
                INSERT OR IGNORE INTO newsletter_subscribers (email)
                VALUES ({placeholder})
            ''', (email,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Successfully subscribed to newsletter'
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# ============= HEALTH CHECK =============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': DB_TYPE,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print(f"🚀 Starting API server with {DB_TYPE.upper()} database...")
    app.run(debug=True, port=5000)
