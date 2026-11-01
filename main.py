from src.loading import DataLoader
from src.queries import PURCHASES_QUERY
from src.config import get_db_connection_string


def main():
    connection_string = get_db_connection_string()

    with DataLoader() as loader:
        df = loader.load_data(connection_string, PURCHASES_QUERY, "data/raw_data.csv")
        cours = loader.load_csv('https://code.s3.yandex.net/datasets/final_tickets_tenge_df.csv', "data/cources.csv")
        loader.close()

if __name__ == "__main__":
    main()
