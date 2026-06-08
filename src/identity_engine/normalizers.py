"""Data normalization utilities"""

import re
import unicodedata
from typing import Optional, Dict, Any
import phonetics


class TextNormalizer:
    """Normalize text data for identity matching
    
    Handles:
    - Case normalization
    - Diacritical mark removal
    - Whitespace standardization
    - Special character handling
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize normalizer
        
        Args:
            config: Configuration with normalization options
        """
        self.case_sensitive = config.get("case_sensitive", False)
        self.remove_diacritics = config.get("remove_diacritics", True)
        self.standardize_spacing = config.get("standardize_spacing", True)
        self.remove_punctuation = config.get("remove_punctuation", False)
    
    def normalize(self, text: Optional[str]) -> Optional[str]:
        """Normalize text string
        
        Args:
            text: Input text
        
        Returns:
            Normalized text or None
        """
        if text is None:
            return None
        
        text = str(text).strip()
        
        # Case normalization
        if not self.case_sensitive:
            text = text.lower()
        
        # Diacritical mark removal
        if self.remove_diacritics:
            text = self._remove_diacritics(text)
        
        # Whitespace standardization
        if self.standardize_spacing:
            text = " ".join(text.split())
        
        # Punctuation removal
        if self.remove_punctuation:
            text = re.sub(r"[^\w\s]", "", text)
        
        return text
    
    def normalize_email(self, email: Optional[str]) -> Optional[str]:
        """Normalize email address
        
        Args:
            email: Input email
        
        Returns:
            Normalized email or None
        """
        if email is None:
            return None
        
        email = str(email).strip().lower()
        
        # Extract local part and domain
        if "@" in email:
            local, domain = email.rsplit("@", 1)
            # Normalize local part (remove dots, underscores)
            local = local.replace(".", "").replace("_", "")
            email = f"{local}@{domain}"
        
        return email
    
    def normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Normalize phone number
        
        Args:
            phone: Input phone number
        
        Returns:
            Normalized phone or None
        """
        if phone is None:
            return None
        
        # Remove all non-digit characters except +
        phone = re.sub(r"[^\d+]", "", str(phone))
        
        # Pad country code if missing (assume US)
        if not phone.startswith("+"):
            if len(phone) == 10:
                phone = "+1" + phone
            elif len(phone) == 11 and phone[0] == "1":
                phone = "+" + phone
        
        return phone
    
    def _remove_diacritics(self, text: str) -> str:
        """Remove diacritical marks from text
        
        Args:
            text: Input text
        
        Returns:
            Text without diacritical marks
        """
        # Decompose and filter out diacriticals
        nfd = unicodedata.normalize("NFD", text)
        return "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    
    def get_phonetic_variation(self, text: Optional[str]) -> Optional[str]:
        """Get phonetic variation of text
        
        Uses Metaphone for English words
        
        Args:
            text: Input text
        
        Returns:
            Phonetic representation or None
        """
        if text is None:
            return None
        
        text = self.normalize(text)
        if not text:
            return None
        
        try:
            # Get Metaphone encoding
            return phonetics.metaphone(text)
        except Exception:
            # Fallback to Soundex if Metaphone fails
            return phonetics.soundex(text)


def extract_initials(text: Optional[str]) -> Optional[str]:
    """Extract initials from text
    
    Args:
        text: Input text (e.g., "John Smith")
    
    Returns:
        Initials (e.g., "JS")
    """
    if not text:
        return None
    
    words = text.split()
    return "".join(w[0].upper() for w in words if w)


def get_first_last_name(full_name: Optional[str]) -> tuple:
    """Extract first and last name from full name
    
    Args:
        full_name: Full name
    
    Returns:
        Tuple of (first_name, last_name)
    """
    if not full_name:
        return None, None
    
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        # Assume last word is surname
        return " ".join(parts[:-1]), parts[-1]
