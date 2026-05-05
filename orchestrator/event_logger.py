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
        Handles varying number of steps and keys across different runs.
        """
        file_path = os.path.join(self.output_dir, f"{experiment_name}.csv")
        file_exists = os.path.exists(file_path)
        
        total_warmup_calls = data.get('warmup_call_count', 0)

        # Flatten data for CSV
        row = {
            'timestamp': time.time(),
            'total_latency_ms': data['total_latency_ms'],
            'warmup_call_count': total_warmup_calls
        }
        
        for i, step in enumerate(data['steps']):
            # Use the node/function name if available, otherwise index
            node_id = step.get('node') or step.get('function_name') or f"step_{i}"
            
            row[f"{node_id}_latency_ms"] = step.get('latency_ms')
            row[f"{node_id}_lambda_duration_ms"] = step.get('lambda_duration_ms')
            row[f"{node_id}_is_warmup"] = step.get('is_warmup')
            row[f"{node_id}_status"] = step.get('status')

        # To handle dynamic keys (especially in 'branch' workflow), 
        # we read existing headers if file exists.
        if file_exists and os.path.getsize(file_path) > 0:
            try:
                with open(file_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    existing_headers = next(reader, None)
            except Exception:
                existing_headers = None

        with open(file_path, 'a', newline='') as f:
            # We use all keys in 'row' to ensure nothing is lost. 
            # Note: This might cause mismatched columns if keys change across runs.
            # In a production system, we'd use a more rigid schema or JSON.
            writer = csv.DictWriter(f, fieldnames=row.keys(), extrasaction='ignore')
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
