from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from sqlalchemy.exc import SQLAlchemyError


class DataProcessor:
    def __init__(self):
        pass

    def load_data(
        self,
        db_connection_string: str,
        sql_query: str,
        csv_path: str,
        force: bool = False,
    ) -> pd.DataFrame:
        """Загружает данные из БД, сохраняя их в .csv, возвращает DataFrame.

        Если файл существует и не указан параметр `force`, читает данные из него.
        При первом запуске или при `force=True` выполняется SQL-запрос к БД.
        """
        path = Path(csv_path)

        # Валидация входных параметров
        if not db_connection_string or not sql_query:
            raise ValueError(
                "db_connection_string и sql_query должны быть заданы и не могут быть пустыми"
            )

        # Чтение из кэша
        if path.exists() and not force:
            try:
                print("Чтение данных из файла", path)
                df = pd.read_csv(path)
                print(f"Данные из файла успешно прочитаны ({len(df)} строк)")
                return df
            except (pd.errors.ParserError, pd.errors.EmptyDataError, OSError) as e:
                print("Не удалось прочитать данные из файла:", str(e))

        # Подключение к базе данных
        engine: Optional[Engine] = None
        try:
            print("Подключение к базе...")
            engine = create_engine(db_connection_string)
            print("Получение данных из базы...")
            df = pd.read_sql(sql_query, engine)
        except SQLAlchemyError as e:
            print("Ошибка выполнения запроса:", e)
            raise
        finally:
            if engine is not None:
                engine.dispose()

        print(f"Данные из базы успешно загружены: ({len(df)} строк)")

        if df.empty:
            print("Внимание: запрос вернул пустой результат")

        # Сохраняем результат в кэш
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(path, index=False)
            print(f"{len(df)} строк сохранено в {path}")
        except OSError as e:
            print("Не удалось сохранить данные в CSV:", e)

        return df
