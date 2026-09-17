"""
Authentication utilities (Phase 2+)
Currently placeholder for Phase 1
"""
from typing import Optional


class AuthUtils:
    """Authentication utilities for Firebase integration."""
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify Firebase ID token.
        Phase 1: Returns None (no auth)
        Phase 2+: Implement Firebase Admin SDK verification
        """
        # TODO: Implement Firebase token verification in Phase 2
        return None
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[str]:
        """Extract user ID from token."""
        # TODO: Implement in Phase 2
        return None
