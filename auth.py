import hmac
import hashlib
import json
import time
from urllib.parse import parse_qs, unquote
from fastapi import HTTPException


def validate_init_data(init_data_raw: str, bot_token: str) -> dict:
    parsed = parse_qs(init_data_raw)

    received_hash = parsed.get("hash", [None])[0]
    if not received_hash:
        raise HTTPException(400, "Missing hash")

    data = {k: v[0] for k, v in parsed.items() if k != "hash"}

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(403, "Invalid Telegram initData")

    auth_date = int(data.get("auth_date", 0))

    if time.time() - auth_date > 86400:
        raise HTTPException(403, "initData expired")

    user = json.loads(unquote(data.get("user", "{}")))

    return user