import traceback
import os
import pickle
import json
from flask import flash, Response, request, session, g, redirect, url_for


def make_response(data: list):
    return Response(json.dumps(data), mimetype='application/json', headers={})


def enforce_login(func):
    def __inner__(*args, **kwargs):
        if not session.get('logged_in'):
            flash("You must be logged in to do this")
            return redirect(url_for('login'))
        else:
            return func(*args, **kwargs)
    __inner__.__name__ = func.__name__
    if hasattr(func, "__is_endpoint__"):
        __inner__.__is_endpoint__ = True
    return __inner__


def handle_request(format_response=False, private=False):
    def _handle_request(func):
        def __handle_request(*args, **kwargs):
            res = func(*args, **kwargs)
            return make_response(res) if format_response else res
        __handle_request.__is_endpoint__ = True
        __handle_request.__name__ = func.__name__
        return enforce_login(__handle_request) if private else __handle_request
    return _handle_request
