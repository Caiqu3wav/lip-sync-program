import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from app.gui.main_window import MainWindow
from app.gui.splash_screen import SplashScreen
from app.gui.welcome_screen import WelcomeScreen


def main():
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    welcome_screen = WelcomeScreen()

    def launch_welcome_screen():
        splash.close()
        welcome_screen.show()
    
    QTimer.singleShot(1000, launch_welcome_screen)


    sys.exit(app.exec_())

if __name__ == "__main__":
        main()