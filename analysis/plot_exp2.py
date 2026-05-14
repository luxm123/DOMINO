import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.stats_utils import calculate_stats, load_exp2_data

def plot_performance_bars(data_dir='data/exp2', output_dir='analysis/output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    workflows = ['chain', 'fanout', 'branch']
    strategies = ['vanilla', 'keep_alive', 'orion', 'domino']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, wf in enumerate(workflows):
        ax = axes[idx]
        ax2 = ax.twinx() # Create a twin axis for warmup counts
        
        x = np.arange(len(strategies))
        width = 0.65
        
        p99s = []
        avg_warmups = []
        
        for strategy in strategies:
            data = load_exp2_data(data_dir, wf, strategy)
            latencies = data['latencies']
            warmups = data['warmup_calls']
            
            stats = calculate_stats(latencies)
            p99s.append(stats['p99'] / 1000.0)
            avg_warmups.append(sum(warmups) / len(warmups) if warmups else 0)
        
        # Plot Latencies (Left Axis)
        bar_colors = ['#BDBDBD', '#66BD63', '#2C7FB8', '#F28E2B']
        ax.bar(x, p99s, width, label='P99 (Latency)', color=bar_colors, alpha=0.9)
        for xi, val in zip(x, p99s):
            ax.text(xi, val + 0.35, f"{val:.2f}", ha='center', va='bottom', fontsize=9)
        
        # Plot Warmups (Right Axis)
        ax2.plot(x, avg_warmups, color='red', marker='D', linestyle='-', linewidth=2, label='Avg Warmups', markersize=8)
        ax2.set_ylabel('Avg Warmup Calls', color='red', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='red')
        
        # Ensure red line is visible by setting y-axis limits slightly above max
        max_warmup = max(avg_warmups) if avg_warmups else 5
        ax2.set_ylim(0, max_warmup + 1) 
        
        ax.set_title(f'Workflow: {wf.capitalize()}', fontsize=14, fontweight='bold')
        ax.set_ylabel('End-to-End Latency (s)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels([s.upper() for s in strategies], rotation=15)
        
        if idx == 0:
            # Combine legends
            lines, labels = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines + lines2, labels + labels2, loc='upper right', fontsize=10)
        
        ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/exp2_p99_comparison.png', dpi=300)
    plt.savefig(f'{output_dir}/exp2_p99_comparison.pdf')
    print(f"Plot saved to {output_dir}/exp2_p99_comparison.png")

if __name__ == "__main__":
    plot_performance_bars()
