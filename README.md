# AI-Enabled Integrated Smart Foundry Management and Optimization System

A final-year project prototype based on the supplied proposal.

## Modules
- Foundry dashboard and casting-order management
- Pattern image upload and pattern-recognition integration point
- Intelligent charge-mix recommendation
- Maintenance-log analysis assistant
- Cost and lead-time quotation estimator
- Furnace-load simulation

## Run
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. `pip install -r requirements.txt`
4. `python app.py`
5. Open `http://127.0.0.1:5000`

## Important
This is a functional prototype, not a production foundry control system. The pattern page includes a clear integration point for a trained YOLO model, and the charge optimizer currently uses a lightweight search with example material data. Replace those parts with validated foundry data/models before real-world use.
