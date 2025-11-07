"""
Django views for NinjaTrader 8 package management and distribution.

This module provides web endpoints for:
- Automated package compilation and ZIP generation
- Build status monitoring (DLL freshness checking)
- NT8-compatible package downloads with flat structure
- Installation and troubleshooting documentation
- Manual compilation triggers

Integration:
- Uses build_and_test.sh from src/services/ninja/ as backend
- Generates timestamped ZIP packages (FKS_AsyncStrategy_YYYYMMDD_HHMMSS.zip)
- Creates comprehensive README with installation steps
"""

import os
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

# Base paths (adjust if needed based on Django project structure)
NINJA_BASE = Path(settings.BASE_DIR).parent.parent / 'services' / 'ninja'
BUILD_SCRIPT = NINJA_BASE / 'build_and_test.sh'
DLL_PATH = NINJA_BASE / 'bin' / 'Release' / 'FKS.dll'
SOURCE_CS = NINJA_BASE / 'src' / 'Strategies' / 'FKS_AsyncStrategy.cs'


@login_required
@require_http_methods(["GET"])
def download_nt8_package(request):
    """
    Generate and download NT8-compatible ZIP package.

    Workflow:
    1. Check if build is needed (DLL older than source)
    2. Run build_and_test.sh if necessary
    3. Create timestamped ZIP package
    4. Stream to user with proper headers

    Returns:
        HttpResponse: ZIP file download
        JsonResponse: Error details if build fails
    """
    try:
        # Check if rebuild is needed
        build_needed = check_build_needed()

        if build_needed:
            print(f"[{datetime.now():%H:%M:%S}] Build needed - DLL older than source")
            result = run_build_script()

            if not result['success']:
                return JsonResponse({
                    'error': 'Build failed',
                    'details': result.get('error', 'Unknown error'),
                    'output': result.get('output', '')
                }, status=500)

        # Verify DLL exists
        if not DLL_PATH.exists():
            return JsonResponse({
                'error': 'DLL not found',
                'details': f'Expected: {DLL_PATH}',
                'hint': 'Run build manually or check build script'
            }, status=500)

        # Create ZIP package
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'FKS_AsyncStrategy_{timestamp}.zip'

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / zip_filename

            # Build package contents
            package_files = prepare_package_files()

            # Create ZIP with flat structure (NT8 requirement)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path, archive_name in package_files.items():
                    if file_path.exists():
                        zipf.write(file_path, archive_name)

            # Read ZIP into memory
            with open(zip_path, 'rb') as f:
                zip_data = f.read()

        # Stream to user
        response = HttpResponse(zip_data, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
        response['X-Package-Version'] = '1.0.0'
        response['X-Build-Date'] = datetime.now().isoformat()

        print(f"[{datetime.now():%H:%M:%S}] Package downloaded: {zip_filename} ({len(zip_data)} bytes)")
        return response

    except subprocess.CalledProcessError as e:
        return JsonResponse({
            'error': 'Build script failed',
            'details': e.stderr.decode('utf-8') if e.stderr else str(e),
            'return_code': e.returncode
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': 'Package generation failed',
            'details': str(e),
            'type': type(e).__name__
        }, status=500)


@login_required
@require_http_methods(["GET"])
def build_status(request):
    """
    Check if compiled DLL exists and is up-to-date.

    Returns JSON with:
    - dll_exists: bool
    - source_exists: bool
    - build_required: bool (True if source is newer than DLL)
    - dll_timestamp: ISO datetime string
    - source_timestamp: ISO datetime string
    - dll_size_kb: float

    Returns:
        JsonResponse: Build status information
    """
    try:
        dll_exists = DLL_PATH.exists()
        source_exists = SOURCE_CS.exists()

        status_data = {
            'dll_exists': dll_exists,
            'source_exists': source_exists,
            'build_required': False,
            'dll_timestamp': None,
            'source_timestamp': None,
            'dll_size_kb': None,
        }

        if dll_exists:
            dll_stat = DLL_PATH.stat()
            status_data['dll_timestamp'] = datetime.fromtimestamp(dll_stat.st_mtime).isoformat()
            status_data['dll_size_kb'] = round(dll_stat.st_size / 1024, 2)

        if source_exists:
            source_stat = SOURCE_CS.stat()
            status_data['source_timestamp'] = datetime.fromtimestamp(source_stat.st_mtime).isoformat()

            # Check if rebuild needed
            if dll_exists and source_stat.st_mtime > dll_stat.st_mtime:
                status_data['build_required'] = True
                status_data['reason'] = 'Source modified after last build'

        if not dll_exists:
            status_data['build_required'] = True
            status_data['reason'] = 'DLL not found'

        return JsonResponse(status_data)

    except Exception as e:
        return JsonResponse({
            'error': 'Build status check failed',
            'details': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def trigger_build(request):
    """
    Manually trigger build via build_and_test.sh.

    Returns JSON with build result, output logs, and error details.

    Returns:
        JsonResponse: Build result with success status and logs
    """
    try:
        print(f"[{datetime.now():%H:%M:%S}] Manual build triggered by {request.user.username}")

        result = run_build_script()

        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Build completed successfully',
                'output': result.get('output', ''),
                'timestamp': datetime.now().isoformat(),
                'dll_size_kb': round(DLL_PATH.stat().st_size / 1024, 2) if DLL_PATH.exists() else None
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Build failed'),
                'output': result.get('output', '')
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'type': type(e).__name__
        }, status=500)


def check_build_needed() -> bool:
    """
    Determine if DLL needs rebuilding.

    Returns:
        bool: True if build is needed, False otherwise
    """
    if not DLL_PATH.exists():
        return True

    if not SOURCE_CS.exists():
        return False  # Can't build without source

    dll_mtime = DLL_PATH.stat().st_mtime
    source_mtime = SOURCE_CS.stat().st_mtime

    return source_mtime > dll_mtime


def run_build_script() -> dict:
    """
    Execute build_and_test.sh script.

    Returns:
        dict: {
            'success': bool,
            'output': str,
            'error': Optional[str]
        }
    """
    if not BUILD_SCRIPT.exists():
        return {
            'success': False,
            'error': f'Build script not found: {BUILD_SCRIPT}',
            'output': None
        }

    try:
        # Make script executable (in case permissions were lost)
        BUILD_SCRIPT.chmod(0o755)

        # Run build script
        result = subprocess.run(
            [str(BUILD_SCRIPT)],
            cwd=str(NINJA_BASE),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute max
        )

        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr or 'Build script returned non-zero exit code',
                'output': result.stdout
            }

        return {
            'success': True,
            'output': result.stdout,
            'error': None
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Build timeout (>120s). Check for errors.',
            'output': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'output': None
        }


