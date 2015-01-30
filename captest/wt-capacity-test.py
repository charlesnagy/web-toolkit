#!/usr/bin/python
""" Capacity test script which replays URLs from a defined source and gather capacity metrics.

Tested with the followings:
CentOS 6.3
Python 2.6
"""

__author__ = "Karoly 'Charles' Nagy"
__copyright__ = "Copyright 2015, Karoly Nagy"
__licence__ = "GPL"
__version__ = "0.1.0"
__contact__ = "dr.karoly.nagy@gmail.com"

import time
import threading
import urllib2
import logging
import os
import sys
from Queue import Queue
from random import randint
from optparse import OptionParser
from logging.handlers import SysLogHandler

_LOG_FORMAT = '[%(process)d] %(levelname)-10s %(message)s'
# Syslog automatically provides timestamp on logs but we want that for stdout and file logs as well
_LOG_FORMAT_TIME = '%(asctime)s ' + _LOG_FORMAT
_LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def config_logging(level):
    _level_map = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
    }

    level = _level_map.get(level, logging.INFO)

    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT_TIME,
        datefmt=_LOG_DATE_FORMAT
    )

    # Also writing to syslog
    logger = logging.getLogger()
    _syslog = SysLogHandler(address='/dev/log')
    _syslog.setFormatter(logging.Formatter(_LOG_FORMAT))
    logger.addHandler(_syslog)

    logging.info('Logging set to %s' % logging.getLevelName(level))


def weighted_random(pairs, total):
    r = randint(1, total)
    _i = 0
    for (value, weight) in pairs:
        r -= weight
        _i += 1
        if r <= 0:
            logging.debug('Weighted random resulted after %d iteration.' % _i)
            return value


def collect(filepath):
    logging.info('Gathering urls from %s' % options.source)
    with open(filepath, 'r') as _f:
        for line in _f:
            yield line.split(',')


class Worker(threading.Thread):
    def __init__(self, queue, baseurl=''):
        super(Worker, self).__init__()
        self.counter = 0
        self.errors = 0
        self.queue = queue
        self.baseurl = baseurl
        self.enabled = True

    def run(self):
        while self.enabled:
            _url = self.queue.get()
            if _url is None:
                logging.debug('%s received the signal to finish' % self)
                return self.counter

            r = urllib2.urlopen('%s/%s' % (self.baseurl, _url))
            _c = r.getcode()
            if _c < 500:
                # Everything below 500 is valid answer from the server and can happen under normal workload
                r.read()
                logging.debug('Fetched %s with %d status code' % (_url, _c))
                self.counter += 1
            else:
                logging.warning('%s return with %d' % (_url._c))
                self.errors += 1
            time.sleep(0.01)


if __name__ == '__main__':
    parser = OptionParser(add_help_option=True, epilog="Run capacity test based on given urls.")
    parser.add_option('-s', '--source', action='store', type='string', dest='source',
                      help='CSV file to read the urls and weights from. Format: url,weight')
    parser.add_option('-c', '--concurrency', action='store', type='int', dest='concurrency', default=2,
                      help='Concurrency: the number of threads being spawned for fetching urls. Default: 2')
    parser.add_option('-t', '--time-out', action='store', type='int', dest='timeout', default=60,
                      help='Fetch random urls from the provided CSV files until this amount of seconds. Default: 60')
    parser.add_option('-B', '--base-url', action='store', type='string', dest='base_url', default='',
                      help='Base url if the urls in the csv file are relative. Default: \'\'')
    parser.add_option('-v', '--verbosity', dest='verbosity',
                      help="Setting the verbosity [0: Only CRITICAL, 1: ERROR, 2: WARNING, 3: INFO, 4: DEBUG]. Default: 3",
                      default=3, action='store', type='int')

    options, args = parser.parse_args()
    config_logging(options.verbosity)

    if not options.source:  # if filename is not given
        parser.error('No source has been given to read urls from.')

    urls = [(_u, int(_w)) for _u, _w in collect(options.source)]
    logging.info('%d urls have been found' % len(urls))
    total_weights = sum(pair[1] for pair in urls)
    _q = Queue()
    _threads = []
    logging.info('Initializing threads [concurrency: %d' % options.concurrency)
    for i in range(0, options.concurrency):
        _t = Worker(_q, options.base_url)
        _t.start()
        _threads.append(_t)
        logging.debug('Thread %s initialized' % _t)

    logging.info('Starting pushing urls into the workers\' queue. Timeout after %d seconds.' % options.timeout)
    _start = time.time()
    _total = 0
    while time.time() - _start < options.timeout:
        if _q.qsize() < options.concurrency * 2:
            _q.put(weighted_random(urls, total_weights))

    logging.info('Times up... Sending signals to workers.')
    for _t in _threads:
        # Gracefully stop the threads
        _q.put(None)

    for _t in _threads:
        _t.join()
        _total += _t.counter
    logging.info('Workers finished')

    _end = time.time()
    logging.info('Ran %d urls in %.2f seconds' % (_total, _end - _start))
    logging.info('Results: %.2f rqs/sec' % (_total / ( _end - _start)))
    print '---------------------'
    print 'Results: %.2f rqs/sec' % (_total / ( _end - _start))

    sys.exit(0)
