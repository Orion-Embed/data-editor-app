"""
Database Manager - SQLite3 operations
"""

import sqlite3
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """Manages all SQLite database operations"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.current_file = None
        
    def create_database(self, file_path: str) -> bool:
        """Create a new SQLite database file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Remove file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Create new database
            self.connection = sqlite3.connect(file_path)
            self.cursor = self.connection.cursor()
            self.current_file = file_path
            
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Create metadata table for our application
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS _db_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Store creation metadata
            metadata = {
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "application": "Database Editor"
            }
            
            self.cursor.execute(
                "INSERT OR REPLACE INTO _db_meta (key, value) VALUES (?, ?)",
                ("metadata", json.dumps(metadata))
            )
            
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"Error creating database: {e}")
            self.close_connection()
            raise
    
    def open_database(self, file_path: str) -> bool:
        """Open an existing SQLite database"""
        try:
            self.connection = sqlite3.connect(file_path)
            self.cursor = self.connection.cursor()
            self.current_file = file_path
            
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Verify it's a valid SQLite database
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            _ = self.cursor.fetchall()  # Just to test
            
            return True
            
        except sqlite3.Error as e:
            print(f"Error opening database: {e}")
            self.close_connection()
            raise
    
    def is_valid_database(self, file_path: str) -> bool:
        """Check if a file is a valid SQLite database"""
        if not os.path.exists(file_path):
            return False
        
        try:
            # Try to open and read the header
            with open(file_path, 'rb') as f:
                header = f.read(16)
                # SQLite database files start with "SQLite format 3\000"
                return header[:15] == b'SQLite format 3\x00'
        except:
            return False
    
    def get_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        if not self.connection:
            return []
        
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            AND name NOT LIKE '_db_%'
            ORDER BY name
        """)
        
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table"""
        if not self.connection:
            return []
        
        # Get column information
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        
        for row in self.cursor.fetchall():
            column = {
                'cid': row[0],
                'name': row[1],
                'type': row[2],
                'notnull': bool(row[3]),
                'default': row[4],
                'pk': bool(row[5])
            }
            columns.append(column)
        
        # Get foreign key information
        self.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = {}
        
        for row in self.cursor.fetchall():
            col_name = row[3]  # 'from' column
            foreign_keys[col_name] = {
                'table': row[2],  # 'to' table
                'column': row[4]  # 'to' column
            }
        
        # Add foreign key info to columns
        for col in columns:
            if col['name'] in foreign_keys:
                col['foreign_key'] = foreign_keys[col['name']]
        
        return columns
    
    def get_table_data(self, table_name: str, limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int]:
        """Get data from a table with pagination"""
        if not self.connection:
            return [], 0
        
        # Get total row count
        self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = self.cursor.fetchone()[0]
        
        # Get column names
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in self.cursor.fetchall()]
        
        # Get data with pagination
        self.cursor.execute(f"""
            SELECT * FROM {table_name} 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = []
        for row in self.cursor.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            rows.append(row_dict)
        
        return rows, total_rows
    
    def create_table(self, table_name: str, columns: List[Dict]) -> bool:
        """Create a new table"""
        if not self.connection:
            return False
        
        try:
            # Build CREATE TABLE statement
            column_defs = []
            for col in columns:
                col_def = f"{col['name']} {col['type']}"
                if col.get('primary_key'):
                    col_def += " PRIMARY KEY"
                if col.get('not_null'):
                    col_def += " NOT NULL"
                if col.get('default'):
                    col_def += f" DEFAULT {col['default']}"
                column_defs.append(col_def)
            
            sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
            
            self.cursor.execute(sql)
            self.connection.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
            return False
    
    def add_column(self, table_name: str, column_name: str, 
                   column_type: str, default_value: str = None) -> bool:
        """Add a new column to an existing table"""
        if not self.connection:
            return False
        
        try:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_value:
                sql += f" DEFAULT {default_value}"
            
            self.cursor.execute(sql)
            self.connection.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error adding column: {e}")
            return False
    
    def insert_row(self, table_name: str, data: Dict[str, Any]) -> int:
        """Insert a new row into a table"""
        if not self.connection:
            return -1
        
        try:
            columns = list(data.keys())
            placeholders = ', '.join(['?'] * len(columns))
            values = list(data.values())
            
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            self.cursor.execute(sql, values)
            self.connection.commit()
            
            return self.cursor.lastrowid
            
        except sqlite3.Error as e:
            print(f"Error inserting row: {e}")
            return -1
    
    def update_row(self, table_name: str, row_id: int, 
                   data: Dict[str, Any], id_column: str = 'id') -> bool:
        """Update an existing row"""
        if not self.connection:
            return False
        
        try:
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            values = list(data.values())
            values.append(row_id)
            
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
            
            self.cursor.execute(sql, values)
            self.connection.commit()
            
            return self.cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error updating row: {e}")
            return False
    
    def delete_row(self, table_name: str, row_id: int, 
                   id_column: str = 'id') -> bool:
        """Delete a row from a table"""
        if not self.connection:
            return False
        
        try:
            sql = f"DELETE FROM {table_name} WHERE {id_column} = ?"
            self.cursor.execute(sql, (row_id,))
            self.connection.commit()
            
            return self.cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error deleting row: {e}")
            return False
    
    def execute_raw_sql(self, sql: str, params: tuple = None) -> List[Tuple]:
        """Execute raw SQL query"""
        if not self.connection:
            return []
        
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
            if sql.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return []
                
        except sqlite3.Error as e:
            print(f"Error executing SQL: {e}")
            return []
    
    def export_to_csv(self, table_name: str, file_path: str) -> bool:
        """Export table data to CSV file"""
        if not self.connection:
            return False
        
        try:
            # Get data
            data, _ = self.get_table_data(table_name, limit=0)
            if not data:
                return False
            
            # Get column names
            columns = list(data[0].keys())
            
            # Write to CSV
            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                
                for row in data:
                    writer.writerow([row[col] for col in columns])
            
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.commit()
            self.connection.close()
            self.connection = None
            self.cursor = None
            self.current_file = None
    
    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close_connection()
