import sys

from scipy import stats
from dotenv import load_dotenv

from src.loading import DataLoader
from src.processing import OrderProcessor
from src.processing.profiles import ProfileProcessor
from src.queries import PURCHASES_QUERY
from src.config import get_db_connection_string, TENGE_RATE_URL

def main():
    load_dotenv()
    connection_string = get_db_connection_string()

    try:
        with DataLoader() as loader:
            df = loader.load_data(connection_string, PURCHASES_QUERY, "data/raw_data.csv")

            rate_df = loader.load_csv(TENGE_RATE_URL, "data/rate.csv")

        orderProcessor = (
            OrderProcessor(df)
            .convert_tenge_to_rubles(rate_df)
            .optimize_dtypes()
            .remove_outliers_by_bounds("revenue_rub", left=0)
            .remove_outliers_by_bounds("revenue_rub", right="q99")
            .drop_duplicates(
                subset=["user_id", "device_type_canonical", "created_ts_msk", "event_id", "revenue"],
                keep="first",
            )
        )
        

        profiles = (
            ProfileProcessor(orderProcessor.df)
                .create_segment_column(
                    "total_orders",
                    [
                        (0, 0, "0 заказов"),
                        (1, 1, "1 заказ"),
                        (2, 2, "2 заказа"),
                        (3, 4, "от 3 до 4 заказов"),
                        (5, None, "от 5 и выше"),
                    ]
                )
            )

        devices_stats = profiles.segment_stats('device_type_canonical', agg={'is_two': ['sum', 'mean']})
        print(devices_stats)

        regiones_stats = profiles.segment_stats('region_name', top_n=10, agg={'is_two': ['sum', 'mean']})
        print(regiones_stats)

        events_stats = profiles.segment_stats('event_type_main', agg={'is_two': ['sum', 'mean']})
        print(events_stats)
        
        # ---------- Гипотеза 1 ----------
        print("\nПроверка гипотезы 1:")
        print(
            "Пользователи, которые совершили первый заказ на спортивные мероприятия, "
            "совершают повторный заказ чаще, чем пользователи, оформившие свой первый заказ на концерты"
        )

        CONCERT_EVENT = 'концерты'
        SPORT_EVENT = 'спорт'
        
        concert_repeat_rate = events_stats.loc[CONCERT_EVENT, "is_two_mean"]
        sport_repeat_rate   = events_stats.loc[SPORT_EVENT,   "is_two_mean"]
        concert_n           = events_stats.loc[CONCERT_EVENT, "count"]
        sport_n             = events_stats.loc[SPORT_EVENT,   "count"]
        concert_two_sum     = events_stats.loc[CONCERT_EVENT, "is_two_sum"]
        sport_two_sum       = events_stats.loc[SPORT_EVENT,   "is_two_sum"]

        diff   = sport_repeat_rate - concert_repeat_rate
        p_pool = (sport_two_sum + concert_two_sum) / (sport_n + concert_n)
        z      = diff / (p_pool * (1 - p_pool) * (1 / sport_n + 1 / concert_n)) ** 0.5
        p_val  = 1 - stats.norm.cdf(z)

        print(f"  Концерты: {concert_repeat_rate:.2%}, Спорт: {sport_repeat_rate:.2%}")
        print(f"  Разница: {diff:.2%}, z = {z:.3f}, p-value = {p_val:.4f}")
        print("  Гипотеза подтверждена" if p_val < 0.05 and diff > 0
              else "  Гипотеза НЕ подтверждена")

        # ---------- Гипотеза 2 ----------
        print("\nПроверка гипотезы 2:")
        print(
            "В регионах, где больше всего пользователей посещают мероприятия, "
            "выше доля повторных заказов, чем в менее активных регионах"
        )

        region_df = regiones_stats.reset_index().iloc[:-1]

        corr, p_val = stats.spearmanr(region_df["count"], region_df["is_two_mean"])

        print(f"  Корреляция Спирмена: rho = {corr:.3f}, p-value = {p_val:.4f}")
        print("  Гипотеза подтверждена" if corr > 0 and p_val < 0.05
              else "  Гипотеза НЕ подтверждена")

        print(profiles.phik_matrix(
                [
                    'total_orders_segment', 
                    'avg_revenue_rub', 
                    'first_order_weekday_number',
                    'device_type_canonical',
                    'region_name',
                    'event_type_main',
                ],
                ['avg_revenue_rub']
            )
        )


    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
