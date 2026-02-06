# tests/test_sessions_smoke.py
from src.workload.synthetic import make_zipf_dataset
from src.eval.sessions import SessionPlan, sample_sessions

def test_sessions_smoke():
	ds = make_zipf_dataset(n=1<<12, vocab=512, a=1.2, seed=1)
	counts = ds.value_counts()
	values = list(ds.index.keys())
	
	plan = SessionPlan(num_sessions=10, session_length=50, pattern="uniform", seed=0)
	sessions = sample_sessions(values, counts, plan)

	assert len(sessions) == 10
	assert all(len(s) == len(set(s)) == 50 for s in sessions)

	print("OK: sessions smoke test passed")

if __name__ == "__main__":
	test_sessions_smoke()
