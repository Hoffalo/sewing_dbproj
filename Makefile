PYTHON ?= python3
MANAGE ?= $(PYTHON) manage.py

.PHONY: up down migrate seed erd messages compile messages-compile black ruff

up:
	docker compose up --build

down:
	docker compose down

migrate:
	$(MANAGE) migrate

seed:
	$(MANAGE) seed_demo

erd:
	$(MANAGE) graph_models -a -g -o docs/erd.png
	$(MANAGE) graph_models customers orders production -o docs/erd_main.png

messages:
	$(MANAGE) makemessages -l en -l es --ignore=.venv

compile:
	$(MANAGE) compilemessages

messages-compile: compile

black:
	black .

ruff:
	ruff check .
