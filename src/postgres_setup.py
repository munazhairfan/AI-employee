"""
PostgreSQL Setup Script for Odoo
Installs and configures PostgreSQL for Odoo Community on Windows
"""

import subprocess
import sys
from pathlib import Path

PG_VERSION = "15"
PG_INSTALLER_URL = "https://get.enterprisedb.com/postgresql/postgresql-15.8-1-windows-x64.exe"
PG_INSTALLER_PATH = Path(__file__).parent / "postgresql_installer.exe"
PG_INSTALL_DIR = Path("C:/Program Files/PostgreSQL/15")


def check_postgresql():
    """Check if PostgreSQL is installed and running."""
    print("Checking PostgreSQL...")
    
    # Check if psql is available
    try:
        result = subprocess.run(
            ["psql", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"PostgreSQL found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    # Check if PostgreSQL service is running
    try:
        result = subprocess.run(
            ["sc", "query", f"postgresql-{PG_VERSION}"],
            capture_output=True,
            text=True
        )
        if "RUNNING" in result.stdout:
            print("PostgreSQL service is running.")
            return True
        elif "postgresql" in result.stdout.lower():
            print("PostgreSQL installed but not running. Starting service...")
            start_postgresql()
            return True
    except Exception as e:
        print(f"Service check error: {e}")
    
    print("PostgreSQL not found.")
    return False


def start_postgresql():
    """Start PostgreSQL Windows service."""
    print("Starting PostgreSQL service...")
    try:
        subprocess.run(
            ["net", "start", f"postgresql-{PG_VERSION}"],
            capture_output=True,
            text=True
        )
        print("PostgreSQL started.")
        return True
    except Exception as e:
        print(f"Failed to start PostgreSQL: {e}")
        return False


def install_postgresql():
    """Install PostgreSQL silently."""
    print(f"\nDownloading PostgreSQL {PG_VERSION}...")
    
    try:
        import requests
        
        response = requests.get(PG_INSTALLER_URL, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(PG_INSTALLER_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        print(f"\nDownloaded: {PG_INSTALLER_PATH}")
        
        # Run silent install
        print("\nInstalling PostgreSQL...")
        print("Note: You may need to run this script as Administrator.")
        
        # Silent install with default password 'admin'
        result = subprocess.run(
            [
                str(PG_INSTALLER_PATH),
                "--mode", "unattended",
                "--superpassword", "admin",
                "--servicepassword", "admin",
                "--serverport", "5432"
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("PostgreSQL installation completed!")
            
            # Start the service
            start_postgresql()
            
            # Cleanup installer
            try:
                PG_INSTALLER_PATH.unlink()
            except Exception:
                pass
            
            return True
        else:
            print(f"Installation failed with code: {result.returncode}")
            print("\nManual installation required:")
            print(f"1. Run: {PG_INSTALLER_PATH}")
            print("2. Set password: admin")
            print("3. Keep default port: 5432")
            return False
            
    except ImportError:
        print("requests library not found. Install with: pip install requests")
        return False
    except Exception as e:
        print(f"Download/install error: {e}")
        return False


def create_odoo_database():
    """Create the Odoo database."""
    print("\nCreating Odoo database: ai_employee_db")
    
    try:
        # Wait for PostgreSQL to be ready
        import time
        time.sleep(3)
        
        # Create database using psql
        result = subprocess.run(
            [
                "psql",
                "-U", "postgres",
                "-c", "CREATE DATABASE ai_employee_db;"
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PGPASSWORD": "admin"}
        )
        
        if result.returncode == 0 or "already exists" in result.stderr:
            print("Database created (or already exists).")
            
            # Create user
            result = subprocess.run(
                [
                    "psql",
                    "-U", "postgres",
                    "-c", "ALTER USER postgres WITH PASSWORD 'admin';"
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "PGPASSWORD": "admin"}
            )
            print("Database user configured.")
            return True
        else:
            print(f"Database creation error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Database setup error: {e}")
        print("\nYou can create the database manually via Odoo web interface:")
        print("http://localhost:8069")
        return False


def main():
    import os
    
    print("=" * 60)
    print("PostgreSQL Setup for Odoo")
    print("=" * 60)
    
    # Check if PostgreSQL is running
    if check_postgresql():
        create_odoo_database()
        print("\n" + "=" * 60)
        print("Setup complete!")
        print("=" * 60)
        print("\nOdoo should now connect to PostgreSQL.")
        print("Access Odoo at: http://localhost:8069")
        print("\nDatabase details:")
        print("  - Database: ai_employee_db")
        print("  - User: postgres / admin")
        print("  - Password: admin")
        print("  - Port: 5432")
        print("=" * 60)
        return
    
    # Install PostgreSQL
    if not install_postgresql():
        print("\nPostgreSQL installation failed.")
        print("\nManual steps:")
        print("1. Download PostgreSQL from: https://www.postgresql.org/download/windows/")
        print("2. Install with password: admin")
        print("3. Run this script again")
        sys.exit(1)
    
    # Create database
    create_odoo_database()
    
    print("\n" + "=" * 60)
    print("PostgreSQL setup complete!")
    print("=" * 60)
    print("\nNow restart Odoo and access at: http://localhost:8069")
    print("=" * 60)


if __name__ == "__main__":
    main()
