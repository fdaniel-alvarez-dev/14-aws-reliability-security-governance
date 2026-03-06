.PHONY: setup demo test clean

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

demo:
	python3 pipelines/pipeline.py --mode demo

test:
	TEST_MODE=demo python3 tests/run_tests.py

clean:
	rm -rf .venv artifacts
