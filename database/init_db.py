import os
import sys
from dotenv import load_dotenv
from db_config import Database, DB_TYPE

# Load environment variables
load_dotenv()

def init_database():
    """Initialize the database with schema and seed data"""
    
    # Determine which schema file to use
    if DB_TYPE == 'postgresql':
        schema_file = 'schema_postgres.sql'
        print(f"🐘 Using PostgreSQL database")
    else:
        schema_file = 'schema.sql'
        print(f"📁 Using SQLite database")
    
    # Read schema file
    schema_path = os.path.join(os.path.dirname(__file__), schema_file)
    
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        return
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Connect to database
    with Database() as db:
        cursor = db.get_cursor()
        
        # Execute schema
        if DB_TYPE == 'postgresql':
            # PostgreSQL can execute the entire script at once
            cursor.execute(schema_sql)
        else:
            # SQLite needs executescript
            cursor.executescript(schema_sql)
        
        print("✓ Database schema created successfully")
        
        # Seed categories
        categories = [
            ('T-Shirts', 'tshirts', 'Comfortable and stylish t-shirts', 1),
            ('Sweaters', 'sweaters', 'Cozy sweaters and hoodies', 2),
            ('Hats', 'hats', 'Hats and beanies for all seasons', 3),
            ('Stickers', 'stickers', 'Weatherproof vinyl stickers', 4),
        ]
        
        for cat in categories:
            try:
                if DB_TYPE == 'postgresql':
                    cursor.execute('''
                        INSERT INTO categories (name, slug, description, display_order)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (slug) DO NOTHING
                    ''', cat)
                else:
                    cursor.execute('''
                        INSERT OR IGNORE INTO categories (name, slug, description, display_order)
                        VALUES (?, ?, ?, ?)
                    ''', cat)
            except Exception as e:
                print(f"Warning: Could not insert category {cat[0]}: {e}")
        
        print(f"✓ Inserted {len(categories)} categories")
        
        # Seed products
        products = [
            # T-Shirts
            ('Classic Bear Tee', 'classic-bear-tee', 1, 
             'Our signature tee featuring the iconic Tahoe Bear. Made from 100% organic cotton.', 
             29.99, None, '👕', 50, True, True),
            ('Don\'t Feed The Bears Tee', 'dont-feed-bears-tee', 1,
             'A friendly reminder to keep our wildlife wild. Soft and comfortable fit.',
             29.99, None, '👕', 45, True, False),
            
            # Sweaters
            ('Grid Life Hoodie', 'grid-life-hoodie', 2,
             'Perfect for chilly Tahoe evenings. Represents the Kings Beach Grid lifestyle.',
             59.99, None, '🧥', 30, True, True),
            ('Cozy Cabin Crewneck', 'cozy-cabin-crewneck', 2,
             'The ultimate lounging sweater. Guaranteed to make you want to hibernate.',
             54.99, None, '🧥', 25, True, False),
            
            # Hats
            ('Trucker Hat', 'trucker-hat', 3,
             'Keep the sun out of your eyes while spotting bears. Mesh back for breathability.',
             24.99, None, '🧢', 60, True, True),
            ('Beanie Cap', 'beanie-cap', 3,
             'Warm knit beanie for those snowy powder days.',
             22.99, None, '🧶', 40, True, False),
            
            # Stickers
            ('Bear Crossing Sticker', 'bear-crossing-sticker', 4,
             'High-quality vinyl sticker. Weatherproof and bear-proof.',
             4.99, None, '🏷️', 200, True, True),
            ('Tahoe Outline Sticker', 'tahoe-outline-sticker', 4,
             'Show your love for the lake. Perfect for water bottles and laptops.',
             4.99, None, '🏔️', 150, True, False),
        ]
        
        for prod in products:
            try:
                if DB_TYPE == 'postgresql':
                    cursor.execute('''
                        INSERT INTO products 
                        (name, slug, category_id, description, price, image_url, emoji, stock_quantity, is_active, featured)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (slug) DO NOTHING
                    ''', prod)
                else:
                    cursor.execute('''
                        INSERT OR IGNORE INTO products 
                        (name, slug, category_id, description, price, image_url, emoji, stock_quantity, is_active, featured)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', prod)
            except Exception as e:
                print(f"Warning: Could not insert product {prod[0]}: {e}")
        
        print(f"✓ Inserted {len(products)} products")
        
        # Seed jerky products (parody items)
        jerky_products = [
            ('Premium Bear Jerky', 'premium-bear-jerky', 'Premium Bear Jerky',
             'The original classic. Tough, chewy, and tastes vaguely of trash bags and pine needles.',
             45.00, '4oz', 'https://tahoebearjerky.com/bear_with_jerky.png', 'sold_out', 'SOLD OUT', None, 1, True),
            ('Spicy Lynx Jerky', 'spicy-lynx-jerky', 'Spicy Lynx Jerky',
             'Elusive flavor for the elusive palate. Catches you by surprise.',
             55.00, '3oz', 'https://tahoebearjerky.com/lynx_with_jerky.png', 'coming_soon', 'COMING SOON', None, 2, True),
            ('Coyote Snack Sticks', 'coyote-snack-sticks', 'Coyote Snack Sticks',
             'Lean, mean, and howlin\' with flavor. Best enjoyed under a full moon.',
             35.00, '6oz', 'https://tahoebearjerky.com/coyote_with_sign.png', 'seasonal', 'SEASONAL', None, 3, True),
        ]
        
        for jerky in jerky_products:
            try:
                if DB_TYPE == 'postgresql':
                    cursor.execute('''
                        INSERT INTO jerky_products 
                        (name, slug, title, description, price, weight, image_url, status, badge_text, badge_color, display_order, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (slug) DO NOTHING
                    ''', jerky)
                else:
                    cursor.execute('''
                        INSERT OR IGNORE INTO jerky_products 
                        (name, slug, title, description, price, weight, image_url, status, badge_text, badge_color, display_order, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', jerky)
            except Exception as e:
                print(f"Warning: Could not insert jerky product {jerky[0]}: {e}")
        
        print(f"✓ Inserted {len(jerky_products)} jerky products")
        
        # Get database info
        if DB_TYPE == 'postgresql':
            cursor.execute("SELECT current_database(), current_user")
            db_info = cursor.fetchone()
            print(f"\n✓ PostgreSQL database initialized successfully")
            print(f"  Database: {db_info['current_database']}")
            print(f"  User: {db_info['current_user']}")
        else:
            print(f"\n✓ SQLite database initialized successfully")
        
        print(f"✓ Total categories: {len(categories)}")
        print(f"✓ Total products: {len(products)}")
        print(f"✓ Total jerky products: {len(jerky_products)}")

def reset_database():
    """Delete all data and recreate the database"""
    print("⚠️  Resetting database...")
    
    with Database() as db:
        cursor = db.get_cursor()
        
        # Drop all tables
        tables = [
            'inventory_transactions',
            'product_images',
            'newsletter_subscribers',
            'order_items',
            'orders',
            'addresses',
            'customers',
            'products',
            'categories',
            'jerky_products'
        ]
        
        for table in tables:
            try:
                if DB_TYPE == 'postgresql':
                    cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
                else:
                    cursor.execute(f'DROP TABLE IF EXISTS {table}')
                print(f"  Dropped table: {table}")
            except Exception as e:
                print(f"  Warning: Could not drop table {table}: {e}")
    
    print("✓ Database reset complete\n")
    init_database()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        init_database()
