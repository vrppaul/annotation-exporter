import functools

from flask import abort, current_app, request


def correct_auth_required(view):
    """
    Decorator, which checks, whether user provided correct credentials.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if request.authorization is None:
            abort(401)

        if not _credentials_are_correct(
                request.authorization["username"],
                request.authorization["password"]
        ):
            abort(403)

        return view(**kwargs)

    return wrapped_view


def _credentials_are_correct(username: str, password: str) -> bool:
    """
    Compares provided credentials with the only one correct,
    stored in the config of the app.
    :param username: str, provided by user.
    :param password: str, provided by user.
    :return: bool, whether provided and correct credentials match.
    """
    correct_username = current_app.config["CORRECT_USERNAME"]
    correct_password = current_app.config["CORRECT_PASSWORD"]

    # If any of correct credentials are missing, raise server error,
    # so that it is explicit that an error is on our side
    if not correct_username or not correct_password:
        raise abort(500, "Cannot check credential correctness.")

    return username == correct_username and password == correct_password
