# HELP
# This will output the help for each task
# thanks to https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

build: ## Build containers
	docker-compose -f docker-compose.yml up --build -d

clean-build: clean db ## Clean and then build containers

clean-build-nocache: clean ## Clean and then build containers with no cache
	docker-compose -f docker-compose.yml build --no-cache

clean: ## Clean build files
	rm -rf .docker
	find . -name '*.pyc' -delete
	docker-compose -f docker-compose.yml stop
	docker-compose -f docker-compose.yml rm --force
	docker volume rm timescalebenchmark_postgres-data| true
	docker volume rm timescalebenchmark_timescaledb-data | true

dev: ## Bring up dev environment
	docker-compose -f docker-compose.yml up -d
	docker ps

db: ## Bring up dev environment and connect to db
	docker-compose -f docker-compose.yml up -d
	sleep 2
	docker exec -it timescalebenchmark_timescaledb_1 psql -U postgres homework -c "\d"
	docker exec -it timescalebenchmark_timescaledb_1 psql -U postgres homework -c "select count(*) from cpu_usage;"
