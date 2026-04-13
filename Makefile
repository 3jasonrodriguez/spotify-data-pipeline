up:
	docker compose up -d

airflow-up:
	docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d --build

airflow-down:
	docker compose -f docker-compose.airflow.yml down