import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to PostgreSQL server (not to a specific database)
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', '5433'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', '')
)

# Set autocommit mode to create database
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

db_name = os.getenv('POSTGRES_DB', 'tahoe_bear_jerky')

# Check if database exists
cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
exists = cursor.fetchone()

if exists:
    print(f"✓ Database '{db_name}' already exists")
else:
    # Create database
    cursor.execute(f'CREATE DATABASE {db_name}')
    print(f"✓ Created database '{db_name}'")

cursor.close()
conn.close()

print(f"\n✓ PostgreSQL setup complete!")
print(f"  Host: {os.getenv('POSTGRES_HOST', 'localhost')}")
print(f"  Port: {os.getenv('POSTGRES_PORT', '5433')}")
print(f"  Database: {db_name}")
print(f"\nNow run: python database/init_db.py")
