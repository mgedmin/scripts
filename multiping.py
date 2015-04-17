#!/usr/bin/python
"""
Multiping version ${version} by Marius Gedminas <marius@gedmin.as>
Licence: GPL v2 or later

Syntax: multiping hostname

Pings a host every second and displays the results in an ncurses window.
Legend:
  #  ping OK
  %  ping OK, response is slow (over 1000 ms)
  -  ping not OK
  !  ping process killed (after 20 seconds)
  ?  cannot execute ping
Keys:
  q                quit
  k, up            scroll up
  j, down          scroll down
  ^U, page up      scroll page up
  ^D, page down    scroll page down
  g, home          scroll to top
  G, end           scroll to bottom
  ^L               redraw
"""
import sys
import curses
from threading import Thread
from time import time, strftime, localtime, sleep
import os

__version__ = '0.9.4'
__author__ = 'Marius Gedminas <marius@gedmin.as>'
__url__ = 'https://gist.github.com/mgedmin/b65af068e0d239fe9c66'
__licence__ = 'GPL v2 or later'


QUEUE_LEN = 20  # max number of outstanding ping subprocesses
                # so we won't fill up the OS pid table or something
                # (guess what event made me add this limitation? ;)

class Ping(Thread):

    def __init__(self, pinger, idx, hostname):
        Thread.__init__(self)
        self.setDaemon(1)
        self.pinger = pinger
        self.idx = idx
        self.hostname = hostname
        self.pid = None
        self.success = 0

    def run(self):
        start = time()
        self.pid = os.fork()
        if not self.pid:
            null = os.open('/dev/null', os.O_WRONLY)
            os.dup2(null, 1)
            os.dup2(null, 2)
            os.execlp('ping', 'ping', '-c', '1', '-n', '-q', self.hostname)
            sys.exit(99) # exec failed!
            return       # exit failed?!?!?
        status = os.waitpid(self.pid, 0)[1]
        self.pid = None
        delay = time() - start
        if os.WIFSIGNALED(status):
            result = '!'
        else:
            status = os.WEXITSTATUS(status)
            if status == 0:
                self.success = 1
                if delay > 1:
                    result = '%'
                else:
                    result = '#'
            elif status == 99:
                result = '?'
            else:
                result = '-'
        self.pinger.set(self.idx, result)

    def timeout(self, hard=False):
        if self.pid:
            # Note that self.pid may be set to None after the check above
            try:
                os.kill(self.pid, hard and 9 or 15)
            except (OSError, TypeError):
                pass


class Pinger(Thread):

    def __init__(self, hostname, interval):
        Thread.__init__(self)
        self.setDaemon(1)
        self.hostname = hostname
        self.interval = interval
        self.status = []
        self.version = 0
        self.running = 1
        self.started = -1
        self.sent = 0
        self.received = 0

    def run(self):
        self.started = last_time = time()
        idx = 0
        queue = []
        last_one = None
        while self.running:
            self.set(idx, '.')
            p = Ping(self, idx, self.hostname)
            queue.append(p)
            p.start()
            if len(queue) >= QUEUE_LEN:
                if last_one:
                    last_one.timeout(1)
                    self.sent += 1
                    if last_one.success:
                        self.received += 1
                last_one = queue.pop(0)
                last_one.timeout()
            # XXX sometimes this logic sleeps too much and skips one cell, why?
            to_sleep = (last_time + self.interval) - time()
            if to_sleep > 0:
                sleep(to_sleep)
            last_time = time()
            idx = max(idx + 1, int((last_time - self.started) / self.interval))

    def set(self, idx, result):
        while idx >= len(self.status):
            self.status.append(ord(' '))
        self.status[idx] = result
        self.version += 1

    def quit(self):
        self.running = 0


