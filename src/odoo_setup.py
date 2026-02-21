"""
Odoo Community 19 Docker Setup Script (Gold Tier)
Self-hosted, local Odoo via Docker Desktop

Run this script once to start Odoo at http://localhost:8069
Create database ai_employee_db, user admin/admin
"""

import subprocess
import sys
from pathlib import Path

# Docker Compose configuration for Odoo 19 + PostgreSQL
DOCKER_COMPOSE_CONTENT = """
services:
  odoo:
    image: odoo:19
    container_name: odoo_community
    ports:
      - "8069:8069"
    depends_on:
      - db
    environment:
      - HOST=db
      - DATABASE=ai_employee_db
      - USER=admin
      - PASSWORD=admin
    volumes:
      - odoo_data:/var/lib/odoo
      - ./odoo_config:/etc/odoo
    restart: unless-stopped

  db:
    image: postgres:15
    container_name: odoo_postgres
    environment:
      - POSTGRES_DB=ai_employee_db
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=admin
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  odoo_data:
    driver: local
  postgres_data:
    driver: local
"""


def check_docker():
    """Check if Docker Desktop is installed and running."""
    print("Checking Docker Desktop...")
    
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Docker found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("Docker not found. Please install Docker Desktop.")
        print("Download: https://www.docker.com/products/docker-desktop/")
        return False
    
    return False


def check_docker_running():
    """Check if Docker Desktop is running."""
    print("Checking if Docker is running...")
    
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Docker Desktop is running.")
            return True
        else:
            print("Docker Desktop is not running. Please start Docker Desktop.")
            return False
    except Exception as e:
        print(f"Docker check error: {e}")
        return False


def write_docker_compose():
    """Write docker-compose.yml file."""
    script_dir = Path(__file__).parent
    docker_compose_file = script_dir / "docker-compose.yml"
    
    print(f"\nWriting {docker_compose_file.name}...")
    docker_compose_file.write_text(DOCKER_COMPOSE_CONTENT.strip(), encoding='utf-8')
    print(f"Created: {docker_compose_file}")
    return docker_compose_file


def start_containers():
    """Start Odoo and PostgreSQL containers."""
    script_dir = Path(__file__).parent
    
    print("\nStarting Odoo containers...")
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=script_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\nContainers started successfully!")
            return True
        else:
            print(f"\nError starting containers:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("\nError: Docker Compose not found.")
        print("Make sure Docker Desktop is installed and running.")
        return False
    except Exception as e:
        print(f"\nError: {e}")
        return False


def show_setup_info():
    """Display setup information and instructions."""
    print("\n" + "=" * 60)
    print("Odoo Community 19 Setup Complete!")
    print("=" * 60)
    print("\nAccess Odoo at: http://localhost:8069")
    print("\nDatabase Configuration (auto-configured):")
    print("  - Database name: ai_employee_db")
    print("  - Database user: admin")
    print("  - Database password: admin")
    print("  - PostgreSQL host: db (internal)")
    print("  - PostgreSQL port: 5432 (internal)")
    print("\nFirst-Time Setup:")
    print("  1. Open http://localhost:8069")
    print("  2. The database is pre-created, just set your admin password")
    print("  3. Install apps: Invoicing, Inventory, CRM, etc.")
    print("\nUseful Commands:")
    print("  - Stop: docker compose down")
    print("  - Restart: docker compose restart")
    print("  - View logs: docker compose logs -f odoo")
    print("  - Remove all: docker compose down -v")
    print("\nNote: Odoo Community Edition does not include built-in OCR.")
    print("For bank statements: Use CSV/Excel file imports.")
    print("\nData Persistence:")
    print("  - Odoo data: Docker volume 'odoo_data'")
    print("  - PostgreSQL data: Docker volume 'postgres_data'")
    print("=" * 60)


def main():
    print("=" * 60)
    print("Odoo Community 19 Docker Setup (Gold Tier)")
    print("=" * 60)
    
    # Check Docker
    if not check_docker():
        sys.exit(1)
    
    # Check Docker is running
    if not check_docker_running():
        print("\nPlease start Docker Desktop and run this script again.")
        sys.exit(1)
    
    # Write docker-compose.yml
    write_docker_compose()
    
    # Start containers
    if not start_containers():
        print("\nFailed to start containers. Check Docker Desktop.")
        sys.exit(1)
    
    # Show setup info
    show_setup_info()


if __name__ == "__main__":
    main()
