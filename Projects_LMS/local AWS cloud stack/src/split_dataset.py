import os
import pandas as pd
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def split_data_by_month(input_filepath: str, output_dir: str, chunk_size: int = 500_000) -> None:
    """
    Reads a large CSV file in chunks and splits it into smaller CSV files
    grouped by month and year.

    Args:
        input_filepath (str): Path to the massive raw CSV file.
        output_dir (str): Directory to save the split monthly files.
        chunk_size (int): Number of rows to process in memory at once.
    """
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Starting to split {input_filepath} into {output_dir}")

    try:
        # We assume the dataset has a column named 'Departure' containing the timestamp
        chunk_iterator = pd.read_csv(input_filepath, chunksize=chunk_size, parse_dates=['Departure'])
        
        for i, chunk in enumerate(chunk_iterator):
            # Drop rows with missing dates to avoid errors
            chunk = chunk.dropna(subset=['Departure'])
            
            # Create a Year-Month column for grouping (e.g., '2016-05')
            chunk['YearMonth'] = chunk['Departure'].dt.strftime('%Y-%m')
            
            # Group the chunk by the YearMonth and append to corresponding files
            for period, group in chunk.groupby('YearMonth'):
                output_file = os.path.join(output_dir, f"bike_data_{period}.csv")
                
                # If file doesn't exist, write header. If it does, append without header.
                file_exists = os.path.isfile(output_file)
                group.drop(columns=['YearMonth']).to_csv(
                    output_file, 
                    mode='a', 
                    index=False, 
                    header=not file_exists
                )
            
            logging.info(f"Processed chunk {i + 1}...")

        logging.info("Splitting complete.")
        
    except Exception as e:
        logging.error(f"Error processing data: {e}")

if __name__ == "__main__":
    split_data_by_month(
        input_filepath="./data/raw/helsinki_bikes.csv",
        output_dir="./data/split_months/"
    )