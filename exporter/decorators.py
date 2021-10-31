from functools import wraps
from typing import Callable, Type, get_type_hints

from flask import jsonify, request
from pydantic import BaseModel, ValidationError


def validate_data(model: Type[BaseModel]) -> Callable:
    def wrapper(view: Callable) -> Callable:
        model_arg_name = _get_model_arg_name(view)

        @wraps(view)
        def wrapped_view(*args, **kwargs):
            data = request.get_json(force=True)
            try:
                validated_data = model(**data)
                kwargs[model_arg_name] = validated_data
                return view(*args, **kwargs)
            except ValidationError as e:
                return jsonify(e.errors()), 400
        return wrapped_view
    return wrapper


def _get_model_arg_name(view: Callable) -> str:
    for arg_name, arg_type in get_type_hints(view).items():
        if issubclass(arg_type, BaseModel):
            return arg_name
