install:
	pip install -r requirements.txt

lint:
	flake8 .

sast:
	semgrep ci

run:
	python app.py