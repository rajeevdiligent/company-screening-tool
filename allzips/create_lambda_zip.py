#!/usr/bin/env python3
"""
Lambda Deployment Package Creator

This script creates a deployment-ready zip file for the Company Screening Lambda function.
It handles dependency installation, code packaging, and optimization for AWS Lambda.

Usage:
    python create_lambda_zip.py [--output-name custom_name.zip]
"""

import os
import sys
import shutil
import zipfile
import subprocess
import tempfile
import argparse
from pathlib import Path
from datetime import datetime

class LambdaZipCreator:
    """Creates optimized Lambda deployment packages"""
    
    def __init__(self, output_name=None):
        self.project_root = Path(__file__).parent.parent  # Go up one level from allzips to project root
        self.output_name = output_name or f"company-screening-lambda-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
        self.temp_dir = None
        
        # Files to include in the Lambda package
        self.python_files = [
            'lambda_handler.py',
            'optimized_company_search.py',
            'sec_filing_enhancer.py',
            'search_based_sec_extractor.py'
        ]
        
        # Files to exclude from the package
        self.exclude_patterns = [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.log',
            'outputjson/',
            'test_*',
            '*.sh',
            '*.md',
            'template.yaml',
            'samconfig.toml',
            'requirements.txt',  # Use requirements-lambda.txt instead
            '.env*',
            'env_template.txt'
        ]
    
    def create_temp_directory(self):
        """Create temporary directory for package assembly"""
        self.temp_dir = tempfile.mkdtemp(prefix='lambda_package_')
        print(f"📁 Created temporary directory: {self.temp_dir}")
        return self.temp_dir
    
    def install_dependencies(self):
        """Install Lambda-specific dependencies"""
        print("📦 Installing Lambda dependencies...")
        
        # Check for requirements file in multiple locations
        requirements_file = self.project_root / 'requirements-lambda.txt'
        if not requirements_file.exists():
            requirements_file = self.project_root / 'src' / 'requirements-lambda.txt'
        if not requirements_file.exists():
            requirements_file = self.project_root / 'allzips' / 'requirements-lambda.txt'
        if not requirements_file.exists():
            print("❌ requirements-lambda.txt not found!")
            return False
        
        try:
            # Install dependencies to temp directory
            cmd = [
                sys.executable, '-m', 'pip', 'install',
                '-r', str(requirements_file),
                '-t', self.temp_dir,
                '--no-deps',  # Don't install dependencies of dependencies
                '--upgrade'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Dependency installation failed: {result.stderr}")
                return False
            
            print("✅ Dependencies installed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def copy_python_files(self):
        """Copy Python source files to temp directory"""
        print("📄 Copying Python source files...")
        
        for file_name in self.python_files:
            # Look for files in src/ directory first, then root
            source_file = self.project_root / 'src' / file_name
            if not source_file.exists():
                source_file = self.project_root / file_name
            
            if source_file.exists():
                dest_file = Path(self.temp_dir) / file_name
                shutil.copy2(source_file, dest_file)
                print(f"  ✅ Copied {file_name} from {source_file.parent.name}/")
            else:
                print(f"  ⚠️ Warning: {file_name} not found in src/ or root")
    
    def clean_package(self):
        """Remove unnecessary files from package"""
        print("🧹 Cleaning package...")
        
        temp_path = Path(self.temp_dir)
        
        # Remove common unnecessary files
        unnecessary_patterns = [
            '**/__pycache__',
            '**/*.pyc',
            '**/*.pyo',
            '**/*.dist-info',
            '**/*.egg-info',
            '**/tests',
            '**/test_*',
            '**/*.so',  # Compiled extensions (Lambda has its own)
            '**/bin',   # Binary files
            '**/share', # Shared files
        ]
        
        for pattern in unnecessary_patterns:
            for item in temp_path.glob(pattern):
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    print(f"  🗑️ Removed directory: {item.name}")
                elif item.is_file():
                    item.unlink()
                    print(f"  🗑️ Removed file: {item.name}")
    
    def create_zip_file(self):
        """Create the final zip file"""
        print(f"📦 Creating zip file: {self.output_name}")
        
        zip_path = self.project_root / self.output_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            temp_path = Path(self.temp_dir)
            
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for zip
                    relative_path = file_path.relative_to(temp_path)
                    zipf.write(file_path, relative_path)
        
        # Get zip file size
        zip_size = zip_path.stat().st_size
        zip_size_mb = zip_size / (1024 * 1024)
        
        print(f"✅ Zip file created: {zip_path}")
        print(f"📊 Package size: {zip_size_mb:.2f} MB")
        
        # Check Lambda size limits
        if zip_size_mb > 50:
            print("⚠️ Warning: Package size exceeds 50MB Lambda limit!")
        elif zip_size_mb > 10:
            print("⚠️ Warning: Large package size may affect cold start performance")
        
        return zip_path
    
    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temporary directory")
    
    def create_package(self):
        """Main method to create the Lambda package"""
        print("🚀 Starting Lambda package creation...")
        print(f"📁 Project root: {self.project_root}")
        
        try:
            # Create temp directory
            self.create_temp_directory()
            
            # Install dependencies
            if not self.install_dependencies():
                return None
            
            # Copy Python files
            self.copy_python_files()
            
            # Clean package
            self.clean_package()
            
            # Create zip file
            zip_path = self.create_zip_file()
            
            print("\n🎉 Lambda package created successfully!")
            print(f"📦 Package: {zip_path}")
            print(f"🔧 Ready for deployment to AWS Lambda")
            
            return zip_path
            
        except Exception as e:
            print(f"❌ Error creating package: {e}")
            return None
            
        finally:
            self.cleanup()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Create Lambda deployment package')
    parser.add_argument('--output-name', '-o', 
                       help='Custom output zip file name')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create the package
    creator = LambdaZipCreator(output_name=args.output_name)
    zip_path = creator.create_package()
    
    if zip_path:
        print(f"\n✅ Success! Lambda package ready: {zip_path}")
        print("\n📋 Next steps:")
        print("1. Upload to AWS Lambda console, or")
        print("2. Use AWS CLI: aws lambda update-function-code --function-name company-screening-tool --zip-file fileb://package.zip")
        print("3. Or deploy with SAM: sam deploy")
        sys.exit(0)
    else:
        print("\n❌ Failed to create Lambda package")
        sys.exit(1)

if __name__ == "__main__":
    main()
