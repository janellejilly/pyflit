# -*- coding: utf-8 -*-

"""
Utility functions.
"""

import urllib2

# gzip/deflate/bzip2 support
from gzip import GzipFile
import zlib
import bz2
from StringIO import StringIO

import os
import sys
import time

import pprint


class ContentEncodingProcessor(urllib2.BaseHandler):
    """
    HTTP handler to add gzip/deflate/bzip2 capabilities to urllib2 requests.
    """
    def deflate(self, data):
        """
        zlib only provides the zlib compress format, not the deflate format;
        so on top of all there's this workaround:
        """
        try:
            return zlib.decompress(data, -zlib.MAX_WBITS)
        except zlib.error:
            return zlib.decompress(data)

    # add headers to requests
    def http_request(self, req):
        req.add_header("Accept-Encoding", "gzip, deflate")
        return req

    # decode
    def http_response(self, req, resp):
        old_resp = resp
        decompress_method = resp.headers.get("content-encoding")
        gz = None
        # gzip
        if decompress_method == "gzip":
            gz = GzipFile(fileobj=StringIO(resp.read()), mode="r")
        # deflate
        elif decompress_method == "deflate":
            gz = StringIO(self.deflate(resp.read()))
        # bzip2
        elif decompress_method == 'bzip2':
            gz = bz2.decompress(resp.read())

        if gz:
            resp = urllib2.addinfourl(gz,
                                      old_resp.headers,
                                      old_resp.url,
                                      old_resp.code)
            resp.msg = old_resp.msg
        return resp


class HTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    """HTTP redirect handler."""
    def http_error_301(self, req, fp, code, msg, headers):
        pass
    http_error_302 = http_error_303 = http_error_307 = http_error_301


def progressbar(total_volume, completed_volume, progress=0):
    """A simple progressbar.

    Arguments:
    - `total_volume`: int, total volume size.
    - `completed_volume`: int, completed volume size.
    - `progress`: int, completed percent.
    """
    progress = completed_volume / float(total_volume) * 100
    base = get_terminal_size()[1] / 2
    current = int(progress / 100 * base)
    info = u'\r[ %s%s Total: %-8d Completed: %.2f%% ]' % (
        current * '#',
        (base - current) * ' ',
        total_volume,
        progress)
    sys.stdout.write(info)
    sys.stdout.flush()
    time.sleep(0.3)


def get_terminal_size(fd=1):
    """
    Returns height and width of current terminal. First tries to get
    size via termios.TIOCGWINSZ, then from environment.

    Arguments:
    - `fd`: file descriptor (default: 1=stdout)
    """
    hw = (0, 0)
    if os.isatty(fd):
        try:
            import fcntl
            import termios
            import struct
            hw = struct.unpack('hh',
                               fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            try:
                hw = (os.environ['LINES'], os.environ['COLUMNS'])
            except:
                pass
    return hw


def dict_list_reverse(dict_list):
    """
    Dictionary list object reverse to process http redirection codes,
    see var codes in pyflit.config module.
    """
    dict_rev = {}
    for (key, vals) in dict_list.items():
        for val in vals:
            dict_rev[val] = key
            if not val.startswith('\\'):
                dict_rev[val.upper()] = key
    return dict_rev


class DictDotLookup(object):
    """
    Creates objects that behave much like a dictionaries, but allow nested
    key access using object '.' (dot) lookups.
    """
    def __init__(self, d):
        """
        Arguments:
        - `d`: dict, reserved dict of list, tuple, or dict.
        """
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]

    def __getitem__(self, name):
        return self.__dict__.get(name, None)

    def __iter__(self):
        return iter(self.__dict__.keys())

    def __repr__(self):
        return pprint.pformat(self.__dict__)
