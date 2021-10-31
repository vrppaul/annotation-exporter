.PHONY: start
start:
	docker-compose build
	docker-compose up -d

.PHONY: stop
stop:
	docker-compose stop