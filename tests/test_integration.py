import json
from unittest import mock

import requests

from tests.conftest import ClientMaker

CORRECT_USERNAME = "test"
CORRECT_PASSWORD = "test"


def test_full_run_ok(get_test_client: ClientMaker):
    client = get_test_client(env_dict={
        "CORRECT_USERNAME": CORRECT_USERNAME,
        "CORRECT_PASSWORD": CORRECT_PASSWORD
    })

    get_patch = mock.patch.object(requests, "get")
    post_patch = mock.patch.object(requests, "post")
    with get_patch as get_mock, post_patch:
        get_mock.return_value.status_code = 200
        with open("tests/fake_data.json") as fake_data:
            get_mock.return_value.json = mock.Mock()
            get_mock.return_value.json.return_value = json.loads(fake_data.read())
        response = client.post(
            "/export",
            auth=(CORRECT_USERNAME, CORRECT_PASSWORD),
            json={"annotation_id": 1, "queue_id": 1}
        )
        assert response.json == {"success": True}
