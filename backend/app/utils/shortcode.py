import secrets
import string

ALPHABET = string.ascii_letters + string.digits
# drop characters that are easy to confuse when someone types a link by hand
ALPHABET = "".join(c for c in ALPHABET if c not in "0O1lI")


def random_code(length=7):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def unique_code(exists, length=7, attempts=8):
    """Keep trying random codes until `exists(code)` says it's free."""
    for i in range(attempts):
        # grow the code a little if we keep colliding
        code = random_code(length + i // 3)
        if not exists(code):
            return code
    raise RuntimeError("Could not generate a unique short code")
