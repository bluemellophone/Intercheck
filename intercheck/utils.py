#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
# HTTP / HTML
import flask
# Python built-in
import simplejson
import argparse
import logging
import time
import os


# Configure the logger
print = logging.warning


# Global variables
__version__ = '0.1.0dev'
version = __version__  # Alias for ipython
tagline = 'An automated SpeedTest logger and web interface for monitoring Internet connectivity'  # NOQA


DEFAULT_SETTINGS = {
    'port'           : 5000,
    'interval'       : 60 * 5,
    'interval_exact' : True,
}


GLOBAL_DICT = {
    '__version__'      : __version__,
    'DEFAULT_SETTINGS' : DEFAULT_SETTINGS,  # shallow, for when settings change
}


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.duration = self.end - self.start


def check_force(autodelete=True, **kwargs):
    force_filepath = get_force_filepath(**kwargs)
    if not os.path.exists(force_filepath):
        return False
    if autodelete:
        clear_force(**kwargs)
    return True


def configure_argparser():
    # Specify default arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int,
                        default=DEFAULT_SETTINGS.get('port'),
                        help='which port to have the web server listen on')
    parser.add_argument('-i', '--interval', type=int,
                        default=DEFAULT_SETTINGS.get('interval'),
                        help='interval (in seconds) between each check')
    parser.add_argument('-e', '--interval-exact', type=bool,
                        default=DEFAULT_SETTINGS.get('interval_exact'),
                        help='round interval to the nearest minute')
    parser.add_argument('-v', '--version', action='version', version=version)
    settings_dict = dict(parser.parse_args()._get_kwargs())
    return settings_dict


