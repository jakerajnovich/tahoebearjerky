from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import urllib.request
import json

# Add database directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database'))
from db_config import get_db_connection, dict_from_row, DB_TYPE

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Square Configuration
SQUARE_ACCESS_TOKEN = os.getenv('SQUARE_ACCESS_TOKEN')
SQUARE_LOCATION_ID = os.getenv('SQUARE_LOCATION_ID')
SQUARE_ENVIRONMENT = os.getenv('SQUARE_ENVIRONMENT', 'sandbox')

# Helper function for Square API calls
def square_request(endpoint, method='POST', body=None):
    base_url = "https://connect.squareupsandbox.com/v2" if SQUARE_ENVIRONMENT == 'sandbox' else "https://connect.squareup.com/v2"
    url = f"{base_url}{endpoint}"
    
    headers = {
        "Square-Version": "2023-10-20",
        "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode()), None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            return None, json.loads(error_body)
        except:
            return None, {'errors': [{'detail': str(e)}]}
    except Exception as e:
        return None, {'errors': [{'detail': str(e)}]}

# ============= AUTH ENDPOINTS =============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    try:
        # Check if user exists
        cursor.execute(f'SELECT id FROM customers WHERE email = {placeholder}', (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 409
            
        password_hash = generate_password_hash(password)
        
        if DB_TYPE == 'postgresql':
            cursor.execute(f'''
                INSERT INTO customers (email, password_hash, first_name, last_name)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                RETURNING id
            ''', (email, password_hash, first_name, last_name))
            user_id = cursor.fetchone()['id']
        else:
            cursor.execute(f'''
                INSERT INTO customers (email, password_hash, first_name, last_name)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (email, password_hash, first_name, last_name))
            user_id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'Registration successful'
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    cursor.execute(f'SELECT * FROM customers WHERE email = {placeholder}', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user['password_hash'] and check_password_hash(user['password_hash'], password):
        user_dict = dict_from_row(user)
        del user_dict['password_hash'] # Don't send hash back
        
        return jsonify({
            'success': True,
            'user': user_dict,
            'message': 'Login successful'
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email"""
    from email_utils import generate_password_reset_token, send_password_reset_email
    
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    # Check if user exists
    cursor.execute(f'SELECT id FROM customers WHERE email = {placeholder}', (email,))
    user = cursor.fetchone()
    conn.close()
    
    # Always return success to prevent email enumeration
    if user:
        token = generate_password_reset_token(email)
        send_password_reset_email(email, token)
    
    return jsonify({
        'success': True,
        'message': 'If that email exists, a password reset link has been sent.'
    })

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    from email_utils import verify_password_reset_token
    
    data = request.json
    token = data.get('token')
    new_password = data.get('password')
    
    if not token or not new_password:
        return jsonify({'error': 'Token and password are required'}), 400
    
    # Verify token
    email = verify_password_reset_token(token)
    if not email:
        return jsonify({'error': 'Invalid or expired token'}), 400
    
    # Update password
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    try:
        password_hash = generate_password_hash(new_password)
        cursor.execute(f'''
            UPDATE customers 
            SET password_hash = {placeholder}, updated_at = CURRENT_TIMESTAMP
            WHERE email = {placeholder}
        ''', (password_hash, email))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Password reset successful'
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

# ============= ACCOUNT ENDPOINTS =============

@app.route('/api/account/<int:user_id>', methods=['GET'])
def get_account(user_id):
    """Get user account details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    cursor.execute(f'SELECT * FROM customers WHERE id = {placeholder}', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
        
    user_dict = dict_from_row(user)
    if 'password_hash' in user_dict:
        del user_dict['password_hash']
        
    # Get orders
    cursor.execute(f'''
        SELECT * FROM orders 
        WHERE customer_id = {placeholder} 
        ORDER BY created_at DESC
    ''', (user_id,))
    orders = [dict_from_row(row) for row in cursor.fetchall()]
    
    # Get payment methods
    cursor.execute(f'''
        SELECT * FROM payment_methods 
        WHERE customer_id = {placeholder}
    ''', (user_id,))
    payment_methods = [dict_from_row(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'user': user_dict,
        'orders': orders,
        'payment_methods': payment_methods
    })

@app.route('/api/account/<int:user_id>/payment-methods', methods=['POST'])
def add_payment_method(user_id):
    """Add a payment method"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    try:
        if DB_TYPE == 'postgresql':
            cursor.execute(f'''
                INSERT INTO payment_methods (customer_id, card_type, last_four, expiry_month, expiry_year)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                RETURNING id
            ''', (user_id, data['card_type'], data['last_four'], data['expiry_month'], data['expiry_year']))
            pm_id = cursor.fetchone()['id']
        else:
            cursor.execute(f'''
                INSERT INTO payment_methods (customer_id, card_type, last_four, expiry_month, expiry_year)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (user_id, data['card_type'], data['last_four'], data['expiry_month'], data['expiry_year']))
            pm_id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': pm_id}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

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
    """Create order using Square Orders API with automatic tax calculation"""
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
        
        # Build line items for Square - use catalog items if linked
        line_items = []
        for item in data['items']:
            # Get product details including Square catalog IDs
            cursor.execute(f"""
                SELECT square_item_id, square_variation_id 
                FROM products 
                WHERE id = {placeholder}
            """, (item['product_id'],))
            product = cursor.fetchone()
            
            # Use catalog item if linked, otherwise use ad-hoc item
            if product and (product['square_variation_id'] or product['square_item_id']):
                # Linked to Square catalog - use catalog_object_id
                line_items.append({
                    "catalog_object_id": product['square_variation_id'] or product['square_item_id'],
                    "quantity": str(item['quantity'])
                })
            else:
                # Not linked - use ad-hoc item
                line_items.append({
                    "name": item['name'],
                    "quantity": str(item['quantity']),
                    "base_price_money": {
                        "amount": int(float(item['price']) * 100),  # Convert to cents
                        "currency": "USD"
                    }
                })
        
        # Build shipping address for Square
        shipping = data['shipping_address']
        fulfillment = {
            "type": "SHIPMENT",
            "state": "PROPOSED",
            "shipment_details": {
                "recipient": {
                    "display_name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                    "email_address": data.get('customer_email'),
                    "address": {
                        "address_line_1": shipping['street_address'],
                        "address_line_2": shipping.get('street_address_2', ''),
                        "locality": shipping['city'],
                        "administrative_district_level_1": shipping['state'],
                        "postal_code": shipping['postal_code'],
                        "country": shipping.get('country', 'US')  # Must be 2-letter ISO code
                    }
                }
            }
        }
        
        # Create order in Square with automatic tax calculation
        square_order_body = {
            "order": {
                "location_id": SQUARE_LOCATION_ID,
                "line_items": line_items,
                "fulfillments": [fulfillment]
            },
            "idempotency_key": str(uuid.uuid4())
        }
        
        response, error = square_request('/orders', method='POST', body=square_order_body)
        
        if not response or 'order' not in response:
            raise Exception(f"Square order creation failed: {error}")
        
        square_order = response['order']
        
        # Extract totals from Square order (tax calculated automatically by Square)
        total_money = square_order.get('total_money', {})
        total = total_money.get('amount', 0) / 100  # Convert from cents
        
        tax_money = square_order.get('total_tax_money', {})
        tax = tax_money.get('amount', 0) / 100
        
        # Calculate subtotal
        subtotal = sum(float(item['price']) * int(item['quantity']) for item in data['items'])
        
        # Shipping cost logic
        shipping_cost = 0.00 if subtotal > 50 else 5.99
        
        # Create shipping address in our database
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
                shipping.get('country', 'US')
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
                shipping['postal_code'],                shipping.get('country', 'US')
            ))
            shipping_address_id = cursor.lastrowid
        
        # Generate order number - find next available number for today
        today = datetime.now().strftime('%Y%m%d')
        cursor.execute(f"""
            SELECT order_number FROM orders 
            WHERE order_number LIKE {placeholder}
            ORDER BY order_number DESC LIMIT 1
        """, (f'TBJ-{today}-%',))
        last_order = cursor.fetchone()
        
        if last_order:
            # Extract the sequence number and increment
            last_seq = int(last_order['order_number'].split('-')[-1])
            next_seq = last_seq + 1
        else:
            # First order of the day
            next_seq = 1
        
        order_number = f"TBJ-{today}-{next_seq:04d}"
        
        # Create order in our database with Square order ID
        if DB_TYPE == 'postgresql':
            cursor.execute(f'''
                INSERT INTO orders 
                (order_number, customer_id, shipping_address_id, subtotal, tax, shipping_cost, total, 
                 status, payment_status, square_order_id)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                        {placeholder}, {placeholder}, 'pending', 'pending', {placeholder})
                RETURNING id
            ''', (order_number, customer_id, shipping_address_id, subtotal, tax, 
                  shipping_cost, total, square_order['id']))
            order_id = cursor.fetchone()['id']
        else:
            cursor.execute(f'''
                INSERT INTO orders 
                (order_number, customer_id, shipping_address_id, subtotal, tax, shipping_cost, total, 
                 status, payment_status, square_order_id)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                        {placeholder}, {placeholder}, 'pending', 'pending', {placeholder})
            ''', (order_number, customer_id, shipping_address_id, subtotal, tax, 
                  shipping_cost, total, square_order['id']))
            order_id = cursor.lastrowid
        
        # Create order items
        for item in data['items']:
            cursor.execute(f'''
                INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, subtotal)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                order_id,
                item['id'],
                item['name'],
                item['quantity'],
                float(item['price']),
                float(item['price']) * int(item['quantity'])
            ))
            
            # Update inventory
            cursor.execute(f'''
                UPDATE products SET stock_quantity = stock_quantity - {placeholder}
                WHERE id = {placeholder}
            ''', (item['quantity'], item['id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'order': {
                'id': order_id,
                'order_number': order_number,
                'square_order_id': square_order['id'],
                'total': total,
                'tax': tax,
                'subtotal': subtotal,
                'shipping_cost': shipping_cost
            }
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error creating order: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
    
    cursor.execute(f'''
        SELECT * FROM orders WHERE id = {placeholder}
    ''', (order_id,))
    
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

# ============= SQUARE PAYMENT =============

@app.route('/api/payment/process', methods=['POST'])
def process_payment():
    """Process payment using Square with order linkage"""
    data = request.json
    source_id = data.get('source_id')  # Card nonce from Square Web SDK
    amount_money = data.get('amount')  # Amount in cents
    customer_id = data.get('customer_id')
    order_id = data.get('order_id')
    square_order_id = data.get('square_order_id')  # NEW: Link to Square order
    
    if not source_id or not amount_money:
        return jsonify({'error': 'Missing required payment information'}), 400
    
    try:
        # Create payment with Square
        idempotency_key = str(uuid.uuid4())
        
        body = {
            "source_id": source_id,
            "idempotency_key": idempotency_key,
            "amount_money": {
                "amount": amount_money,
                "currency": "USD"
            },
            "location_id": SQUARE_LOCATION_ID,
            "note": f"Order #{order_id}" if order_id else "Tahoe Bear Jerky Order"
        }
        
        # Link to Square order if provided (enables automatic tax)
        if square_order_id:
            body["order_id"] = square_order_id
        
        response, error = square_request('/payments', method='POST', body=body)
        
        if response and 'payment' in response:
            payment = response['payment']
            
            # Update order with payment info if order_id provided
            if order_id:
                conn = get_db_connection()
                cursor = conn.cursor()
                placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
                
                cursor.execute(f'''
                    UPDATE orders 
                    SET payment_status = {placeholder}, 
                        status = {placeholder},
                        square_payment_id = {placeholder}
                    WHERE id = {placeholder}
                ''', ('paid', 'processing', payment['id'], order_id))
                
                conn.commit()
                
                # Get order details for email
                cursor.execute(f'''
                    SELECT o.*, c.email, c.first_name, c.last_name
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    WHERE o.id = {placeholder}
                ''', (order_id,))
                order = cursor.fetchone()
                
                # Get order items
                cursor.execute(f'''
                    SELECT product_name as name, quantity, unit_price as price
                    FROM order_items
                    WHERE order_id = {placeholder}
                ''', (order_id,))
                items = [dict_from_row(row) for row in cursor.fetchall()]
                
                conn.close()
                
                # Send order confirmation email
                try:
                    from email_utils import send_order_confirmation_email
                    order_data = {
                        'order_number': order['order_number'],
                        'total': order['total'],
                        'items': items
                    }
                    send_order_confirmation_email(order['email'], order_data)
                except Exception as email_error:
                    print(f"Failed to send order confirmation email: {email_error}")
                    # Don't fail the payment if email fails
            
            return jsonify({
                'success': True,
                'payment_id': payment['id'],
                'status': payment['status'],
                'receipt_url': payment.get('receipt_url')
            }), 200
        else:
            return jsonify({
                'error': 'Payment failed',
                'details': error
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment/card-token', methods=['POST'])
def save_card_token():
    """Save Square card token for future use"""
    data = request.json
    customer_id = data.get('customer_id')
    card_nonce = data.get('card_nonce')
    
    if not customer_id or not card_nonce:
        return jsonify({'error': 'Missing required information'}), 400
    
    try:
        # Create card on file with Square
        body = {
            "idempotency_key": str(uuid.uuid4()),
            "source_id": card_nonce,
            "card": {
                "customer_id": customer_id
            }
        }
        
        response, error = square_request('/cards', method='POST', body=body)
        
        if response and 'card' in response:
            card = response['card']
            
            # Save card reference to database
            conn = get_db_connection()
            cursor = conn.cursor()
            placeholder = '%s' if DB_TYPE == 'postgresql' else '?'
            
            cursor.execute(f'''
                INSERT INTO payment_methods 
                (customer_id, square_card_id, card_brand, last_four, expiry_month, expiry_year)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                customer_id,
                card['id'],
                card.get('card_brand', 'UNKNOWN'),
                card.get('last_4', '****'),
                card.get('exp_month', 0),
                card.get('exp_year', 0)
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'card_id': card['id'],
                'last_four': card.get('last_4'),
                'brand': card.get('card_brand')
            }), 201
        else:
            return jsonify({'error': 'Failed to save card', 'details': error}), 400
            
    except Exception as e:
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
    print(f"📍 Square Environment: {SQUARE_ENVIRONMENT.upper()}")
    print(f"💳 Automatic tax calculation: ENABLED")
    app.run(debug=True, port=5000)
