# ATLAS-OPS

Autonomous AI-Driven Payment Operations Platform.

## LOCAL SETUP

Make sure you have exactly the following dependencies locally active:

1. Install PostgreSQL
2. Install Redis
3. Create DB `atlas_ops`
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload` Or alternatively, run `python run_local.py`

When first launching the engine in a new environment, make sure to execute:
`python check_setup.py`

This will test your PostgreSQL daemon, intercept the Redis socket tests, and ascertain whether fallback DummyModels or the heavy `fraud_model.pkl` are instantiated globally!

### Environment configuration
Make sure to duplicate `.env.local.example` strictly into an `.env` layout on your root directly if you intend to start tweaking connection secrets.
