from threading import currentThread, enumerate, Lock
from time import strftime
from textwrap import fill


class Logger:
    def __init__(self, width=500, lock=None, debug=True):
        self.width = width
        self._lock = lock if lock else Lock()
        self._debug = debug

    def log(self, message, isError=False):
        with self.lock:
            self._log(message, isError)

    def debug(self, message, isError=False):
        if not self._debug:
            return
        with self.lock:
            self._log(message, isError)

    def _log(self, message, isError=False):
        print(
            fill(f"[{' +' if not isError else '-'} {strftime('%Y/%m/%d %H:%M:%S')}]"
                 f"[{currentThread().name} / {len(enumerate())}] {str(message).strip('.').capitalize()}.",
                 self.width, subsequent_indent="\t", replace_whitespace=False))

    @property
    def lock(self):
        return self._lock