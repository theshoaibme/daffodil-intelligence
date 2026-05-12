import sys
sys.path.insert(0, '/Users/ratulhasan/Desktop/Shoaib/daffodil-intelligence/apps/api')

from app.auth_engine import JWTManager
import time

jwt = JWTManager(secret="test-secret")

token = jwt.create_token("user123", "test@example.com", "email")
print(f"Token: {token}")
print(f"Parts: {token.split('.')}")

payload = jwt.verify_token(token)
print(f"Payload: {payload}")