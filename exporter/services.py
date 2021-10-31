import base64
import logging
from contextlib import suppress
from typing import Any
from http import HTTPStatus
from urllib.parse import urljoin
from xml.dom import minidom

import requests
from flask import current_app
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type


EXPORT_URL_TEMPLATE = "/v1/queues/{queue_id}/export?id={annotation_id}"
RETRY_ATTEMPTS = 2


class ExporterException(IOError):
    """
    Special type of exception, needed to differentiate errors, raised manually.
    """
    pass


def send_annotation_info(queue_id: int, annotation_id: int) -> tuple[bool, str]:
    """
    Goes through the whole process of annotation processing:
        1. Get the annotation JSON from Rossum API
        2. Convert the annotation to XML format
        3. Send the annotation to dummy Rossum API

    :param queue_id: int
    :param annotation_id: int
    :return: tuple, first value is success bool,
        second is an error message if one occurs
    """
    # 1. Get the annotation JSON from Rossum API
    try:
        annotation_json = _get_annotation_json(queue_id, annotation_id)
    except ExporterException as e:
        logging.exception("Some exception happened during annotation retrieving:")
        return False, str(e)

    results = annotation_json.get("results", [])
    if not results:
        return False, "Couldn't find the annotation."

    # 2. Convert the annotation to XML format
    xml_result = _convert_annotation_to_xml(results[0])

    # 3. Send the annotation to dummy Rossum API
    try:
        _send_xml_result_to_rossum(annotation_id, xml_result)
        return True, ""
    except ExporterException as e:
        logging.exception("Some exception happened during annotation sending:")
        return False, str(e)


def _get_annotation_json(queue_id: int, annotation_id: int) -> dict[str, Any]:
    """
    Downloads an annotation in JSON format from ROSSUM web.
    :param queue_id: int
    :param annotation_id: int
    :return: dict, parsed annotation json
    """
    try:
        for attempt in Retrying(
            retry=retry_if_exception_type(requests.exceptions.RequestException),
            stop=stop_after_attempt(RETRY_ATTEMPTS),
            wait=wait_exponential(multiplier=1),
            reraise=True,
        ):
            with attempt:
                response = requests.get(
                    urljoin(
                        current_app.config["BASE_ROSSUM_URL"],
                        EXPORT_URL_TEMPLATE.format(queue_id=queue_id, annotation_id=annotation_id)
                    ),
                    headers={"Authorization": f"token {current_app.config['ROSSUM_TOKEN']}"},
                )
                if response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
                    raise requests.exceptions.RequestException
                elif response.status_code >= HTTPStatus.BAD_REQUEST:
                    raise ExporterException(response.json().get("detail", "Something wrong"))
                return response.json()
    except requests.exceptions.RequestException:
        raise ExporterException("Internal error")


def _convert_annotation_to_xml(annotation: dict[str, Any]) -> bytes:
    """
    Convert a JSON annotation to a correct XML format
    :param annotation: dict, parsed json annotation
    :return: bytes, bytestring of a converted XML
    """
    root = minidom.Document()
    invoice_registers = root.createElement("InvoiceRegisters")
    root.appendChild(invoice_registers)

    invoices = root.createElement("Invoices")
    invoice_registers.appendChild(invoices)

    payable = root.createElement("Payable")
    invoices.appendChild(payable)

    sections = annotation.get("content", [])

    # Flat is everything that is not details
    flat_elements = _get_flat_elements_list(sections, root)
    for element in flat_elements:
        payable.appendChild(element)

    details = root.createElement("Details")
    payable.appendChild(details)
    detail_elements = _get_detail_elements_list(sections, root)
    for element in detail_elements:
        details.appendChild(element)

    return root.toprettyxml(encoding="utf-8")


def _get_flat_elements_list(
        sections: list[dict[str, Any]],
        root: minidom.Document,
) -> list[minidom.Element]:
    """
    Returns a list of XML elements, which are not <Details>.
    :param sections: list of dicts, which contain info about the flat elements
    :param root: root xml element
    :return: list of XML elements
    """
    flat_element_mapping = {
        "invoice_info_section": (
            ("InvoiceNumber", "document_id"),
            ("InvoiceDate", "date_issue"),
            ("DueDate", "date_due"),
        ),
        "payment_info_section": (
            ("Iban", "iban"),
        ),
        "amounts_section": (
            ("TotalAmount", "amount_total"),
            ("Amount", "amount_total_tax"),
            ("Currency", "currency"),
        ),
        "vendor_section": (
            ("Vendor", "sender_name"),
            ("VendorAddress", "sender_address"),
        )
    }
    result = []
    for section_to_search_name, elements_to_append in flat_element_mapping.items():
        section_to_search = _get_section_children(sections, section_to_search_name)
        result.extend([
            _create_text_element(element_name, invoice_info_key, root, section_to_search)
            for element_name, invoice_info_key in elements_to_append
        ])
    result.append(root.createElement("Notes"))
    return result


def _get_detail_elements_list(
        sections: list[dict[str, Any]],
        root: minidom.Document
) -> list[minidom.Element]:
    """
    Returns a list of XML elements, which live in <Detail>
    :param sections: list of dicts, which contain info about the detail elements
    :param root: root xml element
    :return: list of XML elements
    """
    detail_element_mapping = {
        "item_amount_total": "Amount",
        "item_quantity": "Quantity",
        "item_description": "Notes",
    }
    details = _get_section_children(
        _get_section_children(sections, "line_items_section"),
        "line_items"
    )
    result = []
    for detail in details:
        detail_element = root.createElement("Detail")
        for json_key, element_name in detail_element_mapping.items():
            detail_element.appendChild(
                _create_text_element(
                    element_name, json_key, root, detail.get("children", [])
                )
            )
        detail_element.appendChild(root.createElement("AccountId"))
        result.append(detail_element)
    return result


def _get_section_children(
        sections: list[dict[str, Any]],
        section_name: str
) -> list[dict[str, str]]:
    """
    Fetches children of a specific section from a list of sections.
    :param sections: list of sections
    :param section_name: name of a sections from which to fetch children
    :return: list of dicts - children
    """
    for section in sections:
        if section.get("schema_id") == section_name:
            return section.get("children", [])
    return []


def _create_text_element(
        element_name: str,
        json_key: str,
        root: minidom.Document,
        children: list[dict[str, str]]
) -> minidom.Element:
    element = root.createElement(element_name)
    text = root.createTextNode(_find_value_in_children(children, json_key))
    element.appendChild(text)
    return element


def _find_value_in_children(children: list[dict[str, str]], child_name: str) -> str:
    for child in children:
        if child.get("schema_id") == child_name:
            return child.get("value", "")
    return ""


def _send_xml_result_to_rossum(annotation_id: int, xml_result: bytes) -> None:
    """
    This function will have no retrying or any other safe guards,
    since it sends a request to a known non-working endpoint.

    :param annotation_id: int, id of an annotation to be sent
    :param xml_result: bytes, resulted xml bytestring
    """
    xml_encoded = base64.encodebytes(xml_result)
    with suppress(Exception):
        requests.post(
            current_app.config["RESULT_ROSSUM_URL"],
            data={
                "annotationId": annotation_id,
                "content": xml_encoded
            }
        )