class UI:

    def __init__(self, win, y, x, width, height, pinger):
        self.win = win
        self.y = y
        self.x = x
        self.width = width
        self.height = height
        self.pinger = pinger
        self.version = -1
        self.autoscrolling = True

        self.row = 0

        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        self.RED = curses.color_pair(1) | curses.A_BOLD
        self.GREEN = curses.color_pair(2) | curses.A_BOLD
        self.DGREEN = curses.color_pair(2)
        curses.curs_set(0)

    def draw(self):
        win = self.win
        y = self.y
        x = self.x
        width = self.width
        height = self.height
        status = self.pinger.status
        interval = self.pinger.interval
        this_is_an_update = self.version != self.pinger.version
        self.version = self.pinger.version

        if self.pinger.sent > 0:
            loss = 100 - 100 * self.pinger.received / self.pinger.sent
            if loss > 0:
                win.addstr(y-1, x, "pinging %s: packet loss %d%%"
                                   % (hostname, int(loss)))
            else:
                win.addstr(y-1, x, "pinging %s" % hostname)
            win.clrtoeol()
        else:
            win.addstr(y-1, x, "pinging %s" % hostname)
            win.clrtoeol()

        if self.autoscroll() and this_is_an_update:
            self._scroll_to_bottom()
        pos = self.row * width
        if self.pinger.started != -1:
            pos -= int(self.pinger.started) % 60
        t = self.pinger.started + pos * interval
        while pos < len(status) and height > 0:
            win.addstr(y, x, strftime("%H:%M [", localtime(t)))
            for i in range(width):
                attr = curses.A_NORMAL
                if 0 <= pos < len(status):
                    ch = status[pos]
                    if ch in ('-', '?', '!'):
                        attr = self.RED
                    elif ch == '#':
                        attr = self.GREEN
                    elif ch == '%':
                        attr = self.DGREEN
                else:
                    ch = ord(" ")
                win.addch(ch, attr)
                pos += 1
            win.addstr("]")
            y += 1
            t += width * interval
            height -= 1
        if height > 0:
            win.move(y, x)
            win.clrtobot()

    def last_row_visible(self):
        max_pos = len(self.pinger.status)
        if self.pinger.started != -1:
            max_pos += int(self.pinger.started) % 60
        pos_just_past_the_screen = (self.row + self.height) * self.width
        return pos_just_past_the_screen - self.width <= max_pos < pos_just_past_the_screen

    def autoscroll(self):
        if not self.autoscrolling:
            return False
        # autoscroll only if the bottom row was visible and is no longer
        pos_just_past_the_screen = (self.row + self.height) * self.width
        max_pos = len(self.pinger.status)
        if self.pinger.started != -1:
            max_pos += int(self.pinger.started) % 60
        return pos_just_past_the_screen <= max_pos - 1

    def update(self):
        if self.version != self.pinger.version:
            try:
                self.draw()
            except curses.error:
                # let's hope it's just a momentary glitch due to a temporarily
                # reduced window size or something
                pass
            return 1
        else:
            return 0

    def scroll(self, delta):
        self.row += delta
        self.row = max(self.row, 1 - self.height)

        max_pos = len(self.pinger.status)
        if self.pinger.started != -1:
            max_pos += int(self.pinger.started) % 60
        self.row = min(self.row, int((max_pos - 1) / self.width))
        self.autoscrolling = self.last_row_visible()
        self.draw()

    def scroll_to_top(self):
        self.row = 0
        self.autoscrolling = self.last_row_visible()
        self.draw()

    def _scroll_to_bottom(self):
        max_pos = len(self.pinger.status)
        if self.pinger.started != -1:
            max_pos += int(self.pinger.started) % 60
        self.row = max(0, int((max_pos - 1) / self.width) - self.height + 1)

    def scroll_to_bottom(self):
        self._scroll_to_bottom()
        self.autoscrolling = True
        self.draw()

    def resize(self, new_height):
        self.height = new_height
        if self.autoscrolling:
            self._scroll_to_bottom()
        self.scroll(0)


def main(stdscr, hostname, interval=1):
    stdscr.addstr(0, 0, "pinging %s" % hostname)
    pinger = Pinger(hostname, interval)
    pinger.start()
    ui = UI(stdscr, 1, 0, 60, curses.LINES - 1, pinger)
    ui.draw()
    stdscr.refresh()
    curses.halfdelay(interval * 5)
    while 1:
        c = stdscr.getch()
        if ui.update():
            stdscr.refresh()
        if c == ord('q'):
            pinger.quit()
            return
        elif c == curses.KEY_RESIZE:
            ui.resize(stdscr.getmaxyx()[0] - 1)
            stdscr.refresh()
        elif c == 12: # ^L
            stdscr.clear()
            ui.draw()
            stdscr.refresh()
        elif c in (ord('k'), curses.KEY_UP):
            ui.scroll(-1)
            stdscr.refresh()
        elif c in (ord('j'), curses.KEY_DOWN):
            ui.scroll(1)
            stdscr.refresh()
        elif c in (ord('U') - ord('@'), curses.KEY_PPAGE):
            ui.scroll(1 - ui.height)
            stdscr.refresh()
        elif c in (ord('D') - ord('@'), curses.KEY_NPAGE):
            ui.scroll(ui.height - 1)
            stdscr.refresh()
        elif c in (ord('g'), curses.KEY_HOME):
            ui.scroll_to_top()
            stdscr.refresh()
        elif c in (ord('G'), curses.KEY_END):
            ui.scroll_to_bottom()
            stdscr.refresh()
        elif c == ord('f'):     # fake ping response for debugging
            pinger.status.append('F')
            ui.draw()
            stdscr.refresh()
        elif c == ord('F'):     # fake ping response for debugging
            pinger.status.extend(['F'] * 60 * 10)
            ui.draw()
            stdscr.refresh()

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.replace('${version}', __version__))
        sys.exit(0)
    hostname = sys.argv[1]
    curses.wrapper(main, hostname)
