build:
	docker-compose build

run:
	docker-compose up

build_and_run: build run

stop:
	docker-compose stop

destroy:
	docker-compose down

init_alembic:
	docker-compose exec api alembic init alembic
	docker-compose exec api python init_alembic.py

makemigrations:
	docker-compose exec api alembic revision --autogenerate

migrate:
	docker-compose exec api alembic upgrade head

init_and_migrate: init_alembic makemigrations migrate

shell_api:
	docker-compose exec api bash

shell_db:
	docker-compose exec db bash

# Local stuff
makemigrations_locally:
	alembic revision --autogenerate

migrate_locally:
	alembic upgrade head

init_alembic_locally:
	alembic init alembic
	python init_alembic.py


init_and_migrate_locally: init_alembic_locally makemigrations_locally migrate_locally