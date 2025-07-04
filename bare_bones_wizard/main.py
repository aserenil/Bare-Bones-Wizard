# main.py
import sys
from enum import Enum, auto

from card_widget import CardWidget
from PySide6.QtCore import Qt, QThread, Slot
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from worker import Worker

# Note: The downloader module is no longer needed.


class WizardStep(Enum):
    WELCOME = auto()
    PROCESSING = auto()
    RESULTS = auto()
    FINAL = auto()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bare Bones Wizard")
        self.setGeometry(200, 200, 500, 600)

        self.results_data = None
        self.worker_thread = None
        self.worker = None
        self.selected_card = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.wizard = QStackedWidget()
        main_layout.addWidget(self.wizard)

        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.next_button = QPushButton("Next")
        nav_layout.addStretch()
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.next_button)
        main_layout.addLayout(nav_layout)

        self._create_pages()

        self.next_button.clicked.connect(self.go_to_next_step)
        self.back_button.clicked.connect(self.go_to_previous_step)
        self.wizard.currentChanged.connect(self.update_ui_for_step)

        self.current_step_index = 0
        self.steps = list(WizardStep)
        self.wizard.setCurrentIndex(self.current_step_index)

    def _create_pages(self):
        welcome_page = QLabel("Welcome! Click Next to begin a simulated process.")
        welcome_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wizard.addWidget(welcome_page)

        processing_page = QLabel("Simulating work... Please wait.")
        processing_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wizard.addWidget(processing_page)

        self.results_page = QWidget()
        results_layout = QVBoxLayout(self.results_page)
        results_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        results_layout.addWidget(scroll_area)
        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.card_container)
        self.wizard.addWidget(self.results_page)

        self.final_page_label = QLabel("Process Complete!")
        self.final_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wizard.addWidget(self.final_page_label)

    def go_to_next_step(self):
        current_step = self.steps[self.current_step_index]

        if current_step == WizardStep.WELCOME:
            self.wizard.setCurrentIndex(WizardStep.PROCESSING.value - 1)
            self.worker_thread = QThread()
            self.worker = Worker()
            self.worker.moveToThread(self.worker_thread)
            self.worker_thread.started.connect(self.worker.do_work)
            self.worker.work_finished.connect(self.on_work_finished)
            self.worker.work_finished.connect(self.worker_thread.quit)
            self.worker_thread.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.finished.connect(self.on_thread_finished)
            self.worker_thread.start()
            return

        if current_step == WizardStep.RESULTS and self.selected_card:
            self.on_card_chosen(self.selected_card.item_data)
            return

        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            self.wizard.setCurrentIndex(self.current_step_index)

    def go_to_previous_step(self):
        """Handles the logic for the 'Back' button."""
        current_step = self.steps[self.current_step_index]

        # --- THE FIX: Special handling for going back ---
        if current_step == WizardStep.RESULTS:
            self._clear_cards()
            # Explicitly jump back to the WELCOME page, skipping PROCESSING.
            self.wizard.setCurrentIndex(WizardStep.WELCOME.value - 1)
            return

        if current_step == WizardStep.FINAL:
            self.final_page_label.setText("Process Complete!")

        # Standard back logic for other pages
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.wizard.setCurrentIndex(self.current_step_index)

    def on_work_finished(self, results):
        self.results_data = results
        self.populate_results_page()
        self.wizard.setCurrentIndex(WizardStep.RESULTS.value - 1)

    def populate_results_page(self):
        self._clear_cards()
        if self.results_data:
            for item in self.results_data:
                card = CardWidget(item)
                card.selected.connect(self.on_card_selected)
                card.chosen.connect(self.on_card_chosen)
                self.card_layout.addWidget(card)

    def _clear_cards(self):
        self.selected_card = None
        while self.card_layout.count():
            child = self.card_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    @Slot(object)
    def on_card_selected(self, card_widget):
        if self.selected_card:
            self.selected_card.unselect_card()
        self.selected_card = card_widget
        self.selected_card.select_card()
        self.next_button.setEnabled(True)

    @Slot(dict)
    def on_card_chosen(self, item_data):
        print(f"Final item chosen: {item_data['name']}")
        self.final_page_label.setText(f"You chose:\n{item_data['name']}")
        self.wizard.setCurrentIndex(WizardStep.FINAL.value - 1)

    def on_thread_finished(self):
        self.worker = None
        self.worker_thread = None

    def update_ui_for_step(self, index):
        self.current_step_index = index
        current_step = self.steps[index]

        if current_step == WizardStep.WELCOME:
            self.back_button.hide()
            self.next_button.show()
        elif current_step == WizardStep.PROCESSING:
            self.back_button.hide()
            self.next_button.hide()
        elif current_step == WizardStep.RESULTS:
            self.back_button.show()
            self.next_button.show()
            self.next_button.setEnabled(bool(self.selected_card))
        elif current_step == WizardStep.FINAL:
            self.back_button.show()
            self.next_button.hide()
        else:
            self.back_button.show()
            self.next_button.show()

    def closeEvent(self, event):
        """The window is closing. We just accept it."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
