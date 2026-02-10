#!/usr/bin/env python3
"""
Content Management System for Kabisa Enterprise ERP
Organizes, validates, and maintains all documentation files
"""

import os
import re
from pathlib import Path
from datetime import datetime

class ContentManager:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.docs_dir = self.base_path / "docs"
        self.archive_dir = self.base_path / "docs_archive"
        
    def organize_documentation(self):
        """Organize all documentation into proper structure"""
        print("🗂️  Organizing documentation...")
        
        # Create docs directory structure
        categories = {
            'getting-started': ['README.md', 'QUICK_START.md', 'QUICK_REFERENCE.md'],
            'architecture': ['SYSTEM_ARCHITECTURE.md', 'PROJECT_STRUCTURE.md'],
            'features': [
                'ORDER_FULFILLMENT_README.md',
                'FINANCIAL_ANALYTICS_README.md',
                'VEHICLE_MANAGEMENT_README.md',
                'LOGISTICS_KPI_IMPLEMENTATION.md',
                'TRANSFER_ALERT_SYSTEM.md'
            ],
            'implementation': [
                'IMPLEMENTATION_COMPLETE.md',
                'IMPLEMENTATION_SUMMARY.md',
                'EXPENSE_CRUD_IMPLEMENTATION.md',
                'FRONTEND_CRUD_SUMMARY.md',
                'ORDER_MANAGEMENT_ENHANCEMENT_SUMMARY.md'
            ],
            'deployment': ['DEPLOYMENT.md', 'SAFE_MIGRATION_PLAN.md'],
            'maintenance': ['FIXES_APPLIED.md']
        }
        
        # Create directory structure
        for category in categories.keys():
            (self.docs_dir / category).mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Created {len(categories)} documentation categories")
        return categories
    
    def scan_documentation(self):
        """Scan and catalog all documentation files"""
        print("\n📊 Scanning documentation files...")
        
        doc_files = {
            'markdown': list(self.base_path.glob('*.md')),
            'text': list(self.base_path.glob('*.txt')),
            'config': list(self.base_path.glob('*.yaml')) + list(self.base_path.glob('*.toml')),
            'scripts': [f for f in self.base_path.glob('*.py') if 'test' in f.name or 'fix' in f.name]
        }
        
        stats = {
            'total_docs': len(doc_files['markdown']) + len(doc_files['text']),
            'markdown_files': len(doc_files['markdown']),
            'text_files': len(doc_files['text']),
            'config_files': len(doc_files['config']),
            'utility_scripts': len(doc_files['scripts'])
        }
        
        print(f"   📄 Markdown files: {stats['markdown_files']}")
        print(f"   📝 Text files: {stats['text_files']}")
        print(f"   ⚙️  Config files: {stats['config_files']}")
        print(f"   🔧 Utility scripts: {stats['utility_scripts']}")
        print(f"   📊 Total documentation: {stats['total_docs']}")
        
        return doc_files, stats
    
    def validate_documentation(self, doc_files):
        """Validate documentation for completeness and quality"""
        print("\n✅ Validating documentation...")
        
        issues = []
        
        for md_file in doc_files['markdown']:
            try:
                content = md_file.read_text()
                
                # Check for empty files
                if len(content.strip()) < 100:
                    issues.append(f"⚠️  {md_file.name} is too short (< 100 chars)")
                
                # Check for proper headers
                if not content.startswith('#'):
                    issues.append(f"⚠️  {md_file.name} missing main header")
                
                # Check for last updated date
                if 'last updated' not in content.lower() and 'date' not in content.lower():
                    issues.append(f"ℹ️  {md_file.name} missing update date")
                    
            except Exception as e:
                issues.append(f"❌ Error reading {md_file.name}: {str(e)}")
        
        if issues:
            print(f"\n   Found {len(issues)} issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"   {issue}")
        else:
            print("   ✅ All documentation validated successfully")
        
        return issues
    
    def generate_content_report(self, doc_files, stats):
        """Generate comprehensive content report"""
        print("\n📋 Generating content report...")
        
        report = f"""# Content Management Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Documentation Statistics

- **Total Documentation Files:** {stats['total_docs']}
- **Markdown Files:** {stats['markdown_files']}
- **Text Files:** {stats['text_files']}
- **Configuration Files:** {stats['config_files']}
- **Utility Scripts:** {stats['utility_scripts']}

## File Inventory

### Markdown Documentation
"""
        for f in sorted(doc_files['markdown']):
            size = f.stat().st_size / 1024  # KB
            report += f"- {f.name} ({size:.1f} KB)\n"
        
        report += "\n### Configuration Files\n"
        for f in sorted(doc_files['config']):
            report += f"- {f.name}\n"
        
        report += "\n### Utility Scripts\n"
        for f in sorted(doc_files['scripts']):
            report += f"- {f.name}\n"
        
        report += f"""

## Recommendations

1. ✅ Keep core documentation (README, QUICK_START) up-to-date
2. 📦 Archive outdated implementation summaries
3. 🔄 Review and consolidate similar documents
4. 📝 Add missing update dates to documentation
5. 🗂️  Consider moving docs to /docs directory

## Next Actions

- [ ] Review and update README.md
- [ ] Consolidate implementation summaries
- [ ] Archive old test scripts
- [ ] Update CONTENT_INDEX.md
- [ ] Create changelog for major updates
"""
        
        return report
    
    def cleanup_temporary_files(self):
        """Identify and list temporary/obsolete files"""
        print("\n🧹 Identifying temporary files...")
        
        temp_patterns = [
            '*.pyc', '__pycache__', '*.log', '*.tmp',
            'receipt_*.html', '*_debug.py', '*_test.py'
        ]
        
        temp_files = []
        for pattern in temp_patterns:
            temp_files.extend(self.base_path.glob(pattern))
        
        if temp_files:
            print(f"   Found {len(temp_files)} temporary files")
            for f in temp_files[:5]:
                print(f"   - {f.name}")
        else:
            print("   ✅ No temporary files found")
        
        return temp_files
    
    def run_full_audit(self):
        """Run complete content management audit"""
        print("=" * 60)
        print("🚀 KABISA ERP - CONTENT MANAGEMENT SYSTEM")
        print("=" * 60)
        
        # Organize
        categories = self.organize_documentation()
        
        # Scan
        doc_files, stats = self.scan_documentation()
        
        # Validate
        issues = self.validate_documentation(doc_files)
        
        # Generate report
        report = self.generate_content_report(doc_files, stats)
        
        # Cleanup check
        temp_files = self.cleanup_temporary_files()
        
        # Save report
        report_path = self.base_path / 'CONTENT_MANAGEMENT_REPORT.md'
        report_path.write_text(report)
        print(f"\n📄 Report saved to: {report_path.name}")
        
        print("\n" + "=" * 60)
        print("✅ CONTENT MANAGEMENT AUDIT COMPLETE")
        print("=" * 60)
        
        return {
            'categories': categories,
            'stats': stats,
            'issues': issues,
            'temp_files': temp_files,
            'report_path': report_path
        }

if __name__ == '__main__':
    base_path = Path(__file__).parent
    manager = ContentManager(base_path)
    results = manager.run_full_audit()
    
    print(f"\n📊 Summary:")
    print(f"   - Documentation files: {results['stats']['total_docs']}")
    print(f"   - Issues found: {len(results['issues'])}")
    print(f"   - Temporary files: {len(results['temp_files'])}")
    print(f"\n📖 Review {results['report_path'].name} for details")
