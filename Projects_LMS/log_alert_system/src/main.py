import logging
from src.rules import FatalErrorsPerMinuteRule, FatalErrorsPerHourPerBundleRule
from src.processor import LogProcessor

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Instantiate the rules you want active
    active_rules = [
        FatalErrorsPerMinuteRule(),
        FatalErrorsPerHourPerBundleRule()
    ]
    
    # Initialize processor pointing to the mounted Docker volume data
    processor = LogProcessor(
        file_path='/app/data/alert_project_data.csv',
        rules=active_rules,
        chunksize=250_000 
    )
    
    processor.process()
    logging.info("Processing complete.")