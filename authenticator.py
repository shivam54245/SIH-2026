

import bcrypt

def hash_password(password: str) -> str:
    """Takes a raw password and returns a secure, encrypted hash string."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if a user-entered password matches the saved hash in the database."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )