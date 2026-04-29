.PHONY: install deploy exp1 clean

PYTHON = python3
PIP = pip3

install:
	$(PIP) install -r requirements.txt

deploy:
	chmod +x functions/deploy.sh
	cd functions && ./deploy.sh

exp1_warm:
	$(PYTHON) experiments/exp1_calibration/calibrate_warm.py

exp1_cold:
	$(PYTHON) experiments/exp1_calibration/calibrate_cold.py

exp1_tau:
	$(PYTHON) experiments/exp1_calibration/calibrate_recycle.py

exp1_scenarios:
	$(PYTHON) experiments/exp1_calibration/run_workflow_scenarios.py

clean:
	rm -rf functions/build
	find . -type d -name "__pycache__" -exec rm -rf {} +
