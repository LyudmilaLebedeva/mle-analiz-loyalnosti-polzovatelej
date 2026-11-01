import pandas as pd

class DataProcessor:
    def convert_tenge_to_rubles(self, df: pd.DataFrame, rate_df: pd.DataFrame) -> pd.Series:
        """Возвращает Series с выручкой в рублях."""
        tenge_curs = rate_df.set_index("data")["curs"]
        tenge_curs.index = pd.to_datetime(tenge_curs.index)

        is_kzt = df["currency_code"] == "kzt"
        rate = df.loc[is_kzt, "created_dt_msk"].map(tenge_curs)

        revenue_rub = df["revenue"].copy()
        revenue_rub.loc[is_kzt] = (df.loc[is_kzt, "revenue"] * rate / 100).round(2)

        return revenue_rub
