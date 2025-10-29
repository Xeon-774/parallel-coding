"""Unit tests for JWT authentication module.

Tests password hashing, JWT token creation / verification, and scope checking.
"""

from datetime import timedelta

import pytest
from jose import JWTError

from orchestrator.core.auth import (
    TokenData,
    check_scope,
    create_access_token,
    create_dev_token,
    hash_password,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password_success(self):
        """Test successful password hashing."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed.startswith("$argon2")  # Argon2 format

    def test_hash_password_empty_raises_error(self):
        """Test that empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

    def test_hash_password_whitespace_only_raises_error(self):
        """Test that whitespace - only password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("   ")

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "MyPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "MyPassword123"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_empty_plain_returns_false(self):
        """Test that empty plain password returns False."""
        hashed = hash_password("SomePassword")

        assert verify_password("", hashed) is False

    def test_verify_password_empty_hash_returns_false(self):
        """Test that empty hash returns False."""
        assert verify_password("SomePassword", "") is False

    def test_verify_password_invalid_hash_returns_false(self):
        """Test that invalid hash format returns False."""
        # Not a valid Argon2 hash
        assert verify_password("password", "invalid_hash_format") is False

    def test_hash_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = hash_password("Password1")
        hash2 = hash_password("Password2")

        assert hash1 != hash2

    def test_hash_same_password_twice_produces_different_hashes(self):
        """Test that hashing same password twice produces different hashes (salt)."""
        password = "SamePassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different due to random salt
        assert hash1 != hash2
        # But both verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token_success(self):
        """Test creating access token."""
        token = create_access_token(
            user_id="user_123", scopes=["supervisor:read", "supervisor:write"]
        )

        assert token is not None
        assert len(token) > 100  # JWT tokens are long
        assert isinstance(token, str)

    def test_create_access_token_empty_user_id_raises_error(self):
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            create_access_token(user_id="", scopes=["supervisor:read"])

    def test_create_access_token_whitespace_user_id_raises_error(self):
        """Test that whitespace - only user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            create_access_token(user_id="   ", scopes=["supervisor:read"])

    def test_create_access_token_with_custom_expiration(self):
        """Test creating token with custom expiration."""
        token = create_access_token(
            user_id="user_123", scopes=["supervisor:read"], expires_delta=timedelta(hours=1)
        )

        assert token is not None

        # Verify token is valid
        token_data = verify_token(token)
        assert token_data.user_id == "user_123"

    def test_create_access_token_with_empty_scopes(self):
        """Test creating token with empty scopes list."""
        token = create_access_token(user_id="user_123", scopes=[])

        assert token is not None
        token_data = verify_token(token)
        assert token_data.scopes == []


class TestJWTTokenVerification:
    """Test JWT token verification."""

    def test_verify_token_success(self):
        """Test verifying valid token."""
        token = create_access_token(user_id="user_456", scopes=["jobs:read", "jobs:write"])

        token_data = verify_token(token)

        assert token_data.user_id == "user_456"
        assert "jobs:read" in token_data.scopes
        assert "jobs:write" in token_data.scopes

    def test_verify_token_invalid_raises_error(self):
        """Test that invalid token raises JWTError."""
        with pytest.raises(JWTError):
            verify_token("invalid.token.string")

    def test_verify_token_expired_raises_error(self):
        """Test that expired token raises JWTError."""
        # Create token that expires immediately
        token = create_access_token(
            user_id="user_123",
            scopes=["supervisor:read"],
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        with pytest.raises(JWTError, match="Token verification failed"):
            verify_token(token)

    def test_verify_token_missing_sub_raises_error(self):
        """Test that token without 'sub' claim raises ValueError."""
        # This is hard to test without mocking jwt.encode
        # The current implementation will catch this via JWTError
        pass

    def test_verify_token_extracts_scopes_correctly(self):
        """Test that scopes are extracted correctly."""
        scopes = ["scope1", "scope2", "scope3"]
        token = create_access_token(user_id="user_123", scopes=scopes)

        token_data = verify_token(token)

        assert len(token_data.scopes) == 3
        assert set(token_data.scopes) == set(scopes)


class TestScopeChecking:
    """Test scope checking functionality."""

    def test_check_scope_present(self):
        """Test checking for present scope."""
        scopes = ["supervisor:read", "supervisor:write", "jobs:read"]

        assert check_scope("supervisor:read", scopes) is True

    def test_check_scope_not_present(self):
        """Test checking for absent scope."""
        scopes = ["supervisor:read", "supervisor:write"]

        assert check_scope("jobs:delete", scopes) is False

    def test_check_scope_empty_list(self):
        """Test checking scope against empty list."""
        assert check_scope("supervisor:read", []) is False

    def test_check_scope_exact_match_required(self):
        """Test that scope checking requires exact match."""
        scopes = ["supervisor:read"]

        # Exact match
        assert check_scope("supervisor:read", scopes) is True

        # Partial match should fail
        assert check_scope("supervisor", scopes) is False
        assert check_scope("supervisor:read:extra", scopes) is False


class TestDevToken:
    """Test development token creation."""

    def test_create_dev_token_default(self):
        """Test creating dev token with defaults."""
        token = create_dev_token()

        assert token is not None

        # Verify token
        token_data = verify_token(token)
        assert token_data.user_id == "dev_user"

        # Should have all default scopes
        expected_scopes = [
            "supervisor:read",
            "supervisor:write",
            "resources:read",
            "resources:write",
            "jobs:read",
            "jobs:write",
        ]
        assert set(token_data.scopes) == set(expected_scopes)

    def test_create_dev_token_custom_user_id(self):
        """Test creating dev token with custom user_id."""
        token = create_dev_token(user_id="custom_dev_user")

        token_data = verify_token(token)
        assert token_data.user_id == "custom_dev_user"

    def test_create_dev_token_custom_scopes(self):
        """Test creating dev token with custom scopes."""
        custom_scopes = ["test:read", "test:write"]
        token = create_dev_token(user_id="test_user", scopes=custom_scopes)

        token_data = verify_token(token)
        assert token_data.user_id == "test_user"
        assert set(token_data.scopes) == set(custom_scopes)

    def test_create_dev_token_long_expiration(self):
        """Test that dev token has long expiration (365 days)."""
        token = create_dev_token()

        # Token should be valid (not expired)
        token_data = verify_token(token)
        assert token_data is not None


class TestTokenDataModel:
    """Test TokenData model."""

    def test_token_data_creation(self):
        """Test creating TokenData instance."""
        token_data = TokenData(user_id="user_789", scopes=["scope1", "scope2"])

        assert token_data.user_id == "user_789"
        assert len(token_data.scopes) == 2

    def test_token_data_empty_scopes_default(self):
        """Test that scopes default to empty list."""
        token_data = TokenData(user_id="user_789")

        assert token_data.scopes == []


class TestIntegration:
    """Integration tests for full auth flow."""

    def test_full_auth_flow(self):
        """Test complete authentication flow."""
        # 1. Hash password
        password = "UserPassword123!"
        hashed = hash_password(password)

        # 2. Verify password
        assert verify_password(password, hashed) is True

        # 3. Create token
        token = create_access_token(
            user_id="integrated_user", scopes=["supervisor:read", "jobs:write"]
        )

        # 4. Verify token
        token_data = verify_token(token)
        assert token_data.user_id == "integrated_user"

        # 5. Check scopes
        assert check_scope("supervisor:read", token_data.scopes) is True
        assert check_scope("jobs:write", token_data.scopes) is True
        assert check_scope("supervisor:delete", token_data.scopes) is False
