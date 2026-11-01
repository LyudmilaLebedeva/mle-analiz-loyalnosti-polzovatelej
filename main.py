from src.processing import DataProcessor
from src.queries import query
from src.config import get_db_connection_string

def main():
    db_connection_string = get_db_connection_string() 

    processor=DataProcessor()

    df = processor.load_data(db_connection_string, query, 'data/raw_data.csv', force=False)

if __name__ == "__main__":
    main()
