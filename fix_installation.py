#!/usr/bin/env python3
"""
Quick fix script for Process Creator installation
"""
import os
import sys
import subprocess

def main():
    print("🔧 Fixing Process Creator Installation...")
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: Please run this from the Django project root (where manage.py is)")
        sys.exit(1)
    
    # Check if process_creator exists
    if not os.path.exists('backend/process_creator'):
        print("❌ Error: process_creator app not found in backend/")
        print("   Please copy the process_creator app to backend/ first")
        sys.exit(1)
    
    print("✅ Found process_creator app")
    
    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'django', 'openai', 'xhtml2pdf', 'python-docx', 'pillow', 'python-dotenv'], check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("⚠️  Warning: Could not install dependencies automatically")
    
    # Run migrations
    print("🗄️  Running migrations...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'makemigrations', 'process_creator'], check=True)
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        print("✅ Migrations completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration error: {e}")
        print("   Please check your settings.py and urls.py configuration")
        return
    
    # Try to load data
    if os.path.exists('process_creator_clean.json'):
        print("📥 Loading data...")
        try:
            subprocess.run([sys.executable, 'manage.py', 'loaddata', 'process_creator_clean.json'], check=True)
            print("✅ Data loaded successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Data loading error: {e}")
            print("   You may need to check the data file or run migrations first")
    else:
        print("⚠️  No data file found (process_creator_clean.json)")
    
    print("\n🎉 Installation fix complete!")
    print("Next steps:")
    print("1. Check your settings.py has 'process_creator' in INSTALLED_APPS")
    print("2. Check your urls.py has the process_creator URL patterns")
    print("3. Run: python manage.py runserver")
    print("4. Visit: http://localhost:8000/process-creator/")

if __name__ == '__main__':
    main()
