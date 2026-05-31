# Documentation build (Zensical).

.PHONY: html fast serve clean

html:
	uv run python ../scripts/build_examples.py
	uv run zensical build --clean

fast:
	SKIP_NOTEBOOKS=1 uv run python ../scripts/build_examples.py
	uv run zensical build --clean

serve:
	uv run zensical serve

clean:
	rm -rf build source/examples
