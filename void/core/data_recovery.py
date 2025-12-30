"""
Data recovery workflows.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..config import Config
from .utils import SafeSubprocess


class DataRecovery:
    """Automated data recovery"""

    @staticmethod
    def recover_contacts(device_id: str) -> Dict[str, Any]:
        """Recover contacts"""
        output_dir = Config.EXPORTS_DIR / f"contacts_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)

        contacts_paths = [
            '/data/data/com.android.providers.contacts/databases/contacts2.db',
        ]

        recovered = []
        for db_path in contacts_paths:
            local_path = output_dir / Path(db_path).name
            code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'pull', db_path, str(local_path)])

            if code == 0 and local_path.exists():
                contacts = DataRecovery._parse_contacts_db(local_path)
                recovered.extend(contacts)

        if recovered:
            output_file = output_dir / "contacts.json"
            with open(output_file, 'w') as f:
                json.dump(recovered, f, indent=2)

            # Also save as CSV
            csv_file = output_dir / "contacts.csv"
            with open(csv_file, 'w', newline='') as f:
                if recovered:
                    writer = csv.DictWriter(f, fieldnames=recovered[0].keys())
                    writer.writeheader()
                    writer.writerows(recovered)

            return {
                'success': True,
                'count': len(recovered),
                'json_path': str(output_file),
                'csv_path': str(csv_file),
            }

        return {'success': False, 'count': 0}

    @staticmethod
    def _parse_contacts_db(db_path: Path) -> List[Dict]:
        """Parse contacts database"""
        contacts = []
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()

                # Try different table schemas
                try:
                    cursor.execute("SELECT display_name FROM raw_contacts LIMIT 1000")
                    for row in cursor.fetchall():
                        if row[0]:
                            contacts.append({'name': row[0]})
                except Exception:
                    pass
        except Exception:
            pass
        return contacts

    @staticmethod
    def recover_sms(device_id: str) -> Dict[str, Any]:
        """Recover SMS messages"""
        output_dir = Config.EXPORTS_DIR / f"sms_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)

        sms_paths = [
            '/data/data/com.android.providers.telephony/databases/mmssms.db',
        ]

        recovered = []
        for db_path in sms_paths:
            local_path = output_dir / Path(db_path).name
            code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'pull', db_path, str(local_path)])

            if code == 0 and local_path.exists():
                messages = DataRecovery._parse_sms_db(local_path)
                recovered.extend(messages)

        if recovered:
            output_file = output_dir / "messages.json"
            with open(output_file, 'w') as f:
                json.dump(recovered, f, indent=2, default=str)

            return {
                'success': True,
                'count': len(recovered),
                'path': str(output_file),
            }

        return {'success': False, 'count': 0}

    @staticmethod
    def _parse_sms_db(db_path: Path) -> List[Dict]:
        """Parse SMS database"""
        messages = []
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()

                try:
                    cursor.execute("SELECT address, body, date FROM sms LIMIT 1000")
                    for row in cursor.fetchall():
                        messages.append(
                            {
                                'address': row[0],
                                'body': row[1],
                                'date': datetime.fromtimestamp(int(row[2]) / 1000).isoformat() if row[2] else '',
                            }
                        )
                except Exception:
                    pass
        except Exception:
            pass
        return messages
