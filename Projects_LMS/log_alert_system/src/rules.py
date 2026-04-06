from abc import ABC, abstractmethod
import pandas as pd
import logging

class AlertRule(ABC):
    """Base class for all alerting rules."""
    
    @abstractmethod
    def evaluate(self, df: pd.DataFrame):
        pass

class FatalErrorsPerMinuteRule(AlertRule):
    """Rule 2.1: Alert on more than 10 fatal errors in less than 1 minute."""
    
    def evaluate(self, df: pd.DataFrame):
        if df.empty:
            return

        # Sort index by time just in case
        df = df.sort_index()
        
        # Calculate rolling count over a 1-minute window
        rolling_counts = df['severity'].rolling('1min').count()
        
        # Identify breaches
        breaches = rolling_counts[rolling_counts > 10]
        
        # In a real system, you'd want deduplication here so it doesn't alert 
        # on every single log after the 10th one. We capture the peak of the breach.
        if not breaches.empty:
            last_breach_time = breaches.index[-1]
            count = breaches.iloc[-1]
            logging.warning(f"[ALERT Rule 2.1] {count} fatal errors detected in 1 min up to {last_breach_time}")

class FatalErrorsPerHourPerBundleRule(AlertRule):
    """Rule 2.2: Alert on more than 10 fatal errors in less than 1 hour for a specific bundle_id."""
    
    def evaluate(self, df: pd.DataFrame):
        if df.empty:
            return

        df = df.sort_index()
        
        # Group by bundle_id, then apply a 1-hour rolling window to each group
        for bundle_id, group in df.groupby('bundle_id'):
            rolling_counts = group['severity'].rolling('1h').count()
            breaches = rolling_counts[rolling_counts > 10]
            
            if not breaches.empty:
                last_breach_time = breaches.index[-1]
                count = breaches.iloc[-1]
                logging.warning(f"[ALERT Rule 2.2] {count} fatal errors in 1 hour for bundle_id '{bundle_id}' up to {last_breach_time}")