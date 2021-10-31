from dataclasses import fields
import os
from typing import Callable, Protocol
from unittest import mock

from flask.testing import FlaskClient
import pytest

from exporter.config import Config


class ClientMaker(Protocol):
    def __call__(self, env_dict: dict[str, str]) -> FlaskClient:
        ...


@pytest.fixture
def get_test_client() -> Callable:
    def client_maker(env_dict: dict[str, str]) -> FlaskClient:
        for field in fields(Config):
            env_dict.setdefault(field.name, "")
        with mock.patch.dict(os.environ, env_dict):
            from app import app
            app.testing = True
            return app.test_client()
    return client_maker
