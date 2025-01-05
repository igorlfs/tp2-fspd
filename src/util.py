MIN_PORT = 2048
MAX_PORT = 65535


def is_valid_port(port: int) -> None:
    assert port >= MIN_PORT and port <= MAX_PORT, f"Port must be between {MIN_PORT} and {MAX_PORT}"
