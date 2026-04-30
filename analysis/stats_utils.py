import numpy as np
import pandas as pd

def calculate_stats(latencies):
    """
    Calculate P50, P95, and P99 latencies.
    """
    if not latencies:
        return {'p50': 0, 'p95': 0, 'p99': 0, 'mean': 0}
    
    return {
        'p50': np.percentile(latencies, 50),
        'p95': np.percentile(latencies, 95),
        'p99': np.percentile(latencies, 99),
        'mean': np.mean(latencies)
    }

def load_exp2_data(data_dir, workflow, strategy):
    """
    Load total_latency_ms from CSV for a given workflow and strategy.
    """
    file_path = f"{data_dir}/exp2_{workflow}_{strategy}.csv"
    try:
        df = pd.read_csv(file_path)
        return df['total_latency_ms'].tolist()
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []
