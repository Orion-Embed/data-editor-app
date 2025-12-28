"""
Editor Window - Main database editing interface
"""

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                              QTreeWidget, QTreeWidgetItem, QTabWidget, QSplitter,
                              QTextEdit, QStatusBar, QToolBar, QMenuBar, QMenu,
                              QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
                              QComboBox, QCheckBox, QSpinBox, QMessageBox,
                              QHeaderView, QFileDialog, QInputDialog, QApplication)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont

from database import DatabaseManager


class EditorWindow(QMainWindow):
    """Main editor window for database operations"""
    
    def __init__(self, file_path: str, db_manager: DatabaseManager):
        super().__init__()
        self.file_path = file_path
        self.db_manager = db_manager
        self.current_table = None
        self.unsaved_changes = False
        
        # Open database
        if not self.db_manager.open_database(file_path):
            QMessageBox.critical(self, "Error", "Failed to open database")
            self.close()
            return
        
        self.setup_ui()
        self.load_tables()
        self.setup_shortcuts()
        
    def setup_ui(self):
        """Setup the editor window UI"""
        self.setWindowTitle(f"Database Editor - {os.path.basename(self.file_path)}")
        self.setGeometry(200, 200, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create splitter for left sidebar and main area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left sidebar (tables and controls)
        sidebar = self.create_sidebar()
        
        # Main area (tabs for table data and SQL editor)
        main_area = self.create_main_area()
        
        splitter.addWidget(sidebar)
        splitter.addWidget(main_area)
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter)
        
        # Setup menu bar
        self.setup_menu_bar()
        
        # Setup toolbar
        self.setup_toolbar()
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Connected to: {os.path.basename(self.file_path)}")
        
    def create_sidebar(self) -> QWidget:
        """Create the left sidebar with tables and controls"""
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Tables")
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-bottom: 1px solid #e0e0e0;
        """)
        
        # Table tree
        self.table_tree = QTreeWidget()
        self.table_tree.setHeaderLabel("Tables")
        self.table_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        self.table_tree.itemClicked.connect(self.on_table_selected)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.add_table_btn = QPushButton("+ Table")
        self.add_table_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #219955;
            }
        """)
        self.add_table_btn.clicked.connect(self.add_table)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_tables)
        
        btn_layout.addWidget(self.add_table_btn)
        btn_layout.addWidget(self.refresh_btn)
        
        # Add widgets to sidebar
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addWidget(self.table_tree)
        sidebar_layout.addLayout(btn_layout)
        
        return sidebar
    
    def create_main_area(self) -> QWidget:
        """Create the main editing area with tabs"""
        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        
        # Add tabs
        self.data_tab = QWidget()
        self.setup_data_tab()
        
        self.sql_tab = QWidget()
        self.setup_sql_tab()
        
        self.tab_widget.addTab(self.data_tab, "Data")
        self.tab_widget.addTab(self.sql_tab, "SQL Editor")
        
        main_layout.addWidget(self.tab_widget)
        
        return main_area
    
    def setup_data_tab(self):
        """Setup the data viewing/editing tab"""
        layout = QVBoxLayout(self.data_tab)
        
        # Table controls
        controls_layout = QHBoxLayout()
        
        self.add_row_btn = QPushButton("Add Row")
        self.add_row_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.add_row_btn.clicked.connect(self.add_row)
        self.add_row_btn.setEnabled(False)
        
        self.delete_row_btn = QPushButton("Delete Row")
        self.delete_row_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.delete_row_btn.clicked.connect(self.delete_row)
        self.delete_row_btn.setEnabled(False)
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setEnabled(False)
        
        controls_layout.addWidget(self.add_row_btn)
        controls_layout.addWidget(self.delete_row_btn)
        controls_layout.addWidget(self.save_btn)
        controls_layout.addStretch()
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        self.data_table.cellChanged.connect(self.on_cell_changed)
        self.data_table.itemSelectionChanged.connect(self.on_row_selected)
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        
        self.prev_page_btn = QPushButton("← Previous")
        self.next_page_btn = QPushButton("Next →")
        self.page_label = QLabel("Page 1")
        
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.next_page_btn.clicked.connect(self.next_page)
        
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_page_btn)
        pagination_layout.addStretch()
        
        # Add to layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.data_table)
        layout.addLayout(pagination_layout)
        
        # Initialize pagination
        self.current_page = 1
        self.page_size = 50
        self.total_rows = 0
    
    def setup_sql_tab(self):
        """Setup the SQL editor tab"""
        layout = QVBoxLayout(self.sql_tab)
        
        # SQL input
        self.sql_editor = QTextEdit()
        self.sql_editor.setPlaceholderText("Enter SQL query here...")
        self.sql_editor.setStyleSheet("""
            QTextEdit {
                font-family: 'Monospace';
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        # SQL controls
        sql_controls = QHBoxLayout()
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.execute_btn.clicked.connect(self.execute_sql)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_sql)
        
        sql_controls.addWidget(self.execute_btn)
        sql_controls.addWidget(self.clear_btn)
        sql_controls.addStretch()
        
        # Results table
        self.results_table = QTableWidget()
        
        # Add to layout
        layout.addWidget(self.sql_editor)
        layout.addLayout(sql_controls)
        layout.addWidget(self.results_table)
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Database", self)
        new_action.triggered.connect(self.new_database)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Database", self)
        open_action.triggered.connect(self.open_database)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_changes)
        file_menu.addAction(save_action)
        
        export_action = QAction("Export to CSV...", self)
        export_action.triggered.connect(self.export_to_csv)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        add_column_action = QAction("Add Column", self)
        add_column_action.triggered.connect(self.add_column)
        edit_menu.addAction(add_column_action)
        
        edit_menu.addSeparator()
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self.refresh_tables)
        edit_menu.addAction(refresh_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        toggle_sidebar_action = QAction("Toggle Sidebar", self)
        toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Setup the toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Add table action
        add_table_action = QAction(QIcon("icons/add.svg"), "Add Table", self)
        add_table_action.triggered.connect(self.add_table)
        toolbar.addAction(add_table_action)
        
        toolbar.addSeparator()
        
        # Save action
        save_action = QAction(QIcon("icons/save.svg"), "Save", self)
        save_action.triggered.connect(self.save_changes)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Add row action
        add_row_action = QAction(QIcon("icons/row_add.svg"), "Add Row", self)
        add_row_action.triggered.connect(self.add_row)
        toolbar.addAction(add_row_action)
        
        # Delete row action
        delete_row_action = QAction(QIcon("icons/row_delete.svg"), "Delete Row", self)
        delete_row_action.triggered.connect(self.delete_row)
        toolbar.addAction(delete_row_action)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Save with Ctrl+S
        save_shortcut = QAction(self)
        save_shortcut.setShortcut(QKeySequence.StandardKey.Save)
        save_shortcut.triggered.connect(self.save_changes)
        self.addAction(save_shortcut)
        
        # Refresh with F5
        refresh_shortcut = QAction(self)
        refresh_shortcut.setShortcut(QKeySequence("F5"))
        refresh_shortcut.triggered.connect(self.refresh_tables)
        self.addAction(refresh_shortcut)
        
        # Execute SQL with Ctrl+Enter
        execute_shortcut = QAction(self)
        execute_shortcut.setShortcut(QKeySequence("Ctrl+Return"))
        execute_shortcut.triggered.connect(self.execute_sql)
        self.addAction(execute_shortcut)
    
    def load_tables(self):
        """Load all tables from database"""
        self.table_tree.clear()
        
        tables = self.db_manager.get_tables()
        for table in tables:
            item = QTreeWidgetItem([table])
            self.table_tree.addTopLevelItem(item)
        
        if tables:
            self.table_tree.setCurrentItem(self.table_tree.topLevelItem(0))
            self.on_table_selected(self.table_tree.topLevelItem(0), 0)
    
    def on_table_selected(self, item, column):
        """Handle table selection"""
        table_name = item.text(0)
        self.current_table = table_name
        self.load_table_data(table_name)
        
        # Enable buttons that require a table
        self.add_row_btn.setEnabled(True)
        self.save_btn.setEnabled(self.unsaved_changes)
        
        # Update status bar
        self.status_bar.showMessage(f"Viewing table: {table_name}")
    
    def load_table_data(self, table_name: str):
        """Load data from the selected table"""
        # Get table schema
        schema = self.db_manager.get_table_schema(table_name)
        
        # Clear table
        self.data_table.clear()
        
        # Set column headers
        column_names = [col['name'] for col in schema]
        self.data_table.setColumnCount(len(column_names))
        self.data_table.setHorizontalHeaderLabels(column_names)
        
        # Get data
        offset = (self.current_page - 1) * self.page_size
        data, self.total_rows = self.db_manager.get_table_data(
            table_name, self.page_size, offset
        )
        
        # Populate table
        self.data_table.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, col_name in enumerate(column_names):
                value = row_data.get(col_name, "")
                item = QTableWidgetItem(str(value))
                
                # Make primary key columns non-editable
                if schema[col_idx].get('pk'):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(Qt.GlobalColor.lightGray)
                
                self.data_table.setItem(row_idx, col_idx, item)
        
        # Update pagination
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page}/{total_pages}")
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)
        
        # Resize columns to content
        self.data_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
    
    def on_cell_changed(self, row, column):
        """Handle cell changes"""
        self.unsaved_changes = True
        self.save_btn.setEnabled(True)
        
        # Update status bar
        column_name = self.data_table.horizontalHeaderItem(column).text()
        self.status_bar.showMessage(f"Modified: {column_name} in row {row + 1}")
    
    def on_row_selected(self):
        """Handle row selection"""
        selected_rows = self.data_table.selectionModel().selectedRows()
        self.delete_row_btn.setEnabled(len(selected_rows) > 0)
    
    def add_table(self):
        """Open dialog to add a new table"""
        dialog = AddTableDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            table_name, columns = dialog.get_results()
            
            if table_name and columns:
                success = self.db_manager.create_table(table_name, columns)
                if success:
                    self.load_tables()
                    self.status_bar.showMessage(f"Table '{table_name}' created successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to create table")
    
    def add_column(self):
        """Add a new column to the current table"""
        if not self.current_table:
            QMessageBox.warning(self, "No Table Selected", "Please select a table first")
            return
        
        dialog = AddColumnDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            column_name, column_type, default_value = dialog.get_results()
            
            if column_name:
                success = self.db_manager.add_column(
                    self.current_table, column_name, column_type, default_value
                )
                if success:
                    self.load_table_data(self.current_table)
                    self.status_bar.showMessage(f"Column '{column_name}' added")
                else:
                    QMessageBox.warning(self, "Error", "Failed to add column")
    
    def add_row(self):
        """Add a new empty row to the current table"""
        if not self.current_table:
            return
        
        # Get table schema
        schema = self.db_manager.get_table_schema(self.current_table)
        
        # Create empty row data
        row_data = {}
        for col in schema:
            if not col.get('pk'):  # Skip primary key (auto-increment)
                row_data[col['name']] = ""
        
        # Insert row
        row_id = self.db_manager.insert_row(self.current_table, row_data)
        if row_id != -1:
            # Reload table data
            self.load_table_data(self.current_table)
            self.unsaved_changes = False
            self.save_btn.setEnabled(False)
            self.status_bar.showMessage(f"Row added with ID: {row_id}")
        else:
            QMessageBox.warning(self, "Error", "Failed to add row")
    
    def delete_row(self):
        """Delete selected row(s)"""
        if not self.current_table:
            return
        
        selected_rows = self.data_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Rows",
            f"Delete {len(selected_rows)} selected row(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Get primary key column (assuming it's the first column)
            schema = self.db_manager.get_table_schema(self.current_table)
            pk_column = None
            for col in schema:
                if col.get('pk'):
                    pk_column = col['name']
                    break
            
            if not pk_column:
                QMessageBox.warning(self, "Error", "No primary key column found")
                return
            
            # Delete each selected row
            for index in selected_rows:
                row = index.row()
                row_id = self.data_table.item(row, 0).text()
                
                try:
                    row_id_int = int(row_id)
                    success = self.db_manager.delete_row(
                        self.current_table, row_id_int, pk_column
                    )
                    if not success:
                        QMessageBox.warning(self, "Error", f"Failed to delete row {row_id}")
                except ValueError:
                    QMessageBox.warning(self, "Error", f"Invalid row ID: {row_id}")
            
            # Reload table data
            self.load_table_data(self.current_table)
            self.status_bar.showMessage(f"Deleted {len(selected_rows)} row(s)")
    
    def save_changes(self):
        """Save all changes to the database"""
        if not self.current_table or not self.unsaved_changes:
            return
        
        # Get table schema to identify primary key
        schema = self.db_manager.get_table_schema(self.current_table)
        pk_column = None
        for col in schema:
            if col.get('pk'):
                pk_column = col['name']
                break
        
        if not pk_column:
            QMessageBox.warning(self, "Error", "No primary key column found")
            return
        
        # Update each modified row
        updated_count = 0
        for row in range(self.data_table.rowCount()):
            row_id = self.data_table.item(row, 0).text()
            
            try:
                row_id_int = int(row_id)
                row_data = {}
                
                # Collect data for this row
                for col_idx in range(self.data_table.columnCount()):
                    col_name = self.data_table.horizontalHeaderItem(col_idx).text()
                    
                    # Skip primary key column
                    if col_name == pk_column:
                        continue
                    
                    item = self.data_table.item(row, col_idx)
                    if item:
                        row_data[col_name] = item.text()
                
                # Update row in database
                if row_data:
                    success = self.db_manager.update_row(
                        self.current_table, row_id_int, row_data, pk_column
                    )
                    if success:
                        updated_count += 1
                        
            except ValueError:
                continue
        
        # Reset unsaved changes flag
        self.unsaved_changes = False
        self.save_btn.setEnabled(False)
        
        # Show success message
        self.status_bar.showMessage(f"Saved {updated_count} row(s)")
        QMessageBox.information(
            self,
            "Changes Saved",
            f"Successfully saved {updated_count} row(s) to the database."
        )
    
    def execute_sql(self):
        """Execute SQL from the editor"""
        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            return
        
        try:
            results = self.db_manager.execute_raw_sql(sql)
            
            # Clear results table
            self.results_table.clear()
            
            if results:
                # If results returned (SELECT query)
                self.results_table.setRowCount(len(results))
                
                # Get column names from cursor description
                if self.db_manager.cursor.description:
                    column_names = [desc[0] for desc in self.db_manager.cursor.description]
                    self.results_table.setColumnCount(len(column_names))
                    self.results_table.setHorizontalHeaderLabels(column_names)
                    
                    # Populate table with results
                    for row_idx, row in enumerate(results):
                        for col_idx, value in enumerate(row):
                            item = QTableWidgetItem(str(value) if value is not None else "NULL")
                            self.results_table.setItem(row_idx, col_idx, item)
                    
                    # Resize columns
                    self.results_table.horizontalHeader().setSectionResizeMode(
                        QHeaderView.ResizeMode.ResizeToContents
                    )
                    
                    self.status_bar.showMessage(f"Query executed: {len(results)} row(s) returned")
                else:
                    # For non-SELECT queries (INSERT, UPDATE, DELETE)
                    affected = self.db_manager.cursor.rowcount
                    self.results_table.setRowCount(1)
                    self.results_table.setColumnCount(1)
                    self.results_table.setHorizontalHeaderLabels(["Result"])
                    
                    result_item = QTableWidgetItem(
                        f"Query executed successfully. Rows affected: {affected}"
                    )
                    self.results_table.setItem(0, 0, result_item)
                    
                    self.status_bar.showMessage(f"Query executed: {affected} row(s) affected")
                    
                    # Refresh table list if structure might have changed
                    if sql.upper().startswith(("CREATE", "DROP", "ALTER")):
                        self.load_tables()
            
        except Exception as e:
            QMessageBox.critical(self, "SQL Error", f"Error executing SQL:\n{str(e)}")
            self.status_bar.showMessage(f"SQL Error: {str(e)}")
    
    def clear_sql(self):
        """Clear the SQL editor"""
        self.sql_editor.clear()
    
    def prev_page(self):
        """Go to previous page of data"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_table_data(self.current_table)
    
    def next_page(self):
        """Go to next page of data"""
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_table_data(self.current_table)
    
    def refresh_tables(self):
        """Refresh the table list and data"""
        self.load_tables()
        if self.current_table:
            self.load_table_data(self.current_table)
        self.status_bar.showMessage("Database refreshed")
    
    def new_database(self):
        """Create a new database"""
        from main import MainWindow
        self.db_manager.close_connection()
        self.close()
        
        # Show main window again
        QTimer.singleShot(100, lambda: MainWindow().show())
    
    def open_database(self):
        """Open a different database"""
        from main import MainWindow
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Database",
            str(Path.home()),
            "SQLite Databases (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        
        if file_path:
            self.db_manager.close_connection()
            self.close()
            
            # Open new editor window
            QTimer.singleShot(100, lambda: EditorWindow(file_path, self.db_manager).show())
    
    def export_to_csv(self):
        """Export current table to CSV"""
        if not self.current_table:
            QMessageBox.warning(self, "No Table", "Please select a table to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            f"{self.current_table}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            success = self.db_manager.export_to_csv(self.current_table, file_path)
            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Table '{self.current_table}' exported to:\n{file_path}"
                )
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export table")
    
    def toggle_sidebar(self):
        """Toggle the sidebar visibility"""
        # Implementation would depend on your layout structure
        pass
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Database Editor",
            """<h2>Database Editor</h2>
            <p>A visual SQLite database editor built with PySide6.</p>
            <p>Version 1.0.0</p>
            <p>Created with ❤️ for database management.</p>
            """
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_changes()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
                return
        
        # Close database connection
        self.db_manager.close_connection()
        event.accept()


class AddTableDialog(QDialog):
    """Dialog for adding a new table"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Add New Table")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Table name
        name_layout = QHBoxLayout()
        name_label = QLabel("Table Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., users, products, orders")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        
        # Columns list
        columns_label = QLabel("Columns:")
        self.columns_table = QTableWidget(0, 4)
        self.columns_table.setHorizontalHeaderLabels([
            "Name", "Type", "Primary Key", "Not Null"
        ])
        
        # Column controls
        controls_layout = QHBoxLayout()
        self.add_column_btn = QPushButton("Add Column")
        self.remove_column_btn = QPushButton("Remove Column")
        
        self.add_column_btn.clicked.connect(self.add_column_row)
        self.remove_column_btn.clicked.connect(self.remove_column_row)
        
        controls_layout.addWidget(self.add_column_btn)
        controls_layout.addWidget(self.remove_column_btn)
        controls_layout.addStretch()
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add widgets to layout
        layout.addLayout(name_layout)
        layout.addWidget(columns_label)
        layout.addWidget(self.columns_table)
        layout.addLayout(controls_layout)
        layout.addWidget(button_box)
        
        # Add one initial column
        self.add_column_row()
    
    def add_column_row(self):
        """Add a new column row to the table"""
        row = self.columns_table.rowCount()
        self.columns_table.insertRow(row)
        
        # Name input
        name_input = QLineEdit()
        name_input.setPlaceholderText("column_name")
        self.columns_table.setCellWidget(row, 0, name_input)
        
        # Type combo
        type_combo = QComboBox()
        type_combo.addItems(["TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC"])
        self.columns_table.setCellWidget(row, 1, type_combo)
        
        # Primary key checkbox
        pk_check = QCheckBox()
        self.columns_table.setCellWidget(row, 2, pk_check)
        
        # Not null checkbox
        nn_check = QCheckBox()
        self.columns_table.setCellWidget(row, 3, nn_check)
    
    def remove_column_row(self):
        """Remove selected column row"""
        current_row = self.columns_table.currentRow()
        if current_row >= 0:
            self.columns_table.removeRow(current_row)
    
    def get_results(self):
        """Get the dialog results"""
        table_name = self.name_input.text().strip()
        
        columns = []
        for row in range(self.columns_table.rowCount()):
            name_widget = self.columns_table.cellWidget(row, 0)
            type_widget = self.columns_table.cellWidget(row, 1)
            pk_widget = self.columns_table.cellWidget(row, 2)
            nn_widget = self.columns_table.cellWidget(row, 3)
            
            if name_widget and type_widget:
                column_name = name_widget.text().strip()
                if column_name:
                    column = {
                        'name': column_name,
                        'type': type_widget.currentText(),
                        'primary_key': pk_widget.isChecked() if pk_widget else False,
                        'not_null': nn_widget.isChecked() if nn_widget else False
                    }
                    columns.append(column)
        
        return table_name, columns


class AddColumnDialog(QDialog):
    """Dialog for adding a new column"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Add New Column")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QFormLayout(self)
        
        # Column name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., email, price, created_at")
        layout.addRow("Column Name:", self.name_input)
        
        # Column type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC"])
        layout.addRow("Data Type:", self.type_combo)
        
        # Default value
        self.default_input = QLineEdit()
        self.default_input.setPlaceholderText("Optional default value")
        layout.addRow("Default Value:", self.default_input)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addRow(button_box)
    
    def get_results(self):
        """Get the dialog results"""
        column_name = self.name_input.text().strip()
        column_type = self.type_combo.currentText()
        default_value = self.default_input.text().strip() or None
        
        return column_name, column_type, default_value
