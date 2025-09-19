#!/usr/bin/env python3
"""
Export Process Creator data with proper UTF-8 encoding
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from process_creator.models import Process, Step, Module, StepImage, StepLink, StepFile, AIInteraction
from django.core import serializers

def export_data():
    print("🔄 Exporting Process Creator data...")
    
    # Export each model separately
    all_data = []
    
    models = [
        ('Module', Module),
        ('Process', Process), 
        ('Step', Step),
        ('StepImage', StepImage),
        ('StepLink', StepLink),
        ('StepFile', StepFile),
        ('AIInteraction', AIInteraction)
    ]
    
    for model_name, model_class in models:
        print(f"  📦 Exporting {model_name}...")
        objects = model_class.objects.all()
        serialized = serializers.serialize('python', objects)
        all_data.extend(serialized)
        print(f"    ✅ {objects.count()} {model_name} objects exported")
    
    # Save to file with proper UTF-8 encoding
    output_file = 'process_creator_clean.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ Export complete: {output_file}")
    print(f"📊 Total objects exported: {len(all_data)}")
    
    # Also create a summary
    summary = {}
    for model_name, model_class in models:
        summary[model_name] = model_class.objects.count()
    
    with open('export_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("📋 Summary:")
    for model, count in summary.items():
        print(f"  {model}: {count}")

if __name__ == '__main__':
    export_data()