def configure_logging(verbose=False):
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[Intercheck] %(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    level = logging.INFO if verbose else logging.WARNING
    logger.setLevel(level)


def decode_from_json(json_str):
    value_dict = simplejson.loads(json_str)
    return value_dict


def clear_force(**kwargs):
    force_filepath = get_force_filepath(**kwargs)
    delete_file(force_filepath)


def clear_logs(**kwargs):
    csv_log_filepath = get_csv_log_filepath(**kwargs)
    delete_file(csv_log_filepath)
    json_log_filepath = get_json_log_filepath(**kwargs)
    delete_file(json_log_filepath)


def delete_file(filepath):
    try:
        os.remove(filepath)
    except OSError:
        pass


def download_file(filepath):
    content = open(filepath, 'r').read()
    filename = os.path.basename(filepath)
    extension = os.path.splitext(filename)[1]
    response = flask.make_response(content)
    content_disposition = 'attachment; filename=%s' % (filename, )
    response.headers['Content-Disposition'] = content_disposition
    response.mimetype = 'text/%s' % (extension, )
    return response


def encode_to_json(value_dict, add_version=True):
    if add_version:
        if 'version' in value_dict:
            raise ValueError('Cannot specify the argument "version" in the ' +
                             'value_dict when add_version is True')
        value_dict['version'] = version
    json_str = simplejson.dumps(value_dict)
    return json_str


def get_internal_path(ensure=True, **kwargs):
    internal_path = os.path.expanduser(os.path.join('~', '.intercheck'))
    internal_path = os.path.abspath(internal_path)
    if ensure and not os.path.exists(internal_path):
        os.makedirs(internal_path)
    return internal_path


def get_csv_log_filepath(**kwargs):
    internal_path = get_internal_path(**kwargs)
    csv_log_filepath = os.path.join(internal_path, 'log.csv')
    return csv_log_filepath


def get_force_filepath(**kwargs):
    internal_path = get_internal_path(**kwargs)
    force_filepath = os.path.join(internal_path, 'force')
    return force_filepath


def get_json_log_filepath(*args, **kwargs):
    internal_path = get_internal_path(**kwargs)
    csv_log_filepath = os.path.join(internal_path, 'log.json')
    return csv_log_filepath


def get_settings_filepath(*args, **kwargs):
    internal_path = get_internal_path(**kwargs)
    settings_filepath = os.path.join(internal_path, 'settings.json')
    return settings_filepath


def get_stats(day_list=[1, 30], latest=None, **kwargs):
    now = time.time()
    latest = -1 if latest is None else int(latest)
    day_seconds = 60 * 60 * 24
    # Open logs from JSON
    log = read_from_json_log(**kwargs)
    # Get the desired days
    day_list = sorted(day_list)
    thresh_list = [ now - 60 * 60 * 24 * day for day in day_list ]
    # Keys we want to average over
    key_list = ['ping', 'download', 'upload', 'duration', 'start']
    # Loop through records and get stats
    stat_dict = { day : { 'downtime' : 0.0 } for day in day_list }
    connected = None
    disconnected = False
    start_earliest = None
    for record in log['log']:
        start = record['start']
        if start < latest:
            # Respect a global latest limit, if specified
            continue
        if start < thresh_list[-1]:
            # Ignore records that were from over 30 days ago
            continue
        # Get earliest record from past 30 days
        if start_earliest is None:
            start_earliest = start
        start_earliest = min(start_earliest, start)
        # Get values for lists
        disconnected_ = False
        for key in key_list:
            value = record[key]
            if value is None:
                disconnected_ = True
                continue
            for index, day in enumerate(day_list):
                thresh = thresh_list[index]
                if start < thresh:
                    continue
                if key not in stat_dict[day]:
                    stat_dict[day][key] = []
                stat_dict[day][key].append(value)
        # Get downtime
        if disconnected_:
            disconnected = True
        else:
            if disconnected:
                key = 'downtime'
                for index, day in enumerate(day_list):
                    thresh = thresh_list[index]
                    if start < thresh:
                        continue
                    if connected is None:
                        start_day = int(thresh / day_seconds) * day_seconds
                        connected = max(start_earliest, start_day)
                    stat_dict[day][key] += start - connected
            disconnected = False
            connected = start
    if start_earliest is None:
        start_earliest = now
    # Get record interval
    record_interval = now - start_earliest
    return stat_dict, record_interval


def get_summary_averages(round_values=False, **kwargs):
    # Get stats
    stat_dict, record_interval = get_stats(**kwargs)
    # Calculate averages and variances
    for day in stat_dict:
        for key in stat_dict[day]:
            value_list = stat_dict[day][key]
            if key == 'downtime':
                value_avg = value_list / 60
                value_var = 0.0
            elif key == 'start':
                value_avg = 0.0
                value_var = 0.0
            else:
                assert isinstance(value_list, list)
                value_avg = sum(value_list) / len(value_list)
                value_list = [ abs(value - value_avg) for value in value_list ]  # NOQA
                value_var = sum(value_list) / len(value_list)
            if round_values:
                value_avg = float('%0.02f' % (value_avg, ))
                value_var = float('%0.02f' % (value_var, ))
            stat_dict[day][key] = (value_avg, value_var, )
    return stat_dict, record_interval


def get_points(**kwargs):
    # Get stats
    stat_dict, record_interval = get_stats(day_list=[30], **kwargs)
    return stat_dict


def load_settings(settings_filepath=None, quiet=False, **kwargs):
    default_settings = DEFAULT_SETTINGS.copy()
    if settings_filepath is None:
        settings_filepath = get_settings_filepath(**kwargs)
    error = False
    try:
        with open(settings_filepath, 'r') as settings_file:
            settings_json_str = settings_file.read()
            settings_dict = decode_from_json(settings_json_str)
    except IOError:
        error = True
        settings_dict = {}
    except simplejson.JSONDecodeError:
        error = True
        settings_dict = {}
    default_settings.update(settings_dict)
    if error:
        save_settings(default_settings, settings_filepath, **kwargs)
    if not quiet:
        print('Loaded settings: %s' % (settings_filepath, ))
        print_settings(default_settings)
    return default_settings


def print_settings(settings_dict):
    longest = max(map(len, settings_dict.keys()))
    for key, value in settings_dict.iteritems():
        args = (str(key).rjust(longest), value, )
        print('    %s : %s' % args)


def read_from_json_log(**kwargs):
    json_log_filepath = get_json_log_filepath(**kwargs)
    try:
        with open(json_log_filepath, 'r') as json_log:
            log = simplejson.load(json_log)
    except IOError:
        log = {
            'log' : []
        }
    return log


def save_settings(settings_dict, settings_filepath=None, quiet=False, **kwargs):
    if settings_filepath is None:
        settings_filepath = get_settings_filepath(**kwargs)
    settings_filepath = get_settings_filepath(**kwargs)
    with open(settings_filepath, 'w') as settings_file:
        simplejson.dump(settings_dict, settings_file)
    if not quiet:
        print('Saving settings: %s' % (settings_filepath, ))
        print_settings(settings_dict)


def set_force(**kwargs):
    force_filepath = get_force_filepath(**kwargs)
    with open(force_filepath, 'a'):
        pass
    print('Forcing...')


def template(template_name='index', **kwargs):
    template_ = '%s.html' % (template_name, )
    if 'GLOBAL_DICT' in kwargs:
        raise ValueError('Cannot specify the argument "GLOBAL_DICT" for ' +
                         'the template')
    kwargs['GLOBAL_DICT'] = GLOBAL_DICT
    return flask.render_template(template_, **kwargs)


def update_settings(*args, **kwargs):
    save_settings(*args, **kwargs)
    set_force(**kwargs)


def write_to_csv_log(key_list, **kwargs):
    csv_log_filepath = get_csv_log_filepath(**kwargs)
    if not os.path.exists(csv_log_filepath):
        with open(csv_log_filepath, 'w') as csv_log:
            csv_line = ','.join(key_list)
            csv_log.write('%s\n' % (csv_line, ))
    with open(csv_log_filepath, 'a') as csv_log:
        args = [ kwargs.get(key, None) for key in key_list ]
        args = [ '' if arg is None else '%s' % (arg, ) for arg in args ]
        csv_line = ','.join(args)
        csv_log.write('%s\n' % (csv_line, ))


def write_to_json_log(key_list, **kwargs):
    log = read_from_json_log(**kwargs)
    json_log_filepath = get_json_log_filepath(**kwargs)
    with open(json_log_filepath, 'w') as json_log:
        args = { key : kwargs.get(key, None) for key in key_list }
        log['log'].append(args)
        simplejson.dump(log, json_log)


def write_to_logs(key_list=None, **kwargs):
    """ Write the SpeedTest results to all log files.

    Write the given SpeedTest results dictionary to the logs on disk.
    Currently, that includes a CSV and a JSON log file.  Eventualy, and for
    scalability, this functionality will be powered by an SQLite3 database.


    Args:
        key_list (list of str): the list of ordered keys that should be written
            to the logs from the SpeedTest results.  Defaults to (in order):
                ``['start', 'duration', 'ping', 'download', 'upload']``
        **kwargs: arbitrary keyword arguments, passed to
            :func:`intercheck.utils.write_to_csv_log()` and
            :func:`intercheck.utils.write_to_json_log()`

    Returns:
        None
    """
    if key_list is None:
        key_list = ['start', 'duration', 'ping', 'download', 'upload']
    write_to_csv_log(key_list, **kwargs)
    write_to_json_log(key_list, **kwargs)
