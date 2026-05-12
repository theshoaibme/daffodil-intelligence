import sys
sys.path.insert(0, '/Users/ratulhasan/Desktop/Shoaib/daffodil-intelligence/apps/api')

from app.auth_engine import AuthenticationEngine, AuthProvider, SecureHasher, JWTManager


def test_password_hashing():
    print("\n" + "="*50)
    print("TEST 1: Password Hashing")
    print("="*50)
    
    password = "securePassword123"
    hashed = SecureHasher.hash_password(password)
    
    print(f"Original: {password}")
    print(f"Hashed: {hashed[:50]}...")
    
    assert hashed != password
    assert SecureHasher.verify_password(password, hashed)
    assert not SecureHasher.verify_password("wrong", hashed)
    print("✓ Password hashing works!")


def test_jwt_tokens():
    print("\n" + "="*50)
    print("TEST 2: JWT Token Generation")
    print("="*50)
    
    jwt = JWTManager(secret="test-secret")
    token = jwt.create_token("user123", "test@example.com", "email")
    
    print(f"Generated token: {token[:50]}...")
    
    payload = jwt.verify_token(token)
    print(f"Verified payload: {payload}")
    
    assert payload["user_id"] == "user123"
    assert payload["email"] == "test@example.com"
    assert payload["provider"] == "email"
    print("✓ JWT tokens work!")


def test_email_registration():
    print("\n" + "="*50)
    print("TEST 3: Email Registration")
    print("="*50)
    
    auth = AuthenticationEngine()
    
    result = auth.register_email(
        name="John Doe",
        email="john@example.com",
        password="password123",
        confirm_password="password123"
    )
    
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"User: {result.user}")
    
    assert result.status == "success"
    assert result.access_token is not None
    assert result.user["email"] == "john@example.com"
    print("✓ Email registration works!")


def test_duplicate_email():
    print("\n" + "="*50)
    print("TEST 4: Duplicate Email Prevention")
    print("="*50)
    
    auth = AuthenticationEngine()
    
    auth.register_email("User One", "duplicate@test.com", "password123", "password123")
    
    result = auth.register_email("User Two", "duplicate@test.com", "password456", "password456")
    
    print(f"Second registration: {result.status} - {result.message}")
    
    assert result.status == "error"
    assert "already registered" in result.message
    print("✓ Duplicate email prevention works!")


def test_password_mismatch():
    print("\n" + "="*50)
    print("TEST 5: Password Mismatch")
    print("="*50)
    
    auth = AuthenticationEngine()
    
    result = auth.register_email(
        "Test User", "test@test.com", "password1", "password2"
    )
    
    print(f"Status: {result.status} - {result.message}")
    
    assert result.status == "error"
    assert "do not match" in result.message
    print("✓ Password mismatch detection works!")


def test_email_login():
    print("\n" + "="*50)
    print("TEST 6: Email Login")
    print("="*50)
    
    auth = AuthenticationEngine()
    
    auth.register_email("Login User", "login@test.com", "mypassword", "mypassword")
    
    result = auth.login_email("login@test.com", "mypassword")
    
    print(f"Login status: {result.status}")
    print(f"User: {result.user}")
    
    assert result.status == "success"
    assert result.access_token is not None
    print("✓ Email login works!")


def test_invalid_credentials():
    print("\n" + "="*50)
    print("TEST 7: Invalid Credentials")
    print("="*50)
    
    auth = AuthenticationEngine()
    
    auth.register_email("Test", "wrong@test.com", "correctpass", "correctpass")
    
    result = auth.login_email("wrong@test.com", "wrongpassword")
    
    print(f"Status: {result.status} - {result.message}")
    
    assert result.status == "error"
    assert "Invalid" in result.message
    print("✓ Invalid credential detection works!")


def test_google_login():
    print("\n" + "="*50)
    print("TEST 8: Google OAuth Login")
    print("="*50)
    
    auth = AuthenticationEngine()
    
    result = auth.login_google(
        google_token="fake_google_token",
        user_info={"email": "google@test.com", "name": "Google User"}
    )
    
    print(f"Google login status: {result.status}")
    print(f"User: {result.user}")
    
    assert result.status == "success"
    assert result.user["auth_provider"] == "google"
    assert result.user["email"] == "google@test.com"
    print("✓ Google OAuth works!")


def test_google_login_existing_user():
    print("\n" + "="*50)
    print("TEST 9: Google Login Existing User")
    print("="*50)
    
    auth = AuthenticationEngine()
    
    auth.register_email("Existing", "existing@test.com", "password", "password")
    
    result = auth.login_google(
        "token",
        {"email": "existing@test.com", "name": "Should Fail"}
    )
    
    print(f"Status: {result.status} - {result.message}")
    
    assert result.status == "error"
    assert "email/password" in result.message
    print("✓ Existing user Google prevention works!")


def test_token_verification():
    print("\n" + "="*50)
    print("TEST 10: Token Verification")
    print("="*50)
    
    auth = AuthenticationEngine()
    
    reg_result = auth.register_email("Token Test", "token@test.com", "password123", "password123")
    token = reg_result.access_token
    
    payload = auth.verify_token(token)
    
    print(f"Token payload: {payload}")
    
    assert payload is not None
    assert payload["email"] == "token@test.com"
    
    invalid = auth.verify_token("invalid|token|here")
    assert invalid is None
    print("✓ Token verification works!")


def main():
    print("\n" + "="*60)
    print("DAFFODIL INTELLIGENCE - AUTH ENGINE TEST SUITE")
    print("="*60)
    
    test_password_hashing()
    test_jwt_tokens()
    test_email_registration()
    test_duplicate_email()
    test_password_mismatch()
    test_email_login()
    test_invalid_credentials()
    test_google_login()
    test_google_login_existing_user()
    test_token_verification()
    
    print("\n" + "="*60)
    print("ALL AUTH TESTS PASSED! ✅")
    print("="*60)


if __name__ == "__main__":
    main()