import pandas as pd
import numpy as np

class GuardianAuditor:
    def __init__(self, df):
        """
        Initialize the auditor with a pandas DataFrame.
        """
        self.df = df
        self.total_rows = len(df)
        self.report_summary = {}

    def check_completeness(self):
        """
        C - Completeness: Measures the percentage of non-null values.
        """
        null_counts = self.df.isnull().sum()
        completeness_pct = ((self.total_rows - null_counts) / self.total_rows) * 100
        
        self.report_summary['completeness'] = completeness_pct.mean()
        return completeness_pct

    def check_uniqueness(self):
        """
        U - Uniqueness: Identifies duplicate records.
        """
        duplicate_count = self.df.duplicated().sum()
        uniqueness_score = ((self.total_rows - duplicate_count) / self.total_rows) * 100
        
        self.report_summary['uniqueness'] = uniqueness_score
        return duplicate_count

    def check_validity(self, numeric_columns=None):
        """
        V - Validity: Checks if business-critical numeric columns have negative values.
        """
        validity_issues = {}
        if numeric_columns:
            for col in numeric_columns:
                invalid_count = (self.df[col] < 0).sum()
                validity_issues[col] = invalid_count
        
        total_issues = sum(validity_issues.values())
        validity_score = max(0, 100 - (total_issues / self.total_rows * 100))
        self.report_summary['validity'] = validity_score
        
        return validity_issues

    def check_timeliness(self, date_column):
        """
        T - Timeliness: Measures the 'freshness' of the data.
        """
        try:
            self.df[date_column] = pd.to_datetime(self.df[date_column])
            latest_date = self.df[date_column].max()
            days
