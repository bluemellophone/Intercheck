Intercheck
==========

An automated SpeedTest logger and web interface for monitoring Internet
connectivity

.. .. image:: https://img.shields.io/pypi/v/intercheck.svg
..         :target: https://pypi.python.org/pypi/intercheck/
..         :alt: Latest Version
.. .. image:: https://img.shields.io/pypi/dm/intercheck.svg
..         :target: https://pypi.python.org/pypi/intercheck/
..         :alt: Downloads
.. .. image:: https://img.shields.io/pypi/l/intercheck.svg
..         :target: https://pypi.python.org/pypi/intercheck/
..         :alt: License

Prerequisites
-------------
- speedtest-cli
- Flask
- tornado
- requests
- simplejson
- Sphinx (optional)
- sphinxcontrib-napoleon (optional)

Install
-------

We strongly recommend installing Intercheck using a virtual environment.  Note
that some internal files and logs are stored on disk the folder
``~/.intercheck/``.  This directory should be deleted by the user if Intercheck
is uninstalled, but will delete all recorded logs in the process.

virtualenv (pip and Github)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    pip install virtualenv
    virtualenv ENV
    source ENV/bin/activate

pip
~~~

::

    pip install intercheck

Github
~~~~~~

::

    pip install git+https://github.com/bluemellophone/Intercheck.git

or

::

    git clone https://github.com/bluemellophone/Intercheck.git
    python setup.py install

Usage
-----

::

    $ intercheck -h
    usage: intercheck [-h] [-p PORT] [-i INTERVAL] [-e INTERVAL_EXACT] [-v]

    optional arguments:
      -h, --help            show this help message and exit
      -p PORT, --port PORT  which port to have the web server listen on
      -i INTERVAL, --interval INTERVAL
                            interval (in seconds) between each check
      -e INTERVAL_EXACT, --interval-exact INTERVAL_EXACT
                            round interval to the nearest minute
      -v, --version         show program's version number and exit

or

::

    $ python
    >>> import intercheck
    >>> help(intercheck.start)

Documentation
-------------

The documentation can be built with Sphinx.

::

    $ cd _docs
    $ make html
    $ open _build/html/index.html

Uninstall
---------

::

    pip uninstall intercheck
    rm -rf ~/.intercheck/

Acknowledgements
----------------

We would like to thank Almsaeed Studio for their open source AdminLTE theme and
SpeedTest for providing a command-line interface (CLI) to their service:

- https://github.com/almasaeed2010/AdminLTE
- https://github.com/sivel/speedtest-cli

