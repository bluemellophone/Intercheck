#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
# HTTP / HTML
import flask
from flask import request
# Intercheck
from . import utils
# Python built-in
import logging
import math
import os


# Configure the logger
print = logging.warning


# Application
APP = flask.Flask(__name__)
APP.status = set(['init'])


################################################################################
# HTML Routes
################################################################################


@APP.route('/')
def index():
    settings_dict = utils.load_settings(quiet=True)
    return utils.template(settings_dict=settings_dict)


################################################################################
# JSON / AJAX Routes
################################################################################


@APP.route('/force/')
def force():
    utils.set_force()
    force_filepath = utils.get_force_filepath()
    status_dict = {
        'status': os.path.exists(force_filepath),
    }
    return utils.encode_to_json(status_dict)


@APP.route('/settings/', methods=['PUT'])
def settings():
    # Get current settings
    settings_dict = utils.load_settings(quiet=True)

    # Get new settings
    interval = request.form.get('intercheck-settings-interval', None)
    interval_exact = request.form.get('intercheck-settings-interval-exact', None)

    # Check setting values
    if interval is not None:
        try:
            interval = int(interval)
        except ValueError:
            interval = 0
        if interval < 60 or 3600 < interval:
            accepted = utils.DEFAULT_SETTINGS['interval']
        else:
            accepted = interval
        settings_dict['interval'] = accepted
    elif interval_exact is not None:
        if interval_exact not in ['true', 'false']:
            accepted = utils.DEFAULT_SETTINGS['interval_exact']
        else:
            accepted = interval_exact == 'true'
        settings_dict['interval_exact'] = accepted

    # Update settings with the accepted version and notify UI
    utils.update_settings(settings_dict)
    accepted_dict = {
        'accepted': accepted,
    }
    return utils.encode_to_json(accepted_dict)


@APP.route('/status/')
def status():
    status_dict = {
        'status': list(APP.status),
    }
    return utils.encode_to_json(status_dict)


@APP.route('/summary/')
def summary():
    day_seconds = 60 * 60 * 24
    stat_dict, record_interval = utils.get_summary_averages(round_values=True)
    record_interval = int(math.ceil(record_interval / day_seconds))
    status_dict = {
        'stats'    : stat_dict,
        'interval' : record_interval,
    }
    return utils.encode_to_json(status_dict)


@APP.route('/points/')
def points():
    latest = request.args.get('latest', None)
    stat_dict = utils.get_points(latest=latest)
    status_dict = {
        'points' : stat_dict,
    }
    return utils.encode_to_json(status_dict)


################################################################################
# File Downalod Routes
################################################################################


@APP.route('/download/log.csv')
def download_csv():
    csv_log_filepath = utils.get_csv_log_filepath()
    response = utils.download_file(csv_log_filepath)
    return response


@APP.route('/download/log.json')
def download_json():
    json_log_filepath = utils.get_json_log_filepath()
    response = utils.download_file(json_log_filepath)
    return response
