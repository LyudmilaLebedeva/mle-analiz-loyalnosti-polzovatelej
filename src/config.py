import os
from dotenv import load_dotenv


def get_db_connection_string() -> str:
    """Собирает строку подключения к PostgreSQL из переменных окружения."""
    load_dotenv()

    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PWD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    if not all([user, pwd, host, port, name]):
        missing = [k for k, v in [
            ("DB_USER", user), ("DB_PWD", pwd), ("DB_HOST", host),
            ("DB_PORT", port), ("DB_NAME", name)
        ] if not v]
        raise ValueError(f"Не заданы переменные окружения: {', '.join(missing)}")

    return f'postgresql://{user}:{pwd}@{host}:{port}/{name}'
