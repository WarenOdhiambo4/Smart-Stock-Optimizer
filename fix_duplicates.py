#!/usr/bin/env python
"""
Fix duplicate sync issues by:
1. Adding airtable_id fields to models
2. Cleaning up existing duplicates in Airtable
3. Mapping existing records to prevent future duplicates
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_project.settings')
django.setup()

from core.models import Branch, Product, Sale, Order, Employee, Vehicle, Trip
from core.airtable_service import airtable_service

def add_airtable_id_fields():
    """Add airtable_id fields to models via migration"""
    print("📝 Adding airtable_id fields to models...")
    
    # Create migration content
    migration_content = '''
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='order',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='trip',
            name='airtable_id',
            field=models.CharField(max_length=50, blank=True, null=True, unique=True),
        ),
    ]
'''
    
    # Write migration file
    import glob
    migration_files = glob.glob('core/migrations/0*.py')
    next_number = len(migration_files) + 1
    migration_filename = f'core/migrations/{next_number:04d}_add_airtable_ids.py'
    
    with open(migration_filename, 'w') as f:
        f.write(migration_content)
    
    print(f"✅ Migration created: {migration_filename}")
    print("Run: python manage.py migrate")

def clean_airtable_duplicates():
    """Remove duplicates from Airtable tables"""
    tables = ['Branches', 'Products', 'Sales', 'Orders', 'Employees', 'Vehicles', 'Trips']
    
    for table_name in tables:
        print(f"\n🧹 Cleaning duplicates in {table_name}...")
        try:
            records = airtable_service.get_records(table_name)
            
            # Group by unique identifier
            seen = {}
            duplicates = []
            
            for record in records:
                fields = record['fields']
                
                # Define unique keys for each table
                if table_name == 'Branches':
                    key = fields.get('Name', '')
                elif table_name == 'Products':
                    key = fields.get('SKU', '')
                elif table_name == 'Sales':
                    key = fields.get('Sale Number', '')
                elif table_name == 'Orders':
                    key = fields.get('Order Number', '')
                elif table_name == 'Employees':
                    key = fields.get('Email', '')
                elif table_name == 'Vehicles':
                    key = fields.get('Registration Number', '')
                elif table_name == 'Trips':
                    key = fields.get('Trip Number', '')
                else:
                    continue
                
                if key in seen:
                    duplicates.append(record['id'])
                    print(f"  🗑️  Duplicate found: {key}")
                else:
                    seen[key] = record['id']
            
            # Delete duplicates
            for duplicate_id in duplicates:
                try:
                    airtable_service.delete_record(table_name, duplicate_id)
                    print(f"  ✅ Deleted duplicate: {duplicate_id}")
                except Exception as e:
                    print(f"  ❌ Failed to delete {duplicate_id}: {e}")
            
            print(f"✅ Cleaned {len(duplicates)} duplicates from {table_name}")
            
        except Exception as e:
            print(f"❌ Error cleaning {table_name}: {e}")

def map_existing_records():
    """Map existing Django records to Airtable records"""
    print("\n🔗 Mapping existing records...")
    
    # Map Branches
    try:
        airtable_branches = airtable_service.get_records('Branches')
        for record in airtable_branches:
            name = record['fields'].get('Name', '')
            try:
                branch = Branch.objects.get(name=name)
                if hasattr(branch, 'airtable_id'):
                    branch.airtable_id = record['id']
                    branch.save(update_fields=['airtable_id'])
                    print(f"  ✅ Mapped Branch: {name}")
            except Branch.DoesNotExist:
                print(f"  ⚠️  Branch not found in Django: {name}")
    except Exception as e:
        print(f"❌ Error mapping branches: {e}")
    
    # Map Products
    try:
        airtable_products = airtable_service.get_records('Products')
        for record in airtable_products:
            sku = record['fields'].get('SKU', '')
            try:
                product = Product.objects.get(sku=sku)
                if hasattr(product, 'airtable_id'):
                    product.airtable_id = record['id']
                    product.save(update_fields=['airtable_id'])
                    print(f"  ✅ Mapped Product: {sku}")
            except Product.DoesNotExist:
                print(f"  ⚠️  Product not found in Django: {sku}")
    except Exception as e:
        print(f"❌ Error mapping products: {e}")

def main():
    print("🚀 Starting duplicate cleanup process...")
    
    print("\n" + "="*50)
    print("STEP 1: Add airtable_id fields to models")
    print("="*50)
    add_airtable_id_fields()
    
    print("\n" + "="*50)
    print("STEP 2: Clean duplicates from Airtable")
    print("="*50)
    clean_airtable_duplicates()
    
    print("\n" + "="*50)
    print("STEP 3: Map existing records")
    print("="*50)
    print("⚠️  Run this AFTER applying the migration!")
    print("Commands to run:")
    print("1. python manage.py migrate")
    print("2. python fix_duplicates.py --map-only")
    
    print("\n🎉 Duplicate cleanup process completed!")
    print("\n📋 Next steps:")
    print("1. Run the migration: python manage.py migrate")
    print("2. Map existing records: python fix_duplicates.py --map-only")
    print("3. Test sync to ensure no more duplicates")

def map_only():
    """Only run the mapping step"""
    print("🔗 Mapping existing records only...")
    map_existing_records()
    print("✅ Mapping completed!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--map-only':
        map_only()
    else:
        main()