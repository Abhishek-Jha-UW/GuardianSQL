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
        
        # Store the average completeness score for the overall health grade
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
        
        # Calculate validity score based on issues found
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
            days_since_update = (pd.Timestamp.now() - latest_date).days
            
            # Score: 100 if data is from today, decays as it gets older
            timeliness_score = max(0, 100 - (days_since_update * 2)) 
            self.report_summary['timeliness'] = timeliness_score
            return days_since_update
        except:
            return None

    def get_overall_health_score(self):
        """
        Returns the weighted average of all performed checks.
        """
        if not self.report_summary:
            return 0
        return sum(self.report_summary.values()) / len(self.report_summary)

    def check_accuracy(self, columns):
        """
        A - Accuracy: Uses IQR to find statistical outliers.
        """
        outlier_report = {}
        for col in columns:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
            outlier_report[col] = len(outliers)
        
        # Scoring: penalty based on % of outliers
        total_outliers = sum(outlier_report.values())
        accuracy_score = max(0, 100 - (total_outliers / self.total_rows * 100))
        self.report_summary['accuracy'] = accuracy_score
        return outlier_report

    def check_consistency(self, col_a, col_b, relationship="a_gt_b"):
        """
        C - Consistency: Checks if logical relationships hold (e.g., Total >= Added).
        """
        if relationship == "a_gt_b":
            inconsistent = self.df[self.df[col_a] < self.df[col_b]]
        
        inconsistent_count = len(inconsistent)
        consistency_score = max(0, 100 - (inconsistent_count / self.total_rows * 100))
        self.report_summary['consistency'] = consistency_score
        return inconsistent_count
