import sys

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

        print(profiles.segment_stats('device_type_canonical', agg={'is_two': ['sum', 'mean']}))

        print(profiles.segment_stats('region_name', top_n=10, agg={'is_two': ['sum', 'mean']}))

        print(profiles.segment_stats('event_type_main', agg={'is_two': ['sum', 'mean']}))

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
