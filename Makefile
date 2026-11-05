PY ?= .venv/bin/python

.PHONY: setup data features train export notebook all

setup:
	python3 -m venv .venv && $(PY) -m pip install -r requirements.txt

data:
	$(PY) src/download.py

features:
	cd src && ../$(PY) features.py

train:
	$(PY) src/train.py

export:
	cd src && ../$(PY) export.py

notebook:
	cd notebooks && ../.venv/bin/jupyter nbconvert --to notebook --execute --inplace analisis.ipynb

all: data features train export notebook
