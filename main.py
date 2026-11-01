import sys

from dotenv import load_dotenv

from src.loading import DataLoader
from src.processing import DataProcessor
from src.queries import PURCHASES_QUERY
from src.config import get_db_connection_string, TENGE_RATE_URL


def main():
    load_dotenv()
    connection_string = get_db_connection_string()

    try:
        with DataLoader() as loader:
            df = loader.load_data(connection_string, PURCHASES_QUERY, "data/raw_data.csv")

            rate_df = loader.load_csv(TENGE_RATE_URL, "data/rate.csv")

            processor = DataProcessor()
            (
                processor
                .set_data(df, rate_df)
                .validate()
                .convert_tenge_to_rubles()
                .optimize_dtypes()
            )
    except ValueError as e:
        print(f"Ошибка валидации: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
