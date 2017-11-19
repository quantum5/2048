import os
import errno
import itertools
from threading import Event, Thread

from .lock import FileLock
from .utils import write_to_disk


class GameManager(object):
    def __init__(self, cls, screen, high_score_file, file_name):
        # Stores the initialization status as this might crash.
        self.created = False

        self.score_name = high_score_file
        self.screen = screen
        self.save_name = file_name
        self.game_class = cls

        self._score_changed = False
        self._running = True

        self._change_event = Event()
        self._saved_event = Event()

        try:
            self.score_fd = self.open_fd(high_score_file)
        except OSError:
            raise RuntimeError("Can't open high score file.")
        self.score_file = os.fdopen(self.score_fd, 'r+')
        self.score_lock = FileLock(self.score_fd)

        with self.score_lock:
            try:
                self._score = self._load_score()
            except ValueError:
                self._score = 0
                self._score_changed = True
                self.save()

        # Try opening save files from zero and counting up.
        for i in itertools.count(0):
            name = file_name % (i,)
            try:
                save = self.open_fd(name)
            except IOError:
                continue
            else:
                self.save_lock = FileLock(save)
                try:
                    self.save_lock.acquire(False)
                except IOError:
                    del self.save_lock
                    os.close(save)
                    continue

                self.save_fd = save
                self.save_file = os.fdopen(save, 'r+')

                read = self.save_file.read()
                if read:
                    self.game = self.game_class.from_save(read, self, screen)
                else:
                    self.new_game()
                self.save_file.seek(0, os.SEEK_SET)

                print('Running as instance #%d.' % (i,))
                break

        self._worker = Thread(target=self._save_daemon)
        self._worker.start()

        self._saved_event.set()

        self.created = True

    @classmethod
    def open_fd(cls, name):
        """Open a file or create it."""
        # Try to create it, if can't, try to open.
        try:
            return os.open(name, os.O_CREAT | os.O_RDWR | os.O_EXCL)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            return os.open(name, os.O_RDWR | os.O_EXCL)

    def new_game(self):
        """Creates a new game of 2048."""
        self.game = self.game_class(self, self.screen)
        self.save()

    def _load_score(self):
        """Load the best score from file."""
        score = int(self.score_file.read())
        self.score_file.seek(0, os.SEEK_SET)
        return score

    def got_score(self, score):
        """Update the best score if the new score is higher, returning the change."""
        if score > self._score:
            delta = score - self._score
            self._score = score
            self._score_changed = True
            self.save()
            return delta
        return 0

    @property
    def score(self):
        return self._score

    def save(self):
        self._saved_event.clear()
        self._change_event.set()

    def _save_daemon(self):
        while self._running:
            self._change_event.wait()
            if self._score_changed:
                with self.score_lock:
                    try:
                        score = self._load_score()
                        self._score = max(score, self._score)
                    except ValueError:
                        pass
                    self.score_file.write(str(self._score))
                    self.score_file.truncate()
                    self.score_file.seek(0, os.SEEK_SET)
                    write_to_disk(self.score_file)
                    self._score_changed = False
            if self.game.lost:
                self.save_file.truncate()
            else:
                self.save_file.write(self.game.serialize())
                self.save_file.truncate()
                self.save_file.seek(0, os.SEEK_SET)

            write_to_disk(self.save_file)
            self._change_event.clear()
            self._saved_event.set()

    def close(self):
        if self.created:
            self._running = False
            self._saved_event.wait()
            self.save()
            self._worker.join()
            self.save_lock.release()
            self.score_file.close()
            self.save_file.close()
            self.created = False

    __del__ = close

    def dispatch(self, event):
        self.game.on_event(event)

    def draw(self):
        self.game.on_draw()
