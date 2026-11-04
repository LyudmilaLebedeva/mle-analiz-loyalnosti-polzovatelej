from __future__ import annotations

import pandas as pd

from src.processing import BaseProcessor


class ProfileProcessor(BaseProcessor):
    """Создание профилей пользователей."""

    def __init__(self, purchases_df: pd.DataFrame) -> None:
        super().__init__(purchases_df)
        self.df = self._build_profiles(purchases_df)

    @staticmethod
    def _build_profiles(purchases_df: pd.DataFrame) -> pd.DataFrame:
        profile = purchases_df.groupby("user_id").agg(
            first_order_date=("created_ts_msk", "min"),
            last_order_date=("created_ts_msk", "max"),
            total_orders=("order_id", "count"),
            avg_revenue_rub=("revenue_rub", "mean"),
            avg_days_between_orders=("days_since_prev", "mean"),
        ).reset_index()

        profile["total_orders"] = pd.to_numeric(profile["total_orders"], errors="coerce")

        first_orders = (
            purchases_df.sort_values(by=["user_id", "created_ts_msk"])
            .drop_duplicates(subset=["user_id"], keep="first")[
                ["user_id", "device_type_canonical", "region_name", "event_type_main"]
            ]
        )

        profile = profile.merge(first_orders, on="user_id", how="left")
        profile['is_two'] = (profile['total_orders'] > 1)

        profile['first_order_weekday_number'] = profile['first_order_date'].dt.weekday


        print(f"\nСозданы профили {len(profile)} пользователей")

        return profile
