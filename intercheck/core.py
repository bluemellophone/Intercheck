#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
# HTTP / HTML
import tornado
import tornado.wsgi
import tornado.httpserver
# Intercheck
from . import utils
from . import routes
# Python built-in
import webbrowser
import threading
import logging
import httplib
import socket
import time
import os


# Configure the logger
print = logging.warning
utils.configure_logging()


# Get a handle on the APP
APP = routes.APP


def background(settings_filepath, min_interval_connected=60.0,
               min_interval_disconnected=30.0, force_check_interval=1,
               debug=True):
    duration_run_avg = None
    while True:
        # Load settings
        settings_dict = utils.load_settings(quiet=True)
        interval = settings_dict.get('interval')
        interval_exact = settings_dict.get('interval_exact')
        # Check the interval to make sure it is reasonable
        if interval < min_interval_connected:
            print('Warning, interval less than 1 minute (minimum interval)')
            interval = max(min_interval_connected, interval)
        if interval < duration_run_avg:
            print('Warning, interval less than average duration')
        # Run SpeedTest
        APP.status.discard('waiting')
        APP.status.add('testing')
        result_dict = speedtest()
        APP.status.discard('testing')
        APP.status.add('waiting')
        # Check for success
        success = result_dict.get('success')
        if success:
            APP.status.discard('disconnected')
            APP.status.add('connected')
        else:
            APP.status.discard('connected')
            APP.status.add('disconnected')
            interval = min_interval_disconnected
        # Get duration and update running average
        duration = result_dict.get('duration')
        if duration_run_avg is None:
            duration_run_avg = duration
        else:
            duration_run_avg = (duration_run_avg + duration) * 0.5
        # Calculate the timeout
        timeout = max(0, interval - duration)
        current = time.time()
        future = current + timeout
        # Correct for Intercheck overhead, round timeout to the nearest minute
        offset = 0.0
        if interval_exact:
            near_interval = 60.0 if success else min_interval_disconnected
            nearest = round(future / near_interval) * near_interval
            offset = nearest - future
        # Correct timeout and future
        timeout += offset
        future += offset
        # Output results of the SpeedTest
        time_str = time.strftime('%D %H:%M:%S', time.localtime(future))
        if debug:
            args = (interval, offset, duration_run_avg, )
            additional = ' (interval %0.2f, offset %0.2f, avg. %0.3f)' % args
        else:
            additional = ''
        args = (timeout, time_str, additional)
        print('Waiting for next check in %0.2f sec. at %s%s' % args)
        # Sleep for the timeout duration, checking for the force file
        while timeout > 0:
            timeout_small = min(force_check_interval, timeout)
            timeout -= timeout_small
            if utils.check_force():
                print('Forcing...')
                break
            time.sleep(timeout_small)


def start_background(settings_filepath):
    if hasattr(APP, 'background_thread') and APP.background_thread is not None:
        print('Cannot start the background process, already running')
        return
    args = [settings_filepath]
    APP.background_thread = threading.Thread(target=background, args=args)
    APP.background_thread.setDaemon(True)
    APP.background_thread.start()
    APP.background_thread.join(0)


def speedtest(verbose=True):
    # Ensure we have the speedtest-cli to use
    find_speedtest(quiet=True)
    # Start the SpeedTest
    if verbose:
        print('Performing SpeedTest...')
    start, duration, ping, download, upload = None, None, None, None, None
    with utils.Timer() as timer:
        try:
            with os.popen(' '.join([APP.server_cli, '--simple'])) as response:
                for line in response:
                    line = line.strip().split()
                    if len(line) == 3:
                        try:
                            key, value = line[:2]
                            value = float(value)
                            if key.startswith('Ping'):
                                ping     = value
                            if key.startswith('Download'):
                                download = value
                            if key.startswith('Upload'):
                                upload   = value
                        except IndexError:
                            pass
                        except ValueError:
                            pass
        except httplib.BadStatusLine:
            pass
    # Compile the results, possibly print
    start = timer.start
    duration = timer.duration
    if verbose:
        ping_str     = 'ERROR\t\t' if ping     is None else '%0.03f ms'   % (ping, )  # NOQA
        download_str = 'ERROR\t\t' if download is None else '%0.03f Mb/s' % (download, )  # NOQA
        upload_str   = 'ERROR'     if upload   is None else '%0.03f Mb/s' % (upload, )  # NOQA
        message = '\tPing: %s\tDownload: %s\tUpload: %s'
        args = (ping_str, download_str, upload_str, )
        print(message % args)
        message = '\tDuration: %0.03f sec.\tPerformed: %s'
        time_str = time.strftime('%D %H:%M:%S', time.localtime(start))
        args = (duration, time_str, )
        print(message % args)
        print('...done')
    # Create results dict
    # Yay, DeMorgan
    failure = ping is None or download is None or upload is None
    result_dict = {
        'start'    : start,
        'duration' : duration,
        'ping'     : ping,
        'download' : download,
        'upload'   : upload,
        'success'  : not failure,
    }
    # Write results to log(s)
    utils.write_to_logs(**result_dict)
    return result_dict


def find_speedtest(command='speedtest-cli', quiet=False):
    # Check to see if speedtest-cli has already been found
    if hasattr(APP, 'server_cli') and APP.server_cli is not None:
        if not quiet:
            print('Cached %s (%s)' % (command, APP.server_cli, ))
        return
    # Find speedtest-cli using bash 'which'
    with os.popen(' '.join(['which', command])) as response:
        for line in response:
            line = line.strip()
            if len(line) > 0 and line.endswith(command):
                APP.server_cli = os.path.abspath(line)
                print('Found %s (%s)' % (command, APP.server_cli, ))
                break  # Gaurantee only first line is processed
            else:
                message = 'Command line interface %r cannot be found, ' + \
                          'install using \'pip install speedtest-cli\''
                raise RuntimeError(message % (command, ))


def start(**kwargs):
    # Configure the command line argument parser
    cl_settings_dict = utils.configure_argparser()
    # Load last settings from disk, if first time load default settings in utils
    settings_dict = utils.load_settings(quiet=True)
    # Update settings with command line argument settings
    settings_dict.update(cl_settings_dict)
    # Update settings with instance-specific settings
    settings_dict.update(kwargs)
    # Save settings
    utils.save_settings(settings_dict, quiet=False)
    # Determine the IP address
    try:
        APP.server_ip_address = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        APP.server_ip_address = '127.0.0.1'
    APP.server_port = settings_dict.get('port')
    # Initialize the web handler
    try:
        wsgi_container = tornado.wsgi.WSGIContainer(APP)
        http_server = tornado.httpserver.HTTPServer(wsgi_container)
        http_server.listen(APP.server_port)
    except socket.error:
        args = (APP.server_port, )
        print('Cannot start Intercheck on port %d, already in use' % args)
        return
    # Determine the URL for this server
    url = 'http://%s:%s' % (APP.server_ip_address, APP.server_port)
    print('Intercheck starting at %s' % (url,))
    # Open URL in default browser
    print('Opening Intercheck using system\'s default browser')
    webbrowser.open(url)
    # Start the IO loop, blocking
    start_background('')
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    start()
