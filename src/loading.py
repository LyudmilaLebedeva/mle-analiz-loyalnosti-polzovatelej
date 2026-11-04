from __future__ import annotations

import warnings

warnings.filterwarnings(
    "ignore",
    message=".*urllib3 v2 only supports OpenSSL.*",
    category=Warning,
)

import requests

from pathlib import Path
from typing import Callable

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class DataLoader:
    def __init__(self) -> None:
        self._engines: dict[str, Engine] = {}

    def _get_engine(self, conn_str: str) -> Engine:
        if conn_str not in self._engines:
            self._engines[conn_str] = create_engine(conn_str)
        return self._engines[conn_str]

    @staticmethod
    def _logged_fetch(fetch: Callable[[], pd.DataFrame], label: str) -> Callable[[], pd.DataFrame]:
        """Оборачивает fetch, логируя МОМЕНТ вызова и объём результата."""
        def wrapper() -> pd.DataFrame:
            print(f"→ {label}")
            df = fetch()
            print(f"← Получен датафрейм {len(df)} строк × {len(df.columns)} колонок")
            return df
        return wrapper

    def _load_or_cache(
        self,
        csv_path: Path,
        fetch: Callable[[], pd.DataFrame],
        force: bool,
        label: str = "данные",
    ) -> pd.DataFrame:
        """Читает кэш, иначе вызывает fetch() и сохраняет результат."""
        path = Path(csv_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists() and not force:
            try:
                print(f"← Кэш: {path}")
                df = pd.read_csv(path)
                print(f"  {len(df)} строк × {len(df.columns)} колонок")
                return df
            except (pd.errors.ParserError, pd.errors.EmptyDataError, OSError) as e:
                print(f"⚠ Кэш повреждён ({e}), загружаем {label} заново")

        df = fetch()

        try:
            df.to_csv(path, index=False)
            print(f"→ Датафрейм сохранен в {path}")
        except OSError as e:
            print(f"⚠ Не удалось сохранить кэш: {e}")

        return df

    def load_data(
        self,
        connection_string: str,
        query: str,
        csv_path: str | Path,
        force: bool = False,
    ) -> pd.DataFrame:
        engine = self._get_engine(connection_string)
        return self._load_or_cache(
            csv_path=Path(csv_path),
            fetch=self._logged_fetch(
                lambda: pd.read_sql(query, engine),
                label="Загрузка данных из базы...",
            ),
            force=force,
            label="данные из базы",
        )

    def load_csv(
        self,
        url: str,
        csv_path: str | Path,
        force: bool = False,
        timeout: int = 30,
    ) -> pd.DataFrame:
        def _fetch() -> pd.DataFrame:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            from io import StringIO
            return pd.read_csv(StringIO(resp.text))

        return self._load_or_cache(
            csv_path=Path(csv_path),
            fetch=self._logged_fetch(_fetch, label=f"Загрузка данных по URL: {url[:60]}..."),
            force=force,
            label="данные по URL",
        )

    def close(self) -> None:
        for engine in self._engines.values():
            engine.dispose()
        self._engines.clear()
        print("Все соединения закрыты")

    def __enter__(self) -> "DataLoader":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()