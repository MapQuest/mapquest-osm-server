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
_stats = {}              # Hash maps tracking the collected statistics.
_prevstats = {}

_timer = None                   # Timer object.
_is_active = None               # Run state.
_lock = None

def _display_stats():
    "Display statistics"
    global _lock, _prevstats

    def _format(prefix, absval, incr):
        """Helper function."""
        s = ""
        if absval:
            s += ("%s: %%(_%sv)d" % (prefix.upper(), prefix))
            if incr:
                s += ("(+%%(_%s)d)" % prefix)
            s += "  "
        return s

    # Retrieve the previous and current counts.
    _c = _prevstats[C.CHANGESET]
    _n = _prevstats[C.NODE]
    _w = _prevstats[C.WAY]
    _r = _prevstats[C.RELATION]

    _lock.acquire()
    _cv = _stats[C.CHANGESET]
    _nv = _stats[C.NODE]
    _wv = _stats[C.WAY]
    _rv = _stats[C.RELATION]
    _prevstats.update(_stats)
    _lock.release()

    # Compute incremental changes.
    _c = _cv - _c
    _n = _nv - _n
    _w = _wv - _w
    _r = _rv - _r

    # Compute the format string.
    s = _format('c', _cv, _c)
    s += _format('n', _nv, _n)
    s += _format('w', _wv, _w)
    s += _format('r', _rv, _r)

    print s % locals()


def _stats_timer():
    "Invoke the actual display helper and re-arm the timer."

    _display_stats()

    global _timer
    if _is_active:
        _timer = threading.Timer(_timer_delay, _stats_timer)
        _timer.start()


def init_statistics(config, options):
    "Initialize the module."
    global _stats, _prevstats

    for n in [C.CHANGESET, C.NODE, C.WAY, C.RELATION]:
        _stats[n] = _prevstats[n] = 0

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
