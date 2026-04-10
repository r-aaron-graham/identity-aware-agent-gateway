from app.auth import mint_token, verify_token


def test_token_round_trip():
    token = mint_token("u1", "Test User", "analyst")
    payload = verify_token(token)
    assert payload["sub"] == "u1"
    assert payload["name"] == "Test User"
    assert payload["role"] == "analyst"
