"""An implementation of a file locker."""

# Import msvcrt if possible.
try:
    import msvcrt
except ImportError:
    # Currently no linux solution with fcntl.
    raise RuntimeError('Linux locker not written yet.')
else:
    class FileLock(object):
        def __init__(self, fd, size=65536):
            if hasattr(fd, 'fileno') and callable(fd.fileno):
                self.fd = fd.fileno()
            else:
                self.fd = fd
            self.size = size

        def acquire(self, blocking=True):
            msvcrt.locking(self.fd, (msvcrt.LK_NBLCK, msvcrt.LK_LOCK)[blocking], self.size)

        def release(self):
            msvcrt.locking(self.fd, msvcrt.LK_UNLCK, self.size)

        def __enter__(self):
            self.acquire()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.release()
