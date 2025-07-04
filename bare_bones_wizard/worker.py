# worker.py
import time

from PySide6.QtCore import QObject, Signal


class Worker(QObject):
    """
    A worker object that performs a task in a separate thread.
    Inherits from QObject to allow signal/slot communication.
    """

    # Signal to emit when work is done. The list argument will carry our results.
    work_finished = Signal(list)

    def do_work(self):
        """
        The main task for the worker. This method will be executed in the background thread.
        """
        print("Worker thread: Starting a long task...")
        # Simulate a 3-second task, like fetching data from a server.
        time.sleep(3)

        # Simulate the results we got from the task.
        results = [
            {"id": 1, "name": "Project Alpha"},
            {"id": 2, "name": "Project Beta"},
            {"id": 3, "name": "Project Gamma"},
            {"id": 4, "name": "Project Delta"},
        ]

        print("Worker thread: Task complete. Emitting results.")
        # Emit the signal to send the results back to the main UI thread.
        self.work_finished.emit(results)
