# Copyright (c) 2011 AOL Inc.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Manage statistics.

"""

import sys
import threading

import apiserver.const as C

_timer_delay = 1         # Number of seconds between reports.
_stats = {}              # Hash map tracking the collected statistics.

_timer = None                   # Timer object.
_is_active = None               # Run state.
_lock = None

def _display_stats():
    "Display statistics"
    global _lock
    _lock.acquire()
    print "C: %d, N: %d, W: %d, R: %d" % (
        _stats[C.CHANGESET],
        _stats[C.NODE],
        _stats[C.WAY],
        _stats[C.RELATION])
    _lock.release()

def _stats_timer():
    "Invoke the actual display helper and re-arm the timer."

    _display_stats()

    global _timer
    if _is_active:
        _timer = threading.Timer(_timer_delay, _stats_timer)
        _timer.start()


def init_statistics(config, options):
    "Initialize the module."
    global _stats

    for n in [C.CHANGESET, C.NODE, C.WAY, C.RELATION]:
        _stats[n] = 0

    global _lock
    _lock = threading.Lock()

    if options.verbose:
        global _is_active, _timer

        _is_active = True
        _timer = threading.Timer(_timer_delay, _stats_timer)
        _timer.daemon = True
        _timer.start()


def fini_statistics(options):
    "Shutdown the module."
    global _is_active
    _is_active = False

    if _timer:
        _timer.cancel()

    if options.verbose:
        _display_stats()


def increment_stats(namespace):
    global _lock, _stats

    _lock.acquire()
    _stats[namespace] = _stats[namespace] + 1
    _lock.release()
