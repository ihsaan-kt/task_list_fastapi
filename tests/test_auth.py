import pytest
from datetime import datetime, timedelta
import jwt 
from unittest.mock import patch, MagicMock

from ..auth import (
    verify_password, get_user, authenticate_user,
    create_access_token, get_current_user,
    UserInDB, mock_users, pwd_context, 
    SECRET_KEY, ALGORITHM
)

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer


@pytest.fixture
def test_user_data():
    """
    Sample user data dictionary.
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "disabled": False,
        "hashed_password": pwd_context.hash("testpassword")
    }


@pytest.fixture
def mock_oauth2_scheme():
    """
    Mock OAuth2PasswordBearer.
    """
    mock = MagicMock(spec=OAuth2PasswordBearer)
    return mock


# Testing password functions
def test_verify_password_correct():
    hashed_pw = pwd_context.hash("mysecret")
    assert verify_password("mysecret", hashed_pw) is True


def test_verify_password_incorrect():
    hashed_pw = pwd_context.hash("mysecret")
    assert verify_password("wrongpassword", hashed_pw) is False


# Testing user models
def test_get_user_exists(test_user_data):
    original_user = mock_users.get(test_user_data["username"])
    mock_users[test_user_data["username"]] = test_user_data

    user = get_user(test_user_data["username"])
    assert user is not None
    assert user.username == test_user_data["username"]
    assert user.hashed_password == test_user_data["hashed_password"]


def test_get_user_does_not_exist():
    user = get_user("nonexistentuser")
    assert user is None


def test_authenticate_user_success(test_user_data):
    original_user = mock_users.get(test_user_data["username"])
    mock_users[test_user_data["username"]] = test_user_data

    user = authenticate_user(test_user_data["username"], "testpassword")
    assert user is not None
    assert user.username == test_user_data["username"]


def test_authenticate_user_wrong_password(test_user_data):
    original_user = mock_users.get(test_user_data["username"])
    mock_users[test_user_data["username"]] = test_user_data

    user = authenticate_user(test_user_data["username"], "wrongpassword")
    assert user is None


# Test JWT Token 
def test_create_access_token_default_expires():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    assert isinstance(token, str)
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_payload["sub"] == "testuser"
    assert decoded_payload["exp"] > (datetime.timezone.utc() + timedelta(minutes=14)).timestamp()
    assert decoded_payload["exp"] < (datetime.timezone.utc() + timedelta(minutes=16)).timestamp()


def test_create_access_token_custom_expires():
    """Tests creation of access token with custom expiration."""
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=5)
    token = create_access_token(data, expires_delta=expires_delta)
    assert isinstance(token, str)
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_payload["sub"] == "testuser"
    assert decoded_payload["exp"] > (datetime.timezone.utc() + timedelta(minutes=4)).timestamp()
    assert decoded_payload["exp"] < (datetime.timezone.utc() + timedelta(minutes=6)).timestamp()


@pytest.mark.asyncio
@patch('auth.get_user') # Patch get_user within the auth module
@patch('jwt.decode')    # Patch jwt.decode from PyJWT
async def test_get_current_user_success(mock_jwt_decode, mock_get_user):
    """Tests successful retrieval of current user."""
    mock_jwt_decode.return_value = {"sub": "john.doe"}
    mock_get_user.return_value = UserInDB(
        username="john.doe", hashed_password="hashed_pw", email="john@example.com"
    )
    mock_oauth2_scheme_instance = MagicMock()
    mock_oauth2_scheme_instance.return_value = "dummy_token" # Simulates token extraction

    user = await get_current_user(token="dummy_token")
    assert user.username == "john.doe"
    mock_jwt_decode.assert_called_once_with("dummy_token", SECRET_KEY, algorithms=[ALGORITHM])
    mock_get_user.assert_called_once_with("john.doe")


@pytest.mark.asyncio
@patch('auth.get_user')
@patch('jwt.decode')
async def test_get_current_user_invalid_token(mock_jwt_decode, mock_get_user):
    """Tests get_current_user with an invalid token (PyJWTError)."""
    mock_jwt_decode.side_effect = jwt.PyJWTError("Invalid token")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="invalid_token")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
@patch('auth.get_user')
@patch('jwt.decode')
async def test_get_current_user_no_username_in_token(mock_jwt_decode, mock_get_user):
    """Tests get_current_user when token payload lacks 'sub'."""
    mock_jwt_decode.return_value = {"some_other_claim": "value"}

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="token_without_sub")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail

