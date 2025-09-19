#!/usr/bin/env python3
"""
Process Creator Installation Script for Backend Setup
This script helps install the Process Creator app into a Django project with backend folder structure.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("🚀 Process Creator Installation Script (Backend Version)")
    print("=" * 60)
    
    # Check if we're in a Django project (look for manage.py in parent directory or current)
    if not os.path.exists('../manage.py') and not os.path.exists('manage.py'):
        print("❌ Error: This doesn't appear to be a Django project.")
        print("   Please run this script from the backend directory of your Django project.")
        print("   The parent directory should contain manage.py")
        sys.exit(1)
    
    # Check if process_creator already exists
    if os.path.exists('process_creator'):
        print("⚠️  Warning: process_creator directory already exists.")
        response = input("   Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("   Installation cancelled.")
            sys.exit(0)
        shutil.rmtree('process_creator')
    
    # Find the standalone_process_creator directory
    # Look in current directory first, then parent, then parent's parent
    source_dir = None
    possible_paths = [
        'standalone_process_creator/process_creator',
        '../standalone_process_creator/process_creator',
        '../../standalone_process_creator/process_creator',
        'standalone_process_creator',
        '../standalone_process_creator',
        '../../standalone_process_creator'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            if path.endswith('process_creator'):
                source_dir = path
                break
            elif os.path.exists(os.path.join(path, 'process_creator')):
                source_dir = os.path.join(path, 'process_creator')
                break
    
    if not source_dir:
        print("❌ Error: Could not find standalone_process_creator directory.")
        print("   Please ensure the standalone_process_creator folder is in:")
        print("   - Current directory")
        print("   - Parent directory") 
        print("   - Parent's parent directory")
        print("   Or run this script from the correct location.")
        sys.exit(1)
    
    print(f"📁 Found source directory: {source_dir}")
    
    # Copy the process_creator app
    print("📁 Copying Process Creator app...")
    try:
        shutil.copytree(source_dir, 'process_creator')
        print("   ✅ App copied successfully")
    except Exception as e:
        print(f"   ❌ Error copying app: {e}")
        sys.exit(1)
    
    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        # Look for requirements.txt in various locations
        req_file = None
        req_paths = [
            'standalone_process_creator/requirements.txt',
            '../standalone_process_creator/requirements.txt',
            '../../standalone_process_creator/requirements.txt',
            'requirements.txt'
        ]
        
        for path in req_paths:
            if os.path.exists(path):
                req_file = path
                break
        
        if req_file:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_file], check=True)
            print("   ✅ Dependencies installed")
        else:
            print("   ⚠️  Warning: Could not find requirements.txt")
            print("   Please install manually: pip install django openai xhtml2pdf python-docx pillow python-dotenv")
    except subprocess.CalledProcessError:
        print("   ⚠️  Warning: Could not install dependencies automatically.")
        print("   Please run: pip install django openai xhtml2pdf python-docx pillow python-dotenv")
    
    # Update settings.py
    print("⚙️  Updating settings.py...")
    settings_files = ['config/settings.py', 'settings.py', '../config/settings.py', '../settings.py']
    settings_file = None
    
    for file_path in settings_files:
        if os.path.exists(file_path):
            settings_file = file_path
            break
    
    if settings_file:
        try:
            with open(settings_file, 'r') as f:
                content = f.read()
            
            # Add process_creator to INSTALLED_APPS if not present
            if "'process_creator'" not in content and '"process_creator"' not in content:
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
                print(f"   ✅ Added process_creator to INSTALLED_APPS in {settings_file}")
            else:
                print(f"   ✅ process_creator already in INSTALLED_APPS in {settings_file}")
        except Exception as e:
            print(f"   ⚠️  Could not update {settings_file}: {e}")
            print("   Please add 'process_creator' to your INSTALLED_APPS manually")
    else:
        print("   ⚠️  Could not find settings.py")
        print("   Please add the following to your settings.py:")
        print("   - Add 'process_creator' to INSTALLED_APPS")
        print("   - Add X_FRAME_OPTIONS = 'SAMEORIGIN'")
        print("   - Configure MEDIA_URL and MEDIA_ROOT")
    
    # Update urls.py
    print("🔗 Updating URLs...")
    urls_files = ['config/urls.py', 'urls.py', '../config/urls.py', '../urls.py']
    urls_file = None
    
    for file_path in urls_files:
        if os.path.exists(file_path):
            urls_file = file_path
            break
    
    if urls_file:
        try:
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
                    print(f"   ✅ Added URL patterns to {urls_file}")
                else:
                    print(f"   ⚠️  Could not find urlpatterns in {urls_file}")
            else:
                print(f"   ✅ process_creator URLs already configured in {urls_file}")
        except Exception as e:
            print(f"   ⚠️  Could not update {urls_file}: {e}")
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
    
    try:
        with open('../.env.template', 'w') as f:
            f.write(env_template)
        print("   ✅ Created .env.template in parent directory")
    except Exception as e:
        print(f"   ⚠️  Could not create .env.template: {e}")
    
    # Run migrations
    print("🗄️  Running migrations...")
    try:
        subprocess.run([sys.executable, '../manage.py', 'makemigrations', 'process_creator'], check=True)
        subprocess.run([sys.executable, '../manage.py', 'migrate'], check=True)
        print("   ✅ Migrations completed")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Migration error: {e}")
        print("   Please run: python manage.py makemigrations process_creator")
        print("   Then: python manage.py migrate")
    
    print("\n🎉 Installation Complete!")
    print("=" * 60)
    print("Next steps:")
    print("1. Copy .env.template to .env and configure your settings")
    print("2. Set your OPENAI_API_KEY in the .env file")
    print("3. Run: python manage.py runserver")
    print("4. Visit: http://localhost:8000/process-creator/")
    print("\nFor more information, see the README.md file.")

if __name__ == '__main__':
    main()
