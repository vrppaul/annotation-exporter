from flask import jsonify, Response
from werkzeug.exceptions import HTTPException


def handle_http_exceptions(exception: HTTPException) -> tuple[Response, int]:
    return jsonify({
        "error": exception.description
    }), exception.code
