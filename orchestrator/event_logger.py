import csv
import os
import time

class EventLogger:
    def __init__(self, output_dir='data'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def log_workflow(self, experiment_name, data):
        """
        Log workflow execution results to CSV.
        """
        file_path = os.path.join(self.output_dir, f"{experiment_name}.csv")
        file_exists = os.path.exists(file_path)
        
        # Flatten data for CSV
        row = {
            'timestamp': time.time(),
            'total_latency_ms': data['total_latency_ms']
        }
        
        for i, step in enumerate(data['steps']):
            func = step.get('function_name', f"step_{i}")
            row[f"{func}_latency_ms"] = step.get('step_latency_ms')
            row[f"{func}_lambda_duration_ms"] = step.get('lambda_duration_ms')
            row[f"{func}_is_warmup"] = step.get('is_warmup')
            row[f"{func}_request_id"] = step.get('request_id')

        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def log_calibration(self, function_name, stage, data):
        """
        Log calibration results.
        """
        file_path = os.path.join(self.output_dir, f"calibration_{function_name}_{stage}.csv")
        file_exists = os.path.exists(file_path)
        
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(data)
