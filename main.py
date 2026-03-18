import re
import sys
import os
import json

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from PySide6.QtWidgets import QApplication
from main_window import ScriptStudioWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScriptStudioWindow()
    window.show()
    sys.exit(app.exec())