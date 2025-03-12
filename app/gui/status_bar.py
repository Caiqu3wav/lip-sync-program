from PyQt5.QtWidgets import QStatusBar, QLabel, QProgressBar, QHBoxLayout, QWidget

class StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        
        # Create a status label
        self.status_label = QLabel("Ready")
        self.addWidget(self.status_label, 1)
        
        # Create a progress container
        progress_container = QWidget()
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a progress label
        self.progress_label = QLabel("Progress:")
        progress_layout.addWidget(self.progress_label)
        
        # Create a progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)  # Hide initially
        progress_layout.addWidget(self.progress_bar)
        
        # Add the progress container to the status bar
        self.addPermanentWidget(progress_container)
    
    def set_status(self, message):
        """Set the status message"""
        self.status_label.setText(message)
    
    def show_progress(self, value=0):
        """Show the progress bar with the given value"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
    
    def hide_progress(self):
        """Hide the progress bar"""
        self.progress_bar.setVisible(False)


# For testing the component individually
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow
    app = QApplication(sys.argv)
    window = QMainWindow()
    status_bar = StatusBar()
    window.setStatusBar(status_bar)
    window.resize(500, 100)
    window.show()
    sys.exit(app.exec_())