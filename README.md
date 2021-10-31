# Rossum annotation exporter

> ⚠️ **DISCLAIMER**: This project is `development only` version,
> it won't be deployed to any production environment.
> Thus, any sensitive data may freely live in the repo.

Simple web application, which has a single endpoint, dedicated to annotation parsing and convertion.


## How to launch locally

### Docker start

- Easiest way if you have `docker` and `docker-compose` installed is to run `make` command,
which will run the docker container at the background:
```shell
make start
```
Server will be available at http://0.0.0.0:8000/

- Similarly, server can be stopped with another `make` command:
```shell
make stop
```


## How to verify correctness

- Use any API tool/platform of your chose.
- While application running, make a `POST` request:
  - endpoint: `http://0.0.0.0:5000/eport`
  - auth: Basic. Username: `myUser123`, Password: `secretSecret`
  - body:
    ```json
    {
        "annotation_id": 9142612,
        "queue_id": 136373
    }
    ```
- Should return following json response:
```json
{
    "success": true
}
```


## How to develop

### Required tools

- Python3.9

### Optional tools

- docker and docker-compose
- make

### Testing

Run tests from the root folder with `pytest --cov` command.

### Linting and code formatting

This project uses none, since it is not required by the task.