def prepare_package_files() -> dict[Path, str]:
    """
    Prepare NT8 package file mappings.

    Returns dict mapping source paths to archive names (flat structure).

    Returns:
        dict: {source_path: archive_name} for ZIP creation
    """
    package_files = {}

    # Core files
    if DLL_PATH.exists():
        package_files[DLL_PATH] = 'FKS.dll'

    if SOURCE_CS.exists():
        package_files[SOURCE_CS] = 'FKS_AsyncStrategy.cs'

    # Metadata files
    manifest_xml = NINJA_BASE / 'src' / 'manifest.xml'
    if manifest_xml.exists():
        package_files[manifest_xml] = 'manifest.xml'

    info_xml = NINJA_BASE / 'src' / 'Info.xml'
    if info_xml.exists():
        package_files[info_xml] = 'Info.xml'

    # Create AdditionalReferences.txt in temp location
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write('FKS')
        additional_refs_path = Path(f.name)
    package_files[additional_refs_path] = 'AdditionalReferences.txt'

    # Generate README
    readme_path = generate_readme_file()
    package_files[readme_path] = 'README.txt'

    return package_files


def generate_readme_file() -> Path:
    """
    Generate installation README.txt in temp location.

    Returns:
        Path: Path to generated README.txt
    """
    readme_content = f"""
FKS NinjaTrader 8 Async Strategy - Installation Guide
=====================================================

PACKAGE CONTENTS:
- FKS.dll (compiled strategy assembly)
- FKS_AsyncStrategy.cs (source code)
- AdditionalReferences.txt (DLL registration)
- Info.xml (export metadata)
- manifest.xml (type registrations)

PREREQUISITES:
1. NinjaTrader 8 (version 8.0.26 or later)
2. .NET Framework 4.8
3. Windows 10/11 (64-bit)

INSTALLATION STEPS:

1. Close NinjaTrader 8 (IMPORTANT - must not be running)

2. Open NinjaTrader 8

3. Import Strategy:
   - Control Center → Tools → Import → NinjaScript Add-On
   - Browse to this ZIP file
   - Click "Import"
   - Accept security warnings (if prompted)

4. Verify Installation:
   - Control Center → Tools → NinjaScript Editor
   - Strategies folder should contain "FKS_AsyncStrategy"

5. Restart NinjaTrader 8 (recommended)

CONFIGURATION:

1. Create New Strategy Instance:
   - Control Center → New → Strategy
   - Template: FKS_AsyncStrategy
   - Instrument: ES 03-25 (or your preference)
   - Data Series: 1 Minute

2. Enable Strategy:
   - Click "Enabled" checkbox
   - Confirm you want to start strategy

3. Verify Socket Connection:
   - Tools → Output Window
   - Look for: "[HH:mm:ss] Async socket listener started on port 8080"
   - If not present, check TROUBLESHOOTING section

TESTING:

1. Test Connection (from Python client):
   - Run: ./signal_sender.py --test-connection
   - Expected: "✅ Connection test successful"

2. Send Test Signal:
   - Run: ./signal_sender.py --action buy --price 4500 --tp 20 --sl 10
   - Verify order appears in NT8

3. Check Output Window:
   - Should show: "[HH:mm:ss] Signal received: {{'action':'buy',...}}"
   - Followed by: "✓ LONG order: FKS_BUY_..."

TROUBLESHOOTING:

Issue: "Strategy does not appear after import"
Fix:
  - Close NT8
  - Delete: C:\\Users\\[USER]\\Documents\\NinjaTrader 8\\cache\\
  - Restart NT8
  - Re-import ZIP

Issue: "Socket listener failed to start"
Fix:
  - Check port 8080 not in use: netstat -ano | findstr :8080
  - Kill process or change port in strategy code
  - Recompile and re-import

Issue: "No signals received from FKS"
Fix:
  - Check Windows Firewall settings
  - Allow NinjaTrader.exe through firewall
  - Verify strategy is enabled on chart

SUPPORT:
- Documentation: https://docs.fks-trading.com/ninja
- Issues: https://github.com/nuniesmith/fks/issues
- Discord: https://discord.gg/fks-trading

Generated: {datetime.now():%Y-%m-%d %H:%M:%S UTC}
Package Version: 1.0.0
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(readme_content)
        return Path(f.name)


@login_required
@require_http_methods(["GET"])
def ninja_dashboard(request):
    """
    Render NT8 package management dashboard.

    Context:
    - build_status: Current DLL/source status
    - recent_builds: Build history (if implemented)

    Returns:
        HttpResponse: Rendered dashboard HTML
    """
    # Get current build status
    build_status_data = build_status(request)
    if isinstance(build_status_data, JsonResponse):
        status_dict = build_status_data.content.decode('utf-8')
        import json
        build_info = json.loads(status_dict)
    else:
        build_info = {'error': 'Could not fetch build status'}

    context = {
        'build_status': build_info,
        'ninja_base': str(NINJA_BASE),
        'build_script': str(BUILD_SCRIPT),
        'dll_path': str(DLL_PATH),
    }

    return render(request, 'ninja/dashboard.html', context)


@login_required
@require_http_methods(["GET"])
def installation_guide(request):
    """
    Display comprehensive installation guide as HTML.

    Returns:
        HttpResponse: Rendered installation guide
    """
    return render(request, 'ninja/installation_guide.html')
