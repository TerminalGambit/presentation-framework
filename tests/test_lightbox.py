"""Tests for the image lightbox in present.html."""

import json
import struct
import zlib
import tempfile
from pathlib import Path

import pytest
import yaml

from pf.builder import PresentationBuilder


def _minimal_png():
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    raw = zlib.compress(b'\x00\x00\x00\x00')
    idat_crc = zlib.crc32(b'IDAT' + raw) & 0xffffffff
    idat = struct.pack('>I', len(raw)) + b'IDAT' + raw + struct.pack('>I', idat_crc)
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    return sig + ihdr + idat + iend


def _build_with_image(tmp_path: Path) -> str:
    """Build a presentation with an image slide and return present.html content."""
    img_path = tmp_path / "test.png"
    img_path.write_bytes(_minimal_png())

    config = {
        "meta": {"title": "Test", "authors": ["Tester"]},
        "theme": {
            "primary": "#1C2537", "accent": "#C4A962",
            "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
        },
        "slides": [
            {"layout": "image", "data": {"title": "Photo", "image": str(img_path), "position": "split"}},
            {"layout": "closing", "data": {"title": "End"}},
        ],
    }
    config_path = tmp_path / "presentation.yaml"
    config_path.write_text(yaml.dump(config, sort_keys=False), encoding="utf-8")
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({"metadata": {}, "summary": {}}), encoding="utf-8")

    builder = PresentationBuilder(config_path=str(config_path), metrics_path=str(metrics_path))
    out = builder.build(output_dir=str(tmp_path / "slides"))
    return (out / "present.html").read_text(encoding="utf-8")


class TestLightboxMarkup:
    def test_lightbox_overlay_exists(self, tmp_path):
        html = _build_with_image(tmp_path)
        assert 'id="lightboxOverlay"' in html

    def test_lightbox_css_exists(self, tmp_path):
        html = _build_with_image(tmp_path)
        assert ".lightbox-overlay" in html

    def test_lightbox_js_functions_exist(self, tmp_path):
        html = _build_with_image(tmp_path)
        assert "openLightbox" in html
        assert "closeLightbox" in html

    def test_lightbox_keyboard_escape(self, tmp_path):
        html = _build_with_image(tmp_path)
        assert "lightboxActive" in html
