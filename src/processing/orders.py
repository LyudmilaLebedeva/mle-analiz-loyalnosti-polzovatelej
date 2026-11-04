from __future__ import annotations

import pandas as pd

from src.processing.base import BaseProcessor
from src.processing.constants import DB_COLUMNS, COMPUTED_COLUMNS


class OrderProcessor(BaseProcessor):
    """Обработка raw-данных заказов."""

    def __init__(self, df: pd.DataFrame) -> None:
        super().__init__(df)

    def optimize_dtypes(
        self, columns: dict | None = None
    ) -> "OrderProcessor":
        merged = {**DB_COLUMNS, **COMPUTED_COLUMNS, **(columns or {})}
        super().optimize_dtypes(merged)
        return self

    def convert_tenge_to_rubles(
        self, rate_df: pd.DataFrame
    ) -> "OrderProcessor":
        print("\nКонвертация выручки из тенге в рубли...")
        
        tenge_curs = rate_df.set_index("data")["curs"]
        tenge_curs.index = pd.to_datetime(tenge_curs.index).normalize()

        is_kzt = self.df["currency_code"] == "kzt"
        order_dt = pd.to_datetime(self.df.loc[is_kzt, "created_dt_msk"]).dt.normalize()
        rate = order_dt.map(tenge_curs)

        self.df["revenue_rub"] = self.df.loc[~is_kzt, "revenue"]

        self.df.loc[is_kzt, "revenue_rub"] = (
            self.df.loc[is_kzt, "revenue"] * rate / 100
        ).round(2)

        print("Создан столбец 'revenue_rub'")

        missing_count = self.df["revenue_rub"].isna().sum() 

        if missing_count == 0:
            print('Нет пропущенных значений')
        else:
            print('Пропущенных значений:', missing_count)

        print("Конвертация завершена")
        return self
