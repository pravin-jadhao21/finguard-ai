import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.sanitizer import TextSanitizer


def test_unicode_nfkc_normalization():
    # Test normalization of compatibility characters (Fraktur math symbols)
    input_text = "ℌ𝔢𝔩𝔩𝔬 World"
    sanitized, modified = TextSanitizer.sanitize(input_text)
    assert sanitized == "Hello World"
    assert modified is True



def test_zero_width_space_stripping():
    # Input with invisible zero-width spaces (\u200B)
    input_text = "Hello\u200BWorld\uFEFFTest"
    sanitized, modified = TextSanitizer.sanitize(input_text)
    assert sanitized == "HelloWorldTest"
    assert modified is True


def test_clean_text_remains_unchanged():
    input_text = "Check my account balance please."
    sanitized, modified = TextSanitizer.sanitize(input_text)
    assert sanitized == input_text
    assert modified is False
