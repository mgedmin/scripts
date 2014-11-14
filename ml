#!/usr/bin/python
"""
Check multiple mailboxes/maildirs for mail.

Wrapper for Debian's mailcheck package that produces more concise output.
"""

import os
import sys


def parse_mailcheck(lines):
    """Parse mailcheck's output.

        >>> from StringIO import StringIO
        >>> lines = StringIO('''
        ... You have 1 saved messages in /home/mg/Mail/Work/INBOX
        ... You have 4 new messages in /home/mg/Mail/Home/IN.root
        ... You have 2 new and 18 saved messages in /home/mg/Mail/Home/IN.zope
        ... You have new mail in /var/spool/mail/mg
        ... You have mail in /var/spool/mail/root
        ... '''.lstrip())
        >>> for mailbox, new, saved in parse_mailcheck(lines):
        ...     print mailbox, new, saved
        /home/mg/Mail/Work/INBOX 0 1
        /home/mg/Mail/Home/IN.root 4 0
        /home/mg/Mail/Home/IN.zope 2 18
        /var/spool/mail/mg True 0
        /var/spool/mail/root 0 True

    """
    for line in lines:
        left, right = line.split('in', 1)
        words = left.split()
        mailbox = right.strip()
        new = saved = 0
        for a, b in zip(words, words[1:]):
            if b == 'new' and a.isdigit():
                new = int(a)
            if b == 'saved' and a.isdigit():
                saved = int(a)
            if (a, b) == ('have', 'new'):
                new = True
            if (a, b) == ('have', 'mail'):
                saved = True
        yield mailbox, new, saved


def short_mailbox_names(mailboxes):
    """Shorten mailbox names.

        >>> from pprint import pprint
        >>> pprint(short_mailbox_names([('/path/to/mailbox/a', 1, 2),
        ...                             ('/path/to/mailbox/b', 3, 4),
        ...                             ('/path/to/mailbox/c/d', 5, 6),]))
        [('a', 1, 2), ('b', 3, 4), ('c/d', 5, 6)]

        >>> pprint(short_mailbox_names([('/path/to/mailbox/a', 1, 2),
        ...                             ('/path/to/mailbox/b', 3, 4),
        ...                             ('/path/to/other/x', 5, 6),]))
        [('mailbox/a', 1, 2), ('mailbox/b', 3, 4), ('other/x', 5, 6)]

        >>> pprint(short_mailbox_names([('/path/to/maildir/a', 1, 2),
        ...                             ('/path/to/maildir/b', 3, 4),
        ...                             ('/path/to/maildir/', 5, 6),]))
        [('a', 1, 2), ('b', 3, 4), ('INBOX', 5, 6)]

    """
    mailboxes = list(mailboxes) # deal with iterators properly
    if mailboxes:
        prefix = os.path.dirname(mailboxes[0][0])
        for mailbox, x, y in mailboxes:
            while not mailbox.startswith(prefix):
                prefix = os.path.dirname(prefix)
                if os.path.dirname(prefix) == prefix: # root
                    prefix = ''
        if prefix:
            count = len(prefix + os.sep)
            mailboxes = [(mailbox[count:] or 'INBOX', x, y)
                         for mailbox, x, y in mailboxes]
    return mailboxes


def terminal_width():
    """Return the current terminal width."""
    cols = 80
    try:
        import curses
    except ImportError:
        pass
    else:
        try:
            curses.setupterm()
            n = curses.tigetnum('cols')
            if n > 0:
                cols = n
        except (curses.error, TypeError):
            # the TypeError appears in doctests, when sys.stdout is a StringIO
            # object.  It says "TypeError: argument must be an int, or have a
            # fileno() method."
            pass
    return cols


def print_word_wrap(words, width=None):
    """Print words, wrapping them nicely.

        >>> print_word_wrap(['a', 'b', 'c'])
        a b c

        >>> print_word_wrap(['This', 'is', 'a', 'long', 'text'], 10)
        This is a
        long text

    """
    if not width:
        width = terminal_width()
    cur_width = 0
    for word in words:
        if cur_width and cur_width + len(word) > width:
            print
            cur_width = 0
        print word,
        cur_width += len(word) + 1
    if cur_width:
        print

def print_info(mailboxes):
    """Print concise information about mailboxes.

        >>> print_info([('a', True, 0)])
        New mail in a

        >>> print_info([('a', 0, 5)])
        Mail in a (5)

        >>> print_info([('a', True, 0), ('b', True, 0), ('c', 0, True)])
        New mail in a, b
        Mail in c

        >>> print_info([('a', 1, 0), ('b', 2, 5), ('c', 0, 3)])
        New mail in a (1), b (2+5)
        Mail in c (3)

    """
    new_mail = []
    saved_mail = []
    for mailbox, new, saved in mailboxes:
        if new is True:
            new_mail.append(mailbox)
        elif new and saved:
            new_mail.append(mailbox + ' (%d+%d)' % (new, saved))
        elif new:
            new_mail.append(mailbox + ' (%d)' % new)
        elif saved is True:
            saved_mail.append(mailbox)
        elif saved:
            saved_mail.append(mailbox + ' (%d)' % saved)
    if new_mail:
        print_word_wrap(["New mail in"]
                        + [word + ',' for word in new_mail[:-1]]
                        + new_mail[-1:])
    if saved_mail:
        print_word_wrap(["Mail in"]
                        + [word + ',' for word in saved_mail[:-1]]
                        + saved_mail[-1:])


def main(argv=sys.argv):
    """Main function."""
    if '--test' in argv:
        sys.exit(test())
    print_info(short_mailbox_names(parse_mailcheck(os.popen('mailcheck'))))


def test():
    """Run tests for this module."""
    import doctest
    nfail, ntests = doctest.testmod()
    if nfail == 0:
        print "All %d tests passed." % ntests


if __name__ == '__main__':
    main()
