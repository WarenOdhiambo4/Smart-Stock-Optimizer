from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


def manifest(request):
    manifest_path = Path(settings.BASE_DIR) / "static" / "pwa" / "manifest.json"
    return HttpResponse(manifest_path.read_text(encoding="utf-8"), content_type="application/manifest+json")


def service_worker(request):
    sw_path = Path(settings.BASE_DIR) / "static" / "pwa" / "sw.js"
    response = HttpResponse(sw_path.read_text(encoding="utf-8"), content_type="application/javascript")
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
