import pandas as pd
import numpy as np

class GuardianAuditor:
    def __init__(self, df):
        self.df = df.copy()
        self.total_rows = len(df)
        self.report_summary = {}

    # -------------------------
    # Completeness
    # -------------------------
    def check_completeness(self):
        if self.total_rows == 0:
            return {}

        null_counts = self.df.isnull().sum()
        completeness_pct = ((self.total_rows - null_counts) / self.total_rows) * 100

        self.report_summary['completeness'] = float(completeness_pct.mean())
        return completeness_pct.to_dict()

    # -------------------------
    # Uniqueness
    # -------------------------
    def check_uniqueness(self):
        if self.total_rows == 0:
            return 0

        duplicate_count = int(self.df.duplicated().sum())
        uniqueness_score = ((self.total_rows - duplicate_count) / self.total_rows) * 100

        self.report_summary['uniqueness'] = float(uniqueness_score)
        return duplicate_count

    # -------------------------
    # Validity (Negative check)
    # -------------------------
    def check_validity(self, numeric_columns=None):
        if self.total_rows == 0 or not numeric_columns:
            return {}

        validity_issues = {}

        for col in numeric_columns:
            if col in self.df.columns:
                numeric_series = pd.to_numeric(self.df[col], errors="coerce")
                invalid_count = int((numeric_series < 0).sum())
                validity_issues[col] = invalid_count

        total_issues = sum(validity_issues.values())
        validity_score = max(0, 100 - (total_issues / self.total_rows * 100))

        self.report_summary['validity'] = float(validity_score)
        return validity_issues

    # -------------------------
    # Accuracy (Outlier check)
    # -------------------------
    def check_accuracy(self, columns=None):
        if self.total_rows == 0 or not columns:
            return {}

        outlier_report = {}

        for col in columns:
            if col in self.df.columns:
                numeric_series = pd.to_numeric(self.df[col], errors="coerce").dropna()

                if len(numeric_series) == 0:
                    outlier_report[col] = 0
                    continue

                Q1 = numeric_series.quantile(0.25)
                Q3 = numeric_series.quantile(0.75)
                IQR = Q3 - Q1

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = numeric_series[
                    (numeric_series < lower_bound) |
                    (numeric_series > upper_bound)
                ]

                outlier_report[col] = int(len(outliers))

        total_outliers = sum(outlier_report.values())
        accuracy_score = max(0, 100 - (total_outliers / self.total_rows * 100))

        self.report_summary['accuracy'] = float(accuracy_score)
        return outlier_report

    # -------------------------
    # Consistency
    # -------------------------
    def check_consistency(self, col_a=None, col_b=None):
        if self.total_rows == 0:
            return 0

        if col_a not in self.df.columns or col_b not in self.df.columns:
            return 0

        series_a = pd.to_numeric(self.df[col_a], errors="coerce")
        series_b = pd.to_numeric(self.df[col_b], errors="coerce")

        inconsistent_count = int((series_a < series_b).sum())

        consistency_score = ((self.total_rows - inconsistent_count) / self.total_rows) * 100
        self.report_summary['consistency'] = float(consistency_score)

        return inconsistent_count

    # -------------------------
    # Timeliness
    # -------------------------
    def check_timeliness(self, date_column=None):
        if self.total_rows == 0:
            return None

        if date_column not in self.df.columns:
            return None

        try:
            date_series = pd.to_datetime(self.df[date_column], errors="coerce")
            latest_date = date_series.max()

            if pd.isna(latest_date):
                return None

            days_since_update = (pd.Timestamp.now() - latest_date).days
            timeliness_score = max(0, 100 - (days_since_update * 2))

            self.report_summary['timeliness'] = float(timeliness_score)
            return int(days_since_update)

        except Exception:
            return None

    # -------------------------
    # Overall Score
    # -------------------------
    def get_overall_health_score(self):
        if not self.report_summary:
            return 0.0

        return round(
            sum(self.report_summary.values()) / len(self.report_summary),
            2
        )
