#!/usr/bin/env python3
"""
Database Connectivity Test Script
Test connection to external PostgreSQL server
"""

import os
import sys
import socket
import time
import psycopg2
from urllib.parse import urlparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from models.config import config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: Could not import config, using environment variables")

def check_ssl_status(cursor, sslmode):
    """Check SSL status using multiple methods"""
    
    # If SSL explicitly disabled, don't check
    if sslmode == 'disable':
        return "Disabled (sslmode=disable)"
    
    # Method 1: Try ssl_is_used() function (PostgreSQL 14+)
    try:
        cursor.execute("SELECT ssl_is_used()")
        ssl_used = cursor.fetchone()[0]
        if ssl_used:
            # Try to get SSL version if available
            try:
                cursor.execute("SELECT current_setting('ssl_version')")
                ssl_version = cursor.fetchone()[0]
                return f"Enabled (Version: {ssl_version})"
            except:
                return "Enabled (Version: Unknown)"
        else:
            return "Not Used"
    except:
        pass
    
    # Method 2: Check pg_stat_ssl view (PostgreSQL 9.5+)
    try:
        cursor.execute("""
            SELECT ssl, version, cipher 
            FROM pg_stat_ssl 
            WHERE pid = pg_backend_pid()
        """)
        ssl_info = cursor.fetchone()
        if ssl_info and ssl_info[0]:  # ssl column is True
            version = ssl_info[1] or 'Unknown'
            cipher = ssl_info[2] or 'Unknown'
            return f"Enabled (Version: {version}, Cipher: {cipher})"
        else:
            return "Not Used"
    except:
        pass
    
    # Method 3: Try to get SSL-related settings
    try:
        cursor.execute("SHOW ssl")
        ssl_setting = cursor.fetchone()[0]
        if ssl_setting.lower() == 'on':
            return f"Enabled (Server SSL: {ssl_setting}, Mode: {sslmode})"
        else:
            return f"Server SSL Off (Mode: {sslmode})"
    except:
        pass
    
    # Fallback: Based on sslmode only
    ssl_modes = {
        'allow': 'May use SSL',
        'prefer': 'Prefers SSL', 
        'require': 'Requires SSL',
        'verify-ca': 'Requires SSL + CA verification',
        'verify-full': 'Requires SSL + Full verification'
    }
    
    return ssl_modes.get(sslmode, f"Unknown (Mode: {sslmode})")


def test_tcp_connection(host, port, timeout=5):
    """Test TCP connection to host:port"""
    print(f"🔍 Testing TCP connection to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()
        
        sock.close()
        
        if result == 0:
            print(f"✅ TCP connection successful ({end_time - start_time:.2f}s)")
            return True
        else:
            print(f"❌ TCP connection failed (error code: {result})")
            return False
            
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_postgresql_connection():
    """Test PostgreSQL connection"""
    print(f"\n🔍 Testing PostgreSQL connection...")
    
    # Get connection parameters
    if CONFIG_AVAILABLE:
        db_url = config.DATABASE_URL
        host = config.POSTGRES_HOST
        port = config.POSTGRES_PORT
        database = config.POSTGRES_DB
        user = config.POSTGRES_USER
        password = config.POSTGRES_PASSWORD
        ssl_config = config.get_postgres_ssl_config()
    else:
        db_url = os.getenv('DATABASE_URL', '')
        host = os.getenv('POSTGRES_HOST', '30.30.30.11')
        port = int(os.getenv('POSTGRES_PORT', '5456'))
        database = os.getenv('POSTGRES_DB', 'mydb')
        user = os.getenv('POSTGRES_USER', 'myuser')
        password = os.getenv('POSTGRES_PASSWORD', 'mypass')
        ssl_config = {'sslmode': os.getenv('POSTGRES_SSL_MODE', 'prefer')}
    
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Database: {database}")
    print(f"  User: {user}")
    print(f"  SSL Mode: {ssl_config.get('sslmode', 'default')}")
    
    try:
        # Build connection parameters
        conn_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'connect_timeout': 10
        }
        
        # Add SSL parameters
        conn_params.update(ssl_config)
        
        # Connect to PostgreSQL
        start_time = time.time()
        conn = psycopg2.connect(**conn_params)
        end_time = time.time()
        
        print(f"✅ PostgreSQL connection successful ({end_time - start_time:.2f}s)")
        
        # Test basic operations
        cursor = conn.cursor()
        
        # Get version info
        cursor.execute('SELECT version()')
        version = cursor.fetchone()[0]
        print(f"  PostgreSQL Version: {version[:80]}...")
        
        # Get basic connection info
        cursor.execute('''
            SELECT current_database(), current_user, 
                   inet_server_addr(), inet_server_port()
        ''')
        info = cursor.fetchone()
        
        print(f"  Current Database: {info[0]}")
        print(f"  Current User: {info[1]}")
        print(f"  Server IP: {info[2] if info[2] else 'Local/Unix Socket'}")
        print(f"  Server Port: {info[3] if info[3] else 'N/A'}")
        
        # Check SSL status with multiple methods
        ssl_status = check_ssl_status(cursor, ssl_config.get('sslmode', 'disable'))
        print(f"  SSL Status: {ssl_status}")
        
        # Test table access (if tables exist)
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            ''')
            table_count = cursor.fetchone()[0]
            print(f"  Public Tables: {table_count}")
        except Exception as e:
            print(f"  Public Tables: Error accessing ({str(e)[:50]}...)")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_dns_resolution(host):
    """Test DNS resolution"""
    print(f"🔍 Testing DNS resolution for {host}...")
    
    try:
        start_time = time.time()
        addr_info = socket.getaddrinfo(host, None)
        end_time = time.time()
        
        ips = list(set([info[4][0] for info in addr_info]))
        print(f"✅ DNS resolution successful ({end_time - start_time:.2f}s)")
        print(f"  Resolved IPs: {', '.join(ips)}")
        return True
        
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Database Connectivity Test")
    print("=" * 50)
    
    # Get connection parameters
    if CONFIG_AVAILABLE:
        host = config.POSTGRES_HOST
        port = config.POSTGRES_PORT
    else:
        host = os.getenv('POSTGRES_HOST', '30.30.30.11')
        port = int(os.getenv('POSTGRES_PORT', '5456'))
    
    print(f"Target: {host}:{port}")
    print()
    
    # Run tests
    results = {}
    
    # Test 1: DNS Resolution
    results['dns'] = test_dns_resolution(host)
    
    # Test 2: TCP Connection
    results['tcp'] = test_tcp_connection(host, port)
    
    # Test 3: PostgreSQL Connection
    results['postgresql'] = test_postgresql_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  DNS Resolution: {'✅ PASS' if results['dns'] else '❌ FAIL'}")
    print(f"  TCP Connection: {'✅ PASS' if results['tcp'] else '❌ FAIL'}")
    print(f"  PostgreSQL:     {'✅ PASS' if results['postgresql'] else '❌ FAIL'}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! Database is ready for production.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check network connectivity and credentials.")
        return 1

if __name__ == '__main__':
    exit(main())
