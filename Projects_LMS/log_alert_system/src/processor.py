import pandas as pd
import logging
from typing import List
from src.rules import AlertRule

class LogProcessor:
    def __init__(self, file_path: str, rules: List[AlertRule], chunksize: int = 500_000):
        self.file_path = file_path
        self.rules = rules
        self.chunksize = chunksize
        self.fatal_buffer = pd.DataFrame() 
        
        # Define all 24 columns exactly as provided in your problem statement
        self.all_columns = [
            'error_code', 'error_message', 'severity', 'log_location', 'mode', 
            'model', 'graphics', 'session_id', 'sdkv', 'test_mode', 'flow_id', 
            'flow_type', 'sdk_date', 'publisher_id', 'game_id', 'bundle_id', 
            'appv', 'language', 'os', 'adv_id', 'gdpr', 'ccpa', 'country_code', 'date'
        ]

    def process(self):
        logging.info(f"Starting log processing for {self.file_path}")
        
        # The specific columns we need in memory to evaluate our rules
        columns_to_read = ['date', 'severity', 'bundle_id']
        
        try:
            chunk_iterator = pd.read_csv(
                self.file_path, 
                chunksize=self.chunksize, 
                names=self.all_columns,  # Apply our actual column names
                header=0,                # Tell Pandas to overwrite that "0,1,2..." row
                usecols=columns_to_read
            )
            
            for chunk in chunk_iterator:
                # Changed 'fatal' to 'error' to match your dataset!
                is_fatal = chunk['severity'].astype(str).str.strip().str.lower() == 'error'
                fatal_chunk = chunk[is_fatal].copy()
                
                if not fatal_chunk.empty:
                    # DEBUG: Let's log how many we find in each chunk
                    logging.info(f"Caught {len(fatal_chunk)} fatal errors in current chunk.")
                    
                    # 1. Convert the column to standard numbers first
                    fatal_chunk['date'] = pd.to_numeric(fatal_chunk['date'], errors='coerce')
                    
                    # 2. Parse as datetime using seconds ('s') as the unit
                    fatal_chunk['date'] = pd.to_datetime(fatal_chunk['date'], unit='s', errors='coerce')
                    fatal_chunk.dropna(subset=['date'], inplace=True)
                    
                    fatal_chunk.set_index('date', inplace=True)
                    
                    # 2. Append to our rolling buffer
                    self.fatal_buffer = pd.concat([self.fatal_buffer, fatal_chunk])
                    self.fatal_buffer.sort_index(inplace=True)
                    
                    # 3. Trim the buffer to keep only the last 1 hour of data 
                    if not self.fatal_buffer.empty:
                        cutoff_time = self.fatal_buffer.index[-1] - pd.Timedelta(hours=1)
                        self.fatal_buffer = self.fatal_buffer[self.fatal_buffer.index >= cutoff_time]
                    
                    # 4. Evaluate rules against the current buffer
                    for rule in self.rules:
                        rule.evaluate(self.fatal_buffer)
                        
        except Exception as e:
            logging.error(f"Failed to process logs: {e}")