# downloader.py
import os
import tempfile

import requests
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

# --- NEW: Create a single, global session object ---
# This allows for connection pooling and proper resource management.
SESSION = requests.Session()


class DownloadThreadPool(QThreadPool):
    """A thin wrapper around QThreadPool to manage global download tasks."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMaxThreadCount(4)
        # --- NEW: Keep track of active runners ---
        self._runners = []

    # --- NEW: Override start to track runners ---
    def start(self, runner, priority=0):
        """Adds a runner to the tracking list before starting it."""
        self._runners.append(runner)
        # When the runner is finished, its notifier will be destroyed.
        # We connect to that to clean up our list.
        runner.notifier.destroyed.connect(lambda: self._remove_runner(runner))
        super().start(runner, priority)

    def _remove_runner(self, runner):
        """Safely removes a runner from the tracking list."""
        try:
            self._runners.remove(runner)
        except ValueError:
            pass  # The runner might have already been removed.

    # --- NEW: A proper shutdown method ---
    def shutdown(self):
        """Signals all active runners to abort and closes the session."""
        print("Downloader: Closing session and aborting runners.")
        # --- NEW: Close the session to release all connections ---
        SESSION.close()

        # Abort runners. Because the session is closed, any ongoing
        # requests should fail quickly, allowing runners to exit.
        for runner in list(self._runners):
            runner.abort()
        self.clear()


class _Notifier(QObject):
    """A helper class to emit signals from a QRunnable."""

    download_succeeded = Signal(bytes)
    download_failed = Signal(str)


class DownloadRunner(QRunnable):
    """A runnable task to download a single file."""

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.notifier = _Notifier()
        self.is_aborted = False

    @Slot()
    def abort(self):
        """Sets a flag to stop the runner's execution."""
        self.is_aborted = True

    def run(self):
        """The main work of the runner, executed on a background thread."""
        if self.is_aborted:
            return

        _, temp_path = tempfile.mkstemp(suffix=".png")

        try:
            # --- NEW: Use the global session object ---
            response = SESSION.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.is_aborted:
                        return
                    f.write(chunk)

            if self.is_aborted:
                return

            with open(temp_path, "rb") as f:
                image_data = f.read()
            self.notifier.download_succeeded.emit(image_data)

        except requests.exceptions.RequestException as e:
            # When the session is closed, this exception is expected.
            if not self.is_aborted:
                print(f"Failed to download {self.url}: {e}")
                self.notifier.download_failed.emit(str(e))
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass


GLOBAL_DOWNLOAD_POOL = DownloadThreadPool()
