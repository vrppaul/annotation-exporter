from flask import Blueprint, jsonify, Response
from pydantic import BaseModel

from exporter.auth import correct_auth_required
from exporter.decorators import validate_data
from exporter.services import send_annotation_info

export_bp = Blueprint("export", __name__)


class ExportBody(BaseModel):
    annotation_id: int
    queue_id: int


@export_bp.post("/export")
@correct_auth_required
@validate_data(ExportBody)
def export_view(body: ExportBody) -> Response:
    """
    Downloads XML of an annotation, converts it into the correct format,
    then uploads it to a rossum endpoint, dedicated for such stuff.
    :param body: ExportBody, should contain annotation_id and queue_id.
    :return: json Response. "success" with corresponding value,
        "error" with corresponding error message if any error occurred.
    """
    success, error_message = send_annotation_info(body.queue_id, body.annotation_id)
    response = {"success": success}
    if error_message:
        response["error_message"] = error_message
    return jsonify(response)
