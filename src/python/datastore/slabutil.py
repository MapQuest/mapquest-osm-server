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

"""Utility functions used for managing slab based access."""

import collections

import apiserver.const as C

__all__ = [ 'init_slabutil', 'slabutil_get_config', 'slabutil_group_keys',
            'slabutil_key_to_start_index', 'slabutil_make_slabkey',
            'slabutil_make_slab', 'slabutil_use_slab' ]

_slab_config = {}

def _make_numeric_slabkey(ns, nperslab, elemid):
    slabno = (int(elemid) / nperslab) * nperslab
    return "%sL%d" % (ns, slabno)

def _make_nonnumeric_slabkey(ns, elemid):
    return "%sL%s" % (ns, elemid)

class _Slab:
    def __init__(self, namespace, slabkey):
        self.namespace = namespace
        self.slabkey = slabkey


class _AlphabeticKeySlab(_Slab):
    def __init__(self, namespace, key, item):
        slabkey = _make_nonnumeric_slabkey(namespace[0].upper(), key)
        _Slab.__init__(self, namespace, slabkey)
        self._value = item
        self._key = key

    def __len__(self):
        return 1

    def items(self):
        return [(self._key, self._value)]

    def keys(self):
        return [self._key]

    def get(self, key):
        if key == self._key:
            return (True, self._value)
        return (False, key)

    def add(self, key, element):
        if key == self._key:
            assert element == self._value
        else:
            raise ValueError, "add() invoked multiple times."

class _NumericKeySlab(_Slab):
    def __init__(self, namespace, items):
        if len(items) == 0 or not isinstance(items, list):
            raise ValueError, "items should be non-empty list."
        k, _ = items[0]
        _, nperslab = _slab_config[namespace]

        slabkey = _make_numeric_slabkey(namespace[0].upper(), nperslab, k)
        start = slabutil_key_to_start_index(namespace, slabkey)

        _Slab.__init__(self, namespace, slabkey)

        self._nperslab = nperslab
        self._start = start
        self._contents = [None] * nperslab
        for (k,v) in items:
            index = int(k)
            if index >= start + nperslab:
                raise ValueError, \
                    "Index too large %s (start: %d, index: %d)" % \
                    (slabkey, start, index)
            index = index % nperslab
            if self._contents[index]:
                raise ValueError, \
                    "Repeated insertion at %s:%d" % (slabkey, index)
            self._contents[index] = v

    def __len__(self):
        return len(self._contents)

    def keys(self):
        return map(str, range(self._start, self._start + self._nperslab))

    def items(self):
        elements = []
        for i in range(self._nperslab):
            v = self._contents[i]
            if v is not None:
                elements.append((True, v))
            else:
                elements.append((False, str(self._start + i)))
        return elements

    def get(self, key):
        "Retrieve an object from the slab."
        index = int(key) % self._nperslab
        v = self._contents[index]
        if v is not None:
            return (True, v)
        return (False, key)


    def add(self, key, value):
        "Add an object at index."
        index = int(key) % self._nperslab
        self._contents[index] = value

def init_slabutil(config):
    "Initialize the module."
    _slab_config[C.CHANGESET] = (
        config.getint(C.DATASTORE, C.CHANGESETS_INLINE_SIZE),
        config.getint(C.DATASTORE, C.CHANGESETS_PER_SLAB))
    _slab_config[C.NODE] = (
        config.getint(C.DATASTORE, C.NODES_INLINE_SIZE),
        config.getint(C.DATASTORE, C.NODES_PER_SLAB))
    _slab_config[C.RELATION] = (
        config.getint(C.DATASTORE, C.RELATIONS_INLINE_SIZE),
        config.getint(C.DATASTORE, C.RELATIONS_PER_SLAB))
    _slab_config[C.WAY] = (
        config.getint(C.DATASTORE, C.WAYS_INLINE_SIZE),
        config.getint(C.DATASTORE, C.WAYS_PER_SLAB))

def slabutil_use_slab(namespace):
    "Return true of the given namespace uses slabs."
    return namespace in _slab_config

def slabutil_make_slabkey(namespace, elemid):
    "Prepare a slab key for a given element and namespace."
    nsk = namespace[0].upper()
    if _slab_config.has_key(namespace):
        _, nperslab = _slab_config[namespace]
        return _make_numeric_slabkey(nsk, nperslab, elemid)
    else:
        return _make_nonnumeric_slabkey(nsk, elemid)

def slabutil_group_keys(namespace, keys):
    "Group keys according to slabs."

    slabset = collections.defaultdict(set)
    nsk = namespace[0].upper()

    if slabutil_use_slab(namespace):
        _, nperslab = _slab_config[namespace]
        for k in keys:
            sk = _make_numeric_slabkey(nsk, nperslab, k)
            slabset[sk].add(k)
    else:
        for k in keys:
            sk = _make_nonnumeric_slabkey(nsk, k)
            slabset[sk].add(k)

    return slabset

def slabutil_get_config(namespace):
    "Return the configuration for a given slab."
    return _slab_config[namespace]

def slabutil_key_to_start_index(namespace, slabkey):
    """Return the start index of elements in a slab."""
    assert slabkey[1] == 'L'
    if slabutil_use_slab(namespace):
        return int(slabkey[2:])
    else:
        return slabkey[2:]

def slabutil_make_slab(namespace, items):
    """Return a populated slab of the appropriate kind."""

    if slabutil_use_slab(namespace):
        return _NumericKeySlab(namespace, items)
    else:
        return _AlphabeticKeySlab(namespace, items)
