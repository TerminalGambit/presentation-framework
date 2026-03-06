"""Tests for map embedding (MEDIA-05)."""
import pytest
from pf.builder import PresentationBuilder

THEME = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
}


def _render(slides):
    b = PresentationBuilder()
    b.config = {"meta": {"title": "T"}, "theme": THEME, "slides": slides}
    b.metrics = {}
    features = b._scan_features(slides)
    return [b.render_slide(s, i, features=features) for i, s in enumerate(slides)]


class TestMapLayout:
    def test_renders_leaflet_init(self):
        htmls = _render([{"layout": "map", "data": {
            "title": "HQ", "lat": 37.7749, "lng": -122.4194, "zoom": 12
        }}])
        assert "L.map" in htmls[0]

    def test_renders_lat_lng(self):
        htmls = _render([{"layout": "map", "data": {
            "title": "HQ", "lat": 37.7749, "lng": -122.4194
        }}])
        assert "37.7749" in htmls[0]
        assert "-122.4194" in htmls[0]

    def test_renders_markers(self):
        slides = [{"layout": "map", "data": {
            "title": "Offices", "lat": 37.77, "lng": -122.42, "zoom": 12,
            "markers": [{"lat": 37.77, "lng": -122.42, "label": "HQ"}]
        }}]
        htmls = _render(slides)
        assert "L.marker" in htmls[0]
        assert "HQ" in htmls[0]

    def test_leaflet_cdn_injected(self):
        htmls = _render([{"layout": "map", "data": {
            "title": "T", "lat": 0, "lng": 0
        }}])
        assert "leaflet" in htmls[0].lower()

    def test_no_leaflet_cdn_without_map(self):
        htmls = _render([{"layout": "section", "data": {"title": "Hello"}}])
        assert "leaflet" not in htmls[0].lower()

    def test_data_pf_ready_sentinel(self):
        htmls = _render([{"layout": "map", "data": {
            "title": "T", "lat": 0, "lng": 0
        }}])
        assert "data-pf-ready" in htmls[0]

    def test_openstreetmap_tiles(self):
        htmls = _render([{"layout": "map", "data": {
            "title": "T", "lat": 0, "lng": 0
        }}])
        assert "openstreetmap" in htmls[0].lower() or "tile.openstreetmap.org" in htmls[0]


class TestMapBlock:
    def test_map_block_in_two_column(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "map", "lat": 40.71, "lng": -74.0, "zoom": 10}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "L.map" in htmls[0] or "pf-map" in htmls[0]
