import jwt
import requests

SUPABASE_PROJECT_URL = "https://<your-project>.supabase.co"
JWKS_URL = f"{SUPABASE_PROJECT_URL}/auth/v1/jwks"

jwks = requests.get(JWKS_URL).json()

def verify_jwt(token):
    try:
        header = jwt.get_unverified_header(token)
        key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="authenticated"
        )
        return decoded
    except Exception as e:
        print("JWT verification failed:", e)
        return None
