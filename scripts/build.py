#!/usr/bin/env python3
"""Build script to create a single-file zipapp bundle from src/."""

import os
import shutil
import sys
import zipfile
from pathlib import Path


def create_zipapp():
    """Create a Python zipapp from the source directory."""
    # Get paths
    repo_root = Path(__file__).parent.parent
    src_dir = repo_root / "src"
    dist_dir = repo_root / "dist"
    output_file = dist_dir / "wbat_statusbar.py"
    
    # Ensure dist directory exists
    dist_dir.mkdir(exist_ok=True)
    
    # Remove existing bundle
    if output_file.exists():
        output_file.unlink()
    
    # Create zipapp
    print(f"Building zipapp: {output_file}")
    
    # Create a temporary directory for the bundle
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy source files (src/wbat_statusbar -> wbat_statusbar in zipapp)
        src_package = src_dir / "wbat_statusbar"
        shutil.copytree(src_package, temp_path / "wbat_statusbar", dirs_exist_ok=True)
        
        # Create __main__.py entry point
        main_py = temp_path / "__main__.py"
        main_py.write_text("""# Entry point for zipapp
import sys
import os

# Add zipapp to path
if hasattr(sys, 'frozen'):
    # Running as zipapp
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    # Running as script
    sys.path.insert(0, os.path.dirname(__file__))

from wbat_statusbar.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
""")
        
        # Create zipfile
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from temp directory
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
        
        # Make it executable
        os.chmod(output_file, 0o755)
    
    print(f"✓ Created zipapp: {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Verify it's a valid zipapp
    try:
        with zipfile.ZipFile(output_file, 'r') as zipf:
            if '__main__.py' not in zipf.namelist():
                print("⚠ Warning: __main__.py not found in zipapp")
                sys.exit(1)
        print("✓ Zipapp verification passed")
    except Exception as e:
        print(f"✗ Zipapp verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_zipapp()
