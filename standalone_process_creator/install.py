#!/usr/bin/env python3
"""
Process Creator Installation Script
This script helps install the Process Creator app into an existing Django project.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("🚀 Process Creator Installation Script")
    print("=" * 50)
    
    # Check if we're in a Django project
    if not os.path.exists('manage.py'):
        print("❌ Error: This doesn't appear to be a Django project.")
        print("   Please run this script from your Django project root directory.")
        sys.exit(1)
    
    # Check if process_creator already exists
    if os.path.exists('process_creator'):
        print("⚠️  Warning: process_creator directory already exists.")
        response = input("   Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("   Installation cancelled.")
            sys.exit(0)
        shutil.rmtree('process_creator')
    
    # Copy the process_creator app
    print("📁 Copying Process Creator app...")
    source_dir = Path(__file__).parent / 'process_creator'
    shutil.copytree(source_dir, 'process_creator')
    print("   ✅ App copied successfully")
    
    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("   ✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("   ⚠️  Warning: Could not install dependencies automatically.")
        print("   Please run: pip install -r requirements.txt")
    
    # Update settings.py
    print("⚙️  Updating settings.py...")
    settings_file = 'settings.py'
    if not os.path.exists(settings_file):
        # Try common locations
        for loc in ['myproject/settings.py', 'config/settings.py', 'django_project/settings.py']:
            if os.path.exists(loc):
                settings_file = loc
                break
    
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            content = f.read()
        
        # Add process_creator to INSTALLED_APPS if not present
        if "'process_creator'" not in content and '"process_creator"' not in content:
            # Find INSTALLED_APPS
            if "INSTALLED_APPS" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "INSTALLED_APPS" in line and "=" in line:
                        # Find the closing bracket
                        for j in range(i+1, len(lines)):
                            if ']' in lines[j]:
                                lines.insert(j, "    'process_creator',")
                                break
                        break
                content = '\n'.join(lines)
                
                with open(settings_file, 'w') as f:
                    f.write(content)
                print("   ✅ Added process_creator to INSTALLED_APPS")
            else:
                print("   ⚠️  Could not find INSTALLED_APPS in settings.py")
                print("   Please add 'process_creator' to your INSTALLED_APPS manually")
    else:
        print("   ⚠️  Could not find settings.py")
        print("   Please add the following to your settings.py:")
        print("   - Add 'process_creator' to INSTALLED_APPS")
        print("   - Add X_FRAME_OPTIONS = 'SAMEORIGIN'")
        print("   - Configure MEDIA_URL and MEDIA_ROOT")
    
    # Update urls.py
    print("🔗 Updating URLs...")
    urls_file = 'urls.py'
    if not os.path.exists(urls_file):
        for loc in ['myproject/urls.py', 'config/urls.py', 'django_project/urls.py']:
            if os.path.exists(loc):
                urls_file = loc
                break
    
    if os.path.exists(urls_file):
        with open(urls_file, 'r') as f:
            content = f.read()
        
        if 'process_creator' not in content:
            # Add the import and URL pattern
            if 'from django.urls import' in content:
                content = content.replace(
                    'from django.urls import',
                    'from django.urls import include,'
                )
            else:
                content = content.replace(
                    'from django.conf.urls import',
                    'from django.conf.urls import include,'
                )
            
            # Add URL pattern
            if 'urlpatterns' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'urlpatterns' in line and '=' in line:
                        for j in range(i+1, len(lines)):
                            if ']' in lines[j]:
                                lines.insert(j, "    path('process-creator/', include('process_creator.urls')),")
                                break
                        break
                content = '\n'.join(lines)
                
                with open(urls_file, 'w') as f:
                    f.write(content)
                print("   ✅ Added URL patterns")
            else:
                print("   ⚠️  Could not find urlpatterns in urls.py")
    else:
        print("   ⚠️  Could not find urls.py")
        print("   Please add the following to your main urls.py:")
        print("   - Add 'process_creator' to your URL patterns")
    
    # Create .env template
    print("📝 Creating .env template...")
    env_template = """# Process Creator Environment Variables
# Copy this to .env and fill in your values

# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# OpenAI API (required for AI features)
OPENAI_API_KEY=your-openai-api-key-here

# File conversion tools (optional)
# ODA_CONVERTER_PDF=path/to/oda-converter.exe
# INVENTOR_IDW_TO_PDF=path/to/inventor-converter.exe
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    print("   ✅ Created .env.template")
    
    # Run migrations
    print("🗄️  Running migrations...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'makemigrations', 'process_creator'], check=True)
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        print("   ✅ Migrations completed")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Migration error: {e}")
        print("   Please run: python manage.py makemigrations process_creator")
        print("   Then: python manage.py migrate")
    
    print("\n🎉 Installation Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Copy .env.template to .env and configure your settings")
    print("2. Set your OPENAI_API_KEY in the .env file")
    print("3. Run: python manage.py runserver")
    print("4. Visit: http://localhost:8000/process-creator/")
    print("\nFor more information, see the README.md file.")

if __name__ == '__main__':
    main()
