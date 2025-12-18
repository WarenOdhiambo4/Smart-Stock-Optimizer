#!/usr/bin/env python3
"""
Installation script for Kabisa Enterprise Financial Analytics
Installs enterprise-grade financial libraries used by Fortune 500 companies
"""

import subprocess
import sys
import os

def run_command(command):
    """Run shell command and return result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_requirements():
    """Install all financial analytics requirements"""
    print("🚀 Installing Kabisa Enterprise Financial Analytics Stack...")
    print("📊 This includes libraries used by J.P. Morgan, Goldman Sachs, and major Fintechs\n")
    
    # Core financial libraries
    libraries = [
        ("pandas>=2.0.0", "Data processing engine (Excel on steroids)"),
        ("numpy>=1.24.0", "High-speed mathematical operations"),
        ("scipy>=1.10.0", "Scientific computing and optimization"),
        ("statsmodels>=0.14.0", "Statistical analysis and econometrics"),
        ("scikit-learn>=1.3.0", "Machine learning for predictions"),
        ("prophet>=1.1.4", "Facebook's forecasting algorithm"),
        ("pulp>=2.7.0", "Linear programming for optimization"),
        ("xlsxwriter>=3.1.0", "Professional Excel report generation"),
        ("reportlab>=4.0.0", "PDF report generation"),
        ("openpyxl>=3.1.0", "Excel file manipulation"),
        ("django-pandas>=0.6.6", "Django-Pandas integration"),
        ("matplotlib>=3.7.0", "Data visualization"),
        ("seaborn>=0.12.0", "Statistical data visualization"),
        ("plotly>=5.15.0", "Interactive charts")
    ]
    
    failed_installs = []
    
    for library, description in libraries:
        print(f"📦 Installing {library.split('>=')[0]}...")
        print(f"   Purpose: {description}")
        
        success, output = run_command(f"pip install {library}")
        
        if success:
            print(f"   ✅ Successfully installed {library.split('>=')[0]}")
        else:
            print(f"   ❌ Failed to install {library.split('>=')[0]}")
            failed_installs.append(library)
        
        print()
    
    return failed_installs

def verify_installation():
    """Verify that key libraries are properly installed"""
    print("🔍 Verifying installation...")
    
    test_imports = [
        ("pandas", "pd"),
        ("numpy", "np"),
        ("scipy", "scipy"),
        ("sklearn", "sklearn"),
        ("prophet", "Prophet"),
        ("pulp", "pulp"),
        ("xlsxwriter", "xlsxwriter"),
        ("reportlab", "reportlab")
    ]
    
    failed_imports = []
    
    for module, alias in test_imports:
        try:
            if alias == "Prophet":
                exec(f"from {module} import {alias}")
            else:
                exec(f"import {module} as {alias}")
            print(f"   ✅ {module} - OK")
        except ImportError as e:
            print(f"   ❌ {module} - FAILED: {e}")
            failed_imports.append(module)
    
    return failed_imports

def create_test_analytics():
    """Create a simple test to verify analytics work"""
    print("\n🧪 Creating analytics test...")
    
    test_code = '''
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create sample financial data
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
np.random.seed(42)

# Simulate sales data
sales_data = pd.DataFrame({
    'date': dates,
    'revenue': np.random.normal(1000, 200, len(dates)),
    'expenses': np.random.normal(600, 100, len(dates))
})

sales_data['profit'] = sales_data['revenue'] - sales_data['expenses']

# Calculate key metrics
total_revenue = sales_data['revenue'].sum()
total_profit = sales_data['profit'].sum()
profit_margin = (total_profit / total_revenue) * 100

print(f"📊 Analytics Test Results:")
print(f"   Total Revenue: ${total_revenue:,.2f}")
print(f"   Total Profit: ${total_profit:,.2f}")
print(f"   Profit Margin: {profit_margin:.1f}%")
print(f"   ✅ Analytics engine working correctly!")
'''
    
    try:
        exec(test_code)
        return True
    except Exception as e:
        print(f"   ❌ Analytics test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🏦 KABISA ENTERPRISE FINANCIAL ANALYTICS INSTALLER")
    print("=" * 60)
    print("Installing enterprise-grade libraries used by:")
    print("• J.P. Morgan Chase")
    print("• Goldman Sachs")
    print("• Morgan Stanley")
    print("• Major Fintech companies")
    print("=" * 60)
    print()
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  WARNING: You're not in a virtual environment!")
        print("   It's recommended to use a virtual environment.")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("   Installation cancelled.")
            return
        print()
    
    # Install requirements
    failed_installs = install_requirements()
    
    # Verify installation
    failed_imports = verify_installation()
    
    # Test analytics
    print()
    analytics_working = create_test_analytics()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 INSTALLATION SUMMARY")
    print("=" * 60)
    
    if not failed_installs and not failed_imports and analytics_working:
        print("🎉 SUCCESS! All financial analytics libraries installed correctly.")
        print("\n📈 Your ERP system now has:")
        print("   • Professional financial forecasting (Prophet)")
        print("   • Risk assessment (Value at Risk)")
        print("   • Inventory optimization (EOQ)")
        print("   • Route optimization (Linear Programming)")
        print("   • Excel report generation")
        print("   • Statistical analysis")
        print("\n🚀 Ready for enterprise-grade financial analytics!")
        
    else:
        print("⚠️  PARTIAL SUCCESS - Some issues detected:")
        
        if failed_installs:
            print(f"\n❌ Failed to install: {', '.join(failed_installs)}")
        
        if failed_imports:
            print(f"\n❌ Import errors: {', '.join(failed_imports)}")
        
        if not analytics_working:
            print("\n❌ Analytics test failed")
        
        print("\n🔧 Try running: pip install -r requirements.txt")
    
    print("\n📚 Next steps:")
    print("   1. Run: python manage.py migrate")
    print("   2. Visit: http://localhost:8000/analytics/")
    print("   3. Generate your first financial forecast!")
    print("=" * 60)

if __name__ == "__main__":
    main()