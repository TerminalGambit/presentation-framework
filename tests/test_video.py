"""Tests for video embedding (MEDIA-04)."""
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
    # Preprocess video data before render
    for s in slides:
        if s.get("layout") == "video":
            b._preprocess_video(s)
        for block in s.get("data", {}).get("left", []) + s.get("data", {}).get("right", []):
            if isinstance(block, dict) and block.get("type") == "video":
                b._enrich_video_data(block)
    return [b.render_slide(s, i, features=features) for i, s in enumerate(slides)]


class TestVideoDetection:
    def test_youtube_url_detected(self):
        d = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        PresentationBuilder._enrich_video_data(d)
        assert d["_video_type"] == "youtube"
        assert d["_video_id"] == "dQw4w9WgXcQ"
        assert "hqdefault" in d["_thumbnail"]

    def test_youtu_be_short_url(self):
        d = {"url": "https://youtu.be/dQw4w9WgXcQ"}
        PresentationBuilder._enrich_video_data(d)
        assert d["_video_type"] == "youtube"
        assert d["_video_id"] == "dQw4w9WgXcQ"

    def test_vimeo_url_detected(self):
        d = {"url": "https://vimeo.com/123456789"}
        PresentationBuilder._enrich_video_data(d)
        assert d["_video_type"] == "vimeo"
        assert d["_video_id"] == "123456789"

    def test_mp4_url_detected(self):
        d = {"url": "https://example.com/video.mp4"}
        PresentationBuilder._enrich_video_data(d)
        assert d["_video_type"] == "mp4"


class TestVideoLayout:
    def test_youtube_thumbnail_in_output(self):
        htmls = _render([{"layout": "video", "data": {
            "title": "Demo",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }}])
        assert "hqdefault" in htmls[0] or "youtube" in htmls[0]

    def test_mp4_uses_video_element(self):
        htmls = _render([{"layout": "video", "data": {
            "title": "Demo",
            "url": "https://example.com/clip.mp4"
        }}])
        assert "<video" in htmls[0]

    def test_video_caption(self):
        htmls = _render([{"layout": "video", "data": {
            "title": "T",
            "url": "https://example.com/v.mp4",
            "caption": "My clip"
        }}])
        assert "My clip" in htmls[0]
