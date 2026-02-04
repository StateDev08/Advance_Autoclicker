"""
Datenbank-Manager für SQLite
Verwaltet Profile, Makros und Einstellungen
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class DatabaseManager:
    """Verwaltet alle Datenbankoperationen"""
    
    def __init__(self, db_path: str = "data/autoclicker.db"):
        """Initialisiert die Datenbankverbindung"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Erstellt eine neue Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialisiert die Datenbankstruktur"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabelle für Profile
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabelle für Makros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS macros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    actions TEXT NOT NULL,
                    hotkey TEXT,
                    loop_count INTEGER DEFAULT 1,
                    loop_infinite BOOLEAN DEFAULT 0,
                    delay_between_loops REAL DEFAULT 0.0,
                    window_filter TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
                )
            """)
            
            # Tabelle für Einstellungen
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    # Profile-Methoden
    def create_profile(self, name: str, description: str = "") -> int:
        """Erstellt ein neues Profil"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO profiles (name, description) VALUES (?, ?)",
                (name, description)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_profiles(self) -> List[Dict]:
        """Gibt alle Profile zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_profile(self, profile_id: int) -> Optional[Dict]:
        """Gibt ein spezifisches Profil zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_profile(self, profile_id: int, name: str, description: str):
        """Aktualisiert ein Profil"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE profiles 
                   SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (name, description, profile_id)
            )
            conn.commit()
    
    def delete_profile(self, profile_id: int):
        """Löscht ein Profil"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            conn.commit()
    
    # Makro-Methoden
    def create_macro(self, profile_id: int, name: str, actions: List[Dict], 
                     description: str = "", hotkey: str = "", 
                     loop_count: int = 1, loop_infinite: bool = False,
                     delay_between_loops: float = 0.0, window_filter: str = "") -> int:
        """Erstellt ein neues Makro"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO macros 
                   (profile_id, name, description, actions, hotkey, 
                    loop_count, loop_infinite, delay_between_loops, window_filter) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (profile_id, name, description, json.dumps(actions), hotkey,
                 loop_count, loop_infinite, delay_between_loops, window_filter)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_macros(self, profile_id: Optional[int] = None) -> List[Dict]:
        """Gibt alle Makros zurück (optional gefiltert nach Profil)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if profile_id:
                cursor.execute(
                    "SELECT * FROM macros WHERE profile_id = ? ORDER BY name",
                    (profile_id,)
                )
            else:
                cursor.execute("SELECT * FROM macros ORDER BY name")
            
            macros = []
            for row in cursor.fetchall():
                macro = dict(row)
                macro['actions'] = json.loads(macro['actions'])
                macros.append(macro)
            return macros
    
    def get_macro(self, macro_id: int) -> Optional[Dict]:
        """Gibt ein spezifisches Makro zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM macros WHERE id = ?", (macro_id,))
            row = cursor.fetchone()
            if row:
                macro = dict(row)
                macro['actions'] = json.loads(macro['actions'])
                return macro
            return None
    
    def update_macro(self, macro_id: int, name: str, actions: List[Dict],
                     description: str = "", hotkey: str = "",
                     loop_count: int = 1, loop_infinite: bool = False,
                     delay_between_loops: float = 0.0, window_filter: str = ""):
        """Aktualisiert ein Makro"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE macros 
                   SET name = ?, description = ?, actions = ?, hotkey = ?,
                       loop_count = ?, loop_infinite = ?, delay_between_loops = ?,
                       window_filter = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (name, description, json.dumps(actions), hotkey,
                 loop_count, loop_infinite, delay_between_loops, window_filter, macro_id)
            )
            conn.commit()
    
    def delete_macro(self, macro_id: int):
        """Löscht ein Makro"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM macros WHERE id = ?", (macro_id,))
            conn.commit()
    
    # Settings-Methoden
    def get_setting(self, key: str, default: str = "") -> str:
        """Gibt einen Einstellungswert zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def set_setting(self, key: str, value: str):
        """Setzt einen Einstellungswert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO settings (key, value, updated_at) 
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, value)
            )
            conn.commit()
    
    def get_all_settings(self) -> Dict[str, str]:
        """Gibt alle Einstellungen zurück"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row['key']: row['value'] for row in cursor.fetchall()}
