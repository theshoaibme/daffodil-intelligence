import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.auth_engine import JWTManager
import time

jwt = JWTManager(secret="test-secret")

token = jwt.create_token("user123", "test@example.com", "email")
print(f"Token: {token}")
print(f"Parts: {token.split('.')}")

payload = jwt.verify_token(token)
print(f"Payload: {payload}")