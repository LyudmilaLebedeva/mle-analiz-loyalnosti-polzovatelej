from enum import Enum

import pandas as pd


class ColumnType(Enum):
    INT = "int"
    FLOAT = "float"
    CATEGORY = "category"
    DATETIME = "datetime"
    OBJECT = "object"


DB_COLUMNS: dict[str, ColumnType] = {
    "user_id": ColumnType.OBJECT,
    "order_id": ColumnType.INT,
    "event_id": ColumnType.INT,
    "tickets_count": ColumnType.INT,
    "created_dt_msk": ColumnType.DATETIME,
    "created_ts_msk": ColumnType.DATETIME,
    "currency_code": ColumnType.CATEGORY,
    "revenue": ColumnType.FLOAT,
    "device_type_canonical": ColumnType.CATEGORY,
    "event_type_main": ColumnType.CATEGORY,
    "service_name": ColumnType.CATEGORY,
    "region_name": ColumnType.CATEGORY,
    "days_since_prev": ColumnType.FLOAT,
}

COMPUTED_COLUMNS: dict[str, ColumnType] = {
    "revenue_rub": ColumnType.FLOAT,
}

CATEGORY_THRESHOLD = 0.5


class DataProcessor:
    def __init__(self) -> None:
        self.df: pd.DataFrame | None = None
        self.rate_df: pd.DataFrame | None = None

    def set_data(self, df: pd.DataFrame, rate_df: pd.DataFrame) -> "DataProcessor":
        self.df = df
        self.rate_df = rate_df
        print(f"Данные загружены: {len(df)} строк, {len(df.columns)} столбцов")
        return self

    def validate(self) -> "DataProcessor":
        missing = set(DB_COLUMNS) - set(self.df.columns)
        if missing:
            raise ValueError(f"Отсутствуют столбцы: {missing}")
        return self

    def convert_tenge_to_rubles(self) -> "DataProcessor":
        kzt_count = (self.df["currency_code"] == "kzt").sum()
        print(f"Конвертация: {kzt_count} транзакций в KZT")

        tenge_curs = self.rate_df.set_index("data")["curs"]
        tenge_curs.index = pd.to_datetime(tenge_curs.index).normalize()

        is_kzt = self.df["currency_code"] == "kzt"
        order_dt = pd.to_datetime(self.df.loc[is_kzt, "created_dt_msk"]).dt.normalize()
        rate = order_dt.map(tenge_curs)

        self.df["revenue_rub"] = self.df["revenue"].copy()
        self.df.loc[is_kzt, "revenue_rub"] = (
            self.df.loc[is_kzt, "revenue"] * rate / 100
        ).round(2)

        print("Конвертация завершена")
        return self

    def optimize_dtypes(self) -> "DataProcessor":
        before = self.df.memory_usage(deep=True).sum() / 1024**2
        print(f"До оптимизации: {before:.1f} МБ")

        for columns in (DB_COLUMNS, COMPUTED_COLUMNS):
            for col, col_type in columns.items():
                if col not in self.df.columns:
                    continue

                if col_type == ColumnType.INT:
                    self.df[col] = pd.to_numeric(self.df[col], downcast="integer")
                elif col_type == ColumnType.FLOAT:
                    self.df[col] = pd.to_numeric(self.df[col], downcast="float")
                elif col_type == ColumnType.CATEGORY:
                    if self.df[col].nunique() < len(self.df) * CATEGORY_THRESHOLD:
                        self.df[col] = self.df[col].astype("category")
                elif col_type == ColumnType.DATETIME:
                    if not pd.api.types.is_datetime64_any_dtype(self.df[col]):
                        self.df[col] = pd.to_datetime(self.df[col])

        after = self.df.memory_usage(deep=True).sum() / 1024**2
        print(f"После оптимизации: {after:.1f} МБ (экономия {before - after:.1f} МБ)")
        return self
