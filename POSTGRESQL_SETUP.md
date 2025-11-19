# PostgreSQL Setup Guide

## Quick Start

1. **Update `.env` file** with your PostgreSQL credentials:
```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tahoe_bear_jerky
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
```

2. **Create the database** (if it doesn't exist):
```sql
CREATE DATABASE tahoe_bear_jerky;
```

3. **Initialize the database**:
```powershell
python database/init_db.py
```

4. **Start the API server**:
```powershell
python api.py
```

## Detailed Setup

### Option 1: Using psql Command Line

```powershell
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE tahoe_bear_jerky;

# Exit psql
\q
```

### Option 2: Using pgAdmin

1. Open pgAdmin
2. Right-click on "Databases"
3. Select "Create" → "Database"
4. Name it `tahoe_bear_jerky`
5. Click "Save"

### Option 3: Using SQL Shell

```sql
-- Connect as postgres user
-- Then run:
CREATE DATABASE tahoe_bear_jerky
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;
```

## Verify Connection

Test your PostgreSQL connection:

```python
python -c "from database.db_config import Database; db = Database(); db.connect(); print('✓ Connected successfully!'); db.close()"
```

## Reset Database

To drop all tables and recreate:

```powershell
python database/init_db.py --reset
```

## Switch Between SQLite and PostgreSQL

Simply change the `DB_TYPE` in `.env`:

```env
# Use PostgreSQL
DB_TYPE=postgresql

# Or use SQLite
DB_TYPE=sqlite
```

Then restart the API server.

## Troubleshooting

### Connection Refused
- Make sure PostgreSQL is running
- Check if the port (5432) is correct
- Verify firewall settings

### Authentication Failed
- Double-check username and password in `.env`
- Ensure the PostgreSQL user has proper permissions

### Database Does Not Exist
- Create the database first using one of the methods above
- Or run: `createdb -U postgres tahoe_bear_jerky`

### Permission Denied
```sql
-- Grant permissions to your user
GRANT ALL PRIVILEGES ON DATABASE tahoe_bear_jerky TO your_username;
```

## PostgreSQL vs SQLite

| Feature | PostgreSQL | SQLite |
|---------|-----------|--------|
| **Performance** | Better for concurrent users | Good for single user |
| **Scalability** | Highly scalable | Limited |
| **Data Types** | Rich type system | Basic types |
| **Concurrency** | Excellent | Limited |
| **Setup** | Requires server | File-based, no setup |
| **Best For** | Production | Development/Testing |

## Recommended: PostgreSQL for Production

For production deployment, PostgreSQL is recommended because:
- ✅ Better performance with multiple concurrent users
- ✅ ACID compliance with better transaction support
- ✅ Advanced features (JSON, full-text search, etc.)
- ✅ Better security and user management
- ✅ Horizontal scaling capabilities

## Database Management Tools

- **pgAdmin**: GUI tool for PostgreSQL
- **DBeaver**: Universal database tool
- **DataGrip**: JetBrains database IDE
- **psql**: Command-line interface

## Backup and Restore

### Backup
```powershell
pg_dump -U postgres tahoe_bear_jerky > backup.sql
```

### Restore
```powershell
psql -U postgres tahoe_bear_jerky < backup.sql
```

## Next Steps

After setting up PostgreSQL:
1. Update your `.env` file
2. Run `python database/init_db.py`
3. Restart the API: `python api.py`
4. Verify at http://localhost:5000/api/health
