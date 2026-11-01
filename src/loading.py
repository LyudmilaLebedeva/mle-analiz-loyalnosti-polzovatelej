from __future__ import annotations
from pathlib import Path
from typing import Callable

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class DataLoader:
    def __init__(self) -> None:
        self._engines: dict[str, Engine] = {}

    def _load_or_cache(
        self,
        csv_path: Path,
        fetch: Callable[[], pd.DataFrame],
        force: bool,
    ) -> pd.DataFrame:
        """Загружает данные через fetch, кэширует в CSV."""
        path = Path(csv_path)

        # Загружаем из локального хранилища
        if path.exists() and not force:
            try:
                print("Чтение данных из файла", path)
                df = pd.read_csv(path)
                print(f"Данные из файла успешно прочитаны ({len(df)} строк)")
                return df
            except (pd.errors.ParserError, pd.errors.EmptyDataError, OSError) as e:
                print("Не удалось прочитать данные из файла:", str(e))

        # Выгружаем из базы данных или скачиваем по url
        df = fetch()

        # Сохраняем результат в локальное хранилище
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(path, index=False)
            print(f"{len(df)} строк сохранено в {path}")
        except OSError as e:
            print("Не удалось сохранить данные в CSV:", e)

        return df

    def _get_engine(self, conn_str: str) -> Engine:
        if conn_str not in self._engines:
            self._engines[conn_str] = create_engine(conn_str)
        return self._engines[conn_str]

    def load_data(
        self,
        connection_string: str,
        query: str,
        csv_path: str | Path,
        force: bool = False,
    ) -> pd.DataFrame:
        engine = self._get_engine(connection_string)
        return self._load_or_cache(
            Path(csv_path),
            fetch=lambda: pd.read_sql(query, engine),
            force=force,
        )

    def load_csv(
        self,
        url: str,
        csv_path: str | Path,
        force: bool = False,
    ) -> pd.DataFrame:
        return self._load_or_cache(
            Path(csv_path),
            fetch=lambda: pd.read_csv(url),
            force=force,
        )

    def close(self) -> None:
        for engine in self._engines.values():
            engine.dispose()
        self._engines.clear()

    def __enter__(self) -> "DataLoader":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
