"""
Makro Import/Export Funktionalität
Unterstützt JSON und CSV Format
"""

import json
import csv
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


class MacroImportExport:
    """Import/Export von Makros"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def export_macro_to_json(self, macro_id: int, filepath: str) -> bool:
        """
        Exportiert ein Makro als JSON
        
        Args:
            macro_id: ID des Makros
            filepath: Ziel-Dateipfad
            
        Returns:
            True bei Erfolg
        """
        macro = self.db.get_macro(macro_id)
        if not macro:
            return False
        
        # Exportierbare Daten vorbereiten
        export_data = {
            'version': '2.0',
            'export_date': datetime.now().isoformat(),
            'macro': {
                'name': macro['name'],
                'description': macro['description'],
                'hotkey': macro['hotkey'],
                'loop_count': macro['loop_count'],
                'loop_infinite': macro['loop_infinite'],
                'delay_between_loops': macro['delay_between_loops'],
                'window_filter': macro['window_filter'],
                'actions': macro['actions']
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def export_profile_to_json(self, profile_id: int, filepath: str) -> bool:
        """
        Exportiert ein komplettes Profil mit allen Makros als JSON
        
        Args:
            profile_id: ID des Profils
            filepath: Ziel-Dateipfad
            
        Returns:
            True bei Erfolg
        """
        profile = self.db.get_profile(profile_id)
        if not profile:
            return False
        
        macros = self.db.get_macros(profile_id)
        
        # Exportierbare Daten vorbereiten
        export_data = {
            'version': '2.0',
            'export_date': datetime.now().isoformat(),
            'profile': {
                'name': profile['name'],
                'description': profile['description']
            },
            'macros': [
                {
                    'name': m['name'],
                    'description': m['description'],
                    'hotkey': m['hotkey'],
                    'loop_count': m['loop_count'],
                    'loop_infinite': m['loop_infinite'],
                    'delay_between_loops': m['delay_between_loops'],
                    'window_filter': m['window_filter'],
                    'actions': m['actions']
                }
                for m in macros
            ]
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def import_macro_from_json(self, filepath: str, profile_id: int) -> Optional[int]:
        """
        Importiert ein Makro aus JSON
        
        Args:
            filepath: Quell-Dateipfad
            profile_id: Ziel-Profil ID
            
        Returns:
            ID des importierten Makros oder None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            macro_data = import_data.get('macro', {})
            
            # Makro erstellen
            macro_id = self.db.create_macro(
                profile_id=profile_id,
                name=macro_data.get('name', 'Importiertes Makro'),
                actions=macro_data.get('actions', []),
                description=macro_data.get('description', ''),
                hotkey=macro_data.get('hotkey', ''),
                loop_count=macro_data.get('loop_count', 1),
                loop_infinite=macro_data.get('loop_infinite', False),
                delay_between_loops=macro_data.get('delay_between_loops', 0.0),
                window_filter=macro_data.get('window_filter', '')
            )
            
            return macro_id
        except Exception:
            return None
    
    def import_profile_from_json(self, filepath: str) -> Optional[int]:
        """
        Importiert ein Profil mit allen Makros aus JSON
        
        Args:
            filepath: Quell-Dateipfad
            
        Returns:
            ID des importierten Profils oder None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            profile_data = import_data.get('profile', {})
            
            # Profil erstellen
            profile_id = self.db.create_profile(
                name=profile_data.get('name', 'Importiertes Profil'),
                description=profile_data.get('description', '')
            )
            
            # Makros importieren
            macros_data = import_data.get('macros', [])
            for macro_data in macros_data:
                self.db.create_macro(
                    profile_id=profile_id,
                    name=macro_data.get('name', 'Makro'),
                    actions=macro_data.get('actions', []),
                    description=macro_data.get('description', ''),
                    hotkey=macro_data.get('hotkey', ''),
                    loop_count=macro_data.get('loop_count', 1),
                    loop_infinite=macro_data.get('loop_infinite', False),
                    delay_between_loops=macro_data.get('delay_between_loops', 0.0),
                    window_filter=macro_data.get('window_filter', '')
                )
            
            return profile_id
        except Exception:
            return None
    
    def export_actions_to_csv(self, macro_id: int, filepath: str) -> bool:
        """
        Exportiert Makro-Aktionen als CSV (für Excel)
        
        Args:
            macro_id: ID des Makros
            filepath: Ziel-Dateipfad
            
        Returns:
            True bei Erfolg
        """
        macro = self.db.get_macro(macro_id)
        if not macro:
            return False
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['#', 'Typ', 'Verzögerung (s)', 'Parameter'])
                
                # Aktionen
                for i, action in enumerate(macro['actions'], 1):
                    action_type = action.get('type', '')
                    delay = action.get('delay', 0)
                    
                    # Parameter als String
                    params = ', '.join([
                        f"{k}={v}" for k, v in action.items() 
                        if k not in ['type', 'delay']
                    ])
                    
                    writer.writerow([i, action_type, delay, params])
            
            return True
        except Exception:
            return False
