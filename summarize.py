#!/usr/bin/env python3
"""
Summarize log files.
"""

# Missing features:
#   - iptables normalization
#   - logcheck email message support (skip rfc822 headers and logcheck titles)

import re
import os
import sys
import errno
import doctest
import fileinput


def mkrule(rx, replacement):
    r"""Build a function that replaces a given regexp.

        >>> strip_whitespace = mkrule('\s+', '')
        >>> strip_whitespace('hello, world\t!')
        'hello,world!'

    """
    return lambda s, sub=re.compile(rx).sub: sub(replacement, s)


RULES = [
    # Get rid of date/time
    mkrule(r'^... +\d+ \d+:\d+:\d+ ', ''),
    # Get rid of process IDs
    mkrule(r'\[\d+\]', '[(pid)]'),
    # PostgreSQL
    mkrule(r'postgres\[\(pid\)\]: \[\d+\]', 'postgres[(pid)]: [(n)]'),
    mkrule(r'postgres\[\(pid\)\]: \[\d+-\d+\]', 'postgres[(pid)]: [(n-m)]'),
    # Samba
    mkrule(r'([sn]mbd\[\(pid\)\]): \[\d\d\d\d/\d\d/\d\d \d\d:\d\d:\d\d, \d+\]',
           r'{\1: [(datetime)]'),
    # Cyrus
    mkrule(r'(cyrus/imapd\[\(pid\)\]: skiplist: checkpointed .*)'
           r' \(\d+ records, \d+ bytes\) in \d+ seconds?',
           r'\1 ((num) records, (num) bytes) in (num) seconds'),
    mkrule(r'cyrus/([a-z_]+)\[\(pid\)\]: ([a-z]+):'
           r' (starting|committing) txn \d+',
           r'cyrus/\1[(pid)]: \2: \3 txn (txnid)'),
    mkrule(r'cyrus/lmtpd\[\(pid\)\]: duplicate_(check|mark): <(.*?)>\s+',
           r'cyrus/lmtpd[(pid)]: duplicate_\1: (msgid) '),
    mkrule(r'cyrus/master\[\(pid\)\]: process \d+ exited, status 0',
           r'cyrus/master[(pid)]: process (pid) exited, status 0'),
    # Postfix
    mkrule(r'postfix/cleanup\[\(pid\)\]: [0-9A-Z]+: message-id=[^ ]*',
           'postfix/cleanup[(pid)]: (queueid): message-id=(msgid)'),
    mkrule(r'postfix/([a-z]+)\[\(pid\)\]: [0-9A-Z]+:',
           r'postfix/\1[(pid)]: (queueid):'),
]


def uniq_with_counts(lines):
    """Collapse equal neighboring elements.

        >>> l = ['a', 'bb', 'bb', 'c', 'bb', 'd', 'd', 'd']
        >>> list(uniq_with_counts(l))
        [('a', 1), ('bb', 2), ('c', 1), ('bb', 1), ('d', 3)]

        >>> list(uniq_with_counts(['a']))
        [('a', 1)]

        >>> list(uniq_with_counts(['a', 'a']))
        [('a', 2)]

        >>> list(uniq_with_counts([]))
        []

    """
    it = iter(lines)
    try:
        last = next(it)
    except StopIteration:
        return
    count = 1
    for line in it:
        if line == last:
            count += 1
        else:
            yield last, count
            last = line
            count = 1
    yield last, count


def summarize(input, output=sys.stdout):
    lines = []
    for line in input:
        line = line.rstrip('\r\n')
        for rule in RULES:
            line = rule(line)
        lines.append(line)
    lines.sort()
    uniq_lines = list(uniq_with_counts(lines))
    print("Processed %d lines into %d lines" % (len(lines), len(uniq_lines)),
          file=output)
    for line, count in uniq_lines:
        if count > 1:
            print("%s\t{*%d}" % (line, count), file=output)
        else:
            print(line, file=output)


def main():
    test()
    pager = os.popen('less -S -M', 'w')
    try:
        summarize(fileinput.input(), pager)
    except IOError as e:
        if e.errno != errno.EPIPE:
            print(e, file=sys.stderr)
    pager.close()


def test():
    doctest.testmod()


if __name__ == '__main__':
    main()
