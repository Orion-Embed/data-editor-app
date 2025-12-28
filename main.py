#!/usr/bin/env python3
"""
Database Editor - Main Application
A visual SQLite database editor built with PySide6
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QPushButton, QLabel, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPalette, QColor

# Import our modules
from database import DatabaseManager
from editor_window import EditorWindow


class MainWindow(QMainWindow):
    """Main application window with New, Open, Quit buttons"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_styles()
        self.db_manager = DatabaseManager()
        
    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("Database Editor")
        self.setGeometry(100, 100, 500, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title_label = QLabel("Database Editor")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 30px;")
        
        # Subtitle
        subtitle_label = QLabel("Manage SQLite databases with ease")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; font-size: 14px; margin-bottom: 40px;")
        
        # Buttons
        self.new_btn = self.create_button("New Database", "#27ae60", "icons/add.svg")
        self.open_btn = self.create_button("Open Database", "#3498db", "icons/open.svg")
        self.quit_btn = self.create_button("Quit", "#e74c3c", "icons/quit.svg")
        
        # Recent files section
        recent_label = QLabel("Recent Files:")
        recent_label.setStyleSheet("color: #95a5a6; margin-top: 40px;")
        
        self.recent_list = QLabel("No recent files")
        self.recent_list.setStyleSheet("""
            color: #7f8c8d;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
        """)
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addWidget(self.new_btn)
        layout.addWidget(self.open_btn)
        layout.addWidget(self.quit_btn)
        layout.addStretch()
        layout.addWidget(recent_label)
        layout.addWidget(self.recent_list)
        
        # Connect signals
        self.new_btn.clicked.connect(self.create_new_database)
        self.open_btn.clicked.connect(self.open_database)
        self.quit_btn.clicked.connect(self.close)
        
    def create_button(self, text, color, icon_path=None):
        """Create a styled button"""
        btn = QPushButton(text)
        btn.setMinimumHeight(50)
        
        style = f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 40)};
            }}
        """
        
        btn.setStyleSheet(style)
        
        if icon_path and os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(24, 24))
        
        return btn
    
    def darken_color(self, hex_color, percent=20):
        """Darken a hex color by percentage"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        r = max(0, r - (r * percent // 100))
        g = max(0, g - (g * percent // 100))
        b = max(0, b - (b * percent // 100))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def setup_styles(self):
        """Setup application-wide styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
    def create_new_database(self):
        """Create a new database file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Create New Database",
            str(Path.home() / "new_database.db"),
            "SQLite Databases (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        
        if file_path:
            try:
                # Create database
                self.db_manager.create_database(file_path)
                
                # Open editor window
                self.open_editor(file_path)
                
                # Update recent files
                self.update_recent_files(file_path)
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create database:\n{str(e)}"
                )
    
    def open_database(self):
        """Open an existing database file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Database",
            str(Path.home()),
            "SQLite Databases (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        
        if file_path:
            try:
                # Verify it's a valid SQLite database
                if not self.db_manager.is_valid_database(file_path):
                    QMessageBox.warning(
                        self,
                        "Invalid File",
                        "The selected file is not a valid SQLite database."
                    )
                    return
                
                # Open editor window
                self.open_editor(file_path)
                
                # Update recent files
                self.update_recent_files(file_path)
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to open database:\n{str(e)}"
                )
    
    def open_editor(self, file_path):
        """Open the editor window with the specified database"""
        self.editor = EditorWindow(file_path, self.db_manager)
        self.editor.show()
        self.hide()  # Hide main window
    
    def update_recent_files(self, file_path):
        """Update the recent files display"""
        # Load recent files from config/settings
        recent_text = os.path.basename(file_path) + "\n"
        recent_text += "Click 'Open' to browse for other files"
        self.recent_list.setText(recent_text)
    
    def closeEvent(self, event):
        """Handle application close"""
        reply = QMessageBox.question(
            self,
            "Quit",
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Close database connection if open
            self.db_manager.close_connection()
            event.accept()
        else:
            event.ignore()


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Database Editor")
    app.setOrganizationName("DatabaseEditor")
    
    # Set application icon if available
    if os.path.exists("icons/app.png"):
        app.setWindowIcon(QIcon("icons/app.png"))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
