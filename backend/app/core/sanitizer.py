import unicodedata
import re
from typing import Tuple


class TextSanitizer:
    """
    Deterministic Inbound Text Sanitizer.
    Enforces Unicode NFKC normalization and removes zero-width/control characters.
    """
    
    # Regex pattern to match zero-width spaces, joiners, and non-printable control chars (excluding normal space, tab, newline)
    ZERO_WIDTH_AND_CONTROL_RE = re.compile(
        r'[\u200B-\u200D\uFEFF\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]'
    )

    @classmethod
    def sanitize(cls, text: str) -> Tuple[str, bool]:
        """
        Sanitizes text prompt.
        Returns: (sanitized_text, modified_flag)
        """
        if not text:
            return "", False
            
        # 1. Unicode NFKC Normalization (resolves homoglyphs & composite character trickery)
        normalized = unicodedata.normalize("NFKC", text)
        
        # 2. Strip zero-width & non-printable control characters
        cleaned, num_subs = cls.ZERO_WIDTH_AND_CONTROL_RE.subn("", normalized)
        
        modified = (cleaned != text)
        return cleaned, modified
