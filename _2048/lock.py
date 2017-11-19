class FileLockBase(object):
    def __init__(self, fd):
        if hasattr(fd, 'fileno') and callable(fd.fileno):
            self.fd = fd.fileno()
        else:
            self.fd = fd

    def acquire(self, blocking=True):
        raise NotImplementedError()

    def release(self):
        raise NotImplementedError()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


try:
    import msvcrt
except ImportError:
    import fcntl
    import os

    class FileLock(FileLockBase):
        def acquire(self, blocking=True):
            fcntl.flock(self.fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))

        def release(self):
            fcntl.flock(self.fd, fcntl.LOCK_UN)
else:
    class FileLock(FileLockBase):
        def acquire(self, blocking=True):
            msvcrt.locking(self.fd, (msvcrt.LK_NBLCK, msvcrt.LK_LOCK)[blocking], 2147483647)

        def release(self):
            msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 2147483647)
