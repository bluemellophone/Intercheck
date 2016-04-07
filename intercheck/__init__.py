#!/usr/bin/env python
"""
Intercheck Python Module

To start the Intercheck server and begin performing SpeedTest logging, run the
function intercheck.core.start().

To run a single SpeedTest and save it automatically to the log, run the function
intercheck.core.speedtest().

All logs and setting files are written to ~/.intercheck/
"""
from utils import __version__, version, tagline  # NOQA
from core import find_speedtest, speedtest, start  # NOQA
