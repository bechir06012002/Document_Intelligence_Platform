import os


def get_api_base_url() -> str:
    value = os.environ.get("API_BASE_URL")
    if not value:
        raise RuntimeError(
            "API_BASE_URL environment variable is not set. Set it to the FastAPI "
            "backend's base URL, e.g. http://127.0.0.1:8000."
        )
    return value.rstrip("/")
