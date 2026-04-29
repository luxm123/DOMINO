# DOMINO: Directed Orchestration for MIcro-service Networks and Operations

DOMINO is a project aimed at quantifying and mitigating cold start propagation effects in serverless workflows.

## Project Structure

- `orchestrator/`: Core orchestration logic.
- `functions/`: Test Lambda functions.
- `experiments/`: Experiment scripts.
- `analysis/`: Data analysis and plotting.
- `data/`: Raw experimental data.
- `config/`: Configuration files.

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Configure AWS credentials.
3. Deploy functions: `cd functions && ./deploy.sh`
4. Run experiments: `cd experiments/exp1_calibration && python calibrate_warm.py`
