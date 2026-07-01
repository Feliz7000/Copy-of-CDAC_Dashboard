"""
Script to manually create database schema from SQL file
Run this after: docker-compose exec backend python manage.py migrate
"""
import os
import sys
import psycopg2
from django.conf import settings
from pathlib import Path

# Get database credentials from Django settings
DB_NAME = os.getenv('POSTGRES_DB', 'student_analytics')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

# Path to SQL file
SQL_FILE = Path(__file__).parent.parent / 'backend_sql_view2_test.sql'

def run_sql():
    """Execute SQL schema file"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        print(f"Connected to {DB_NAME} on {DB_HOST}:{DB_PORT}")
        print(f"Reading SQL from: {SQL_FILE}")
        
        # Read and execute SQL file
        with open(SQL_FILE, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolons and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            try:
                cursor.execute(statement)
                print(f"✓ Statement {i}/{len(statements)} executed")
            except psycopg2.Error as e:
                print(f"⚠ Statement {i} warning: {e}")
                # Continue even if some statements fail (e.g., IF EXISTS checks)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✅ Successfully initialized database schema!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ SQL file not found: {SQL_FILE}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = run_sql()
    sys.exit(0 if success else 1)
