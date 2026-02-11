from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


def manifest(request):
    manifest_path = Path(settings.BASE_DIR) / "static" / "pwa" / "manifest.json"
    return HttpResponse(manifest_path.read_text(encoding="utf-8"), content_type="application/manifest+json")


def service_worker(request):
    sw_path = Path(settings.BASE_DIR) / "static" / "pwa" / "sw.js"
    return HttpResponse(sw_path.read_text(encoding="utf-8"), content_type="application/javascript")
