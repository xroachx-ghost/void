"""
Device diagnostics and health checks.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from typing import Dict, List

from .utils import SafeSubprocess


class DiagnosticsTools:
    """Device diagnostics and health checks"""

    @staticmethod
    def check_battery_health(device_id: str) -> Dict:
        """Get battery health information"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'dumpsys', 'battery'])
        
        battery = {}
        if code == 0:
            for line in stdout.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    battery[key] = value
        
        return battery

    @staticmethod
    def check_storage_health(device_id: str) -> Dict:
        """Get storage health and space information"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'df', '-h'])
        
        storage = {'partitions': []}
        if code == 0:
            lines = stdout.strip().split('\n')
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 6:
                        storage['partitions'].append({
                            'filesystem': parts[0],
                            'size': parts[1],
                            'used': parts[2],
                            'available': parts[3],
                            'use_percent': parts[4],
                            'mounted_on': parts[5]
                        })
        
        return storage

    @staticmethod
    def list_sensors(device_id: str) -> List[Dict]:
        """List available sensors"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'dumpsys', 'sensorservice'])
        
        sensors = []
        if code == 0:
            current_sensor = {}
            for line in stdout.split('\n'):
                if '| ' in line and 'name=' in line.lower():
                    if current_sensor:
                        sensors.append(current_sensor)
                    current_sensor = {'raw': line.strip()}
                    # Parse sensor name
                    if 'name=' in line:
                        start = line.find('name=') + 5
                        end = line.find('|', start)
                        if end > start:
                            current_sensor['name'] = line[start:end].strip()
                elif current_sensor and 'type=' in line.lower():
                    if 'type=' in line:
                        start = line.find('type=') + 5
                        end = line.find('|', start) if '|' in line[start:] else len(line)
                        current_sensor['type'] = line[start:end].strip()
            
            if current_sensor:
                sensors.append(current_sensor)
        
        return sensors

    @staticmethod
    def get_device_temperature(device_id: str) -> Dict:
        """Get device temperature readings"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'dumpsys', 'thermalservice'])
        
        temps = {}
        if code == 0:
            for line in stdout.split('\n'):
                if 'Temperature{' in line or 'mValue=' in line:
                    # Try to extract temperature values
                    if 'mValue=' in line:
                        parts = line.split('mValue=')
                        if len(parts) > 1:
                            value = parts[1].split(',')[0].strip()
                            if 'mType=' in line:
                                type_parts = line.split('mType=')
                                if len(type_parts) > 1:
                                    temp_type = type_parts[1].split(',')[0].strip()
                                    temps[temp_type] = value
        
        # Alternative: try battery temperature
        if not temps:
            code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'dumpsys', 'battery'])
            if code == 0:
                for line in stdout.split('\n'):
                    if 'temperature:' in line.lower():
                        value = line.split(':')[1].strip()
                        # Usually in tenths of degree Celsius
                        try:
                            temps['battery'] = str(int(value) / 10) + '°C'
                        except:
                            temps['battery'] = value
        
        return temps

    @staticmethod
    def get_sim_status(device_id: str) -> Dict:
        """Get SIM card status"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'dumpsys', 'telephony.registry'])
        
        sim = {}
        if code == 0:
            for line in stdout.split('\n'):
                if 'mCallState' in line:
                    sim['call_state'] = line.split('=')[1].strip() if '=' in line else ''
                elif 'mDataConnectionState' in line:
                    sim['data_state'] = line.split('=')[1].strip() if '=' in line else ''
                elif 'mServiceState' in line:
                    sim['service_state'] = line.split('=')[1].strip() if '=' in line else ''
        
        return sim

    @staticmethod
    def get_imei(device_id: str) -> str:
        """Get device IMEI"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'service', 'call', 'iphonesubinfo', '1'])
        
        if code == 0:
            # Parse the output to extract IMEI
            imei = ''
            for line in stdout.split('\n'):
                if "'" in line:
                    parts = line.split("'")
                    for part in parts[1::2]:  # Get odd indices (quoted strings)
                        if part.strip() and part.strip() != '.':
                            imei += part.strip()
            
            return imei if imei else 'N/A'
        
        return 'N/A'

    @staticmethod
    def get_build_fingerprint(device_id: str) -> str:
        """Get device build fingerprint"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'getprop', 'ro.build.fingerprint'])
        
        if code == 0:
            return stdout.strip()
        
        return ''

    @staticmethod
    def test_screen_density(device_id: str) -> Dict:
        """Get screen density information"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'wm', 'density'])
        
        density = {}
        if code == 0:
            for line in stdout.split('\n'):
                if 'Physical density:' in line:
                    density['physical'] = line.split(':')[1].strip()
                elif 'Override density:' in line:
                    density['override'] = line.split(':')[1].strip()
        
        return density

    @staticmethod
    def test_screen_size(device_id: str) -> Dict:
        """Get screen size information"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'wm', 'size'])
        
        size = {}
        if code == 0:
            for line in stdout.split('\n'):
                if 'Physical size:' in line:
                    size['physical'] = line.split(':')[1].strip()
                elif 'Override size:' in line:
                    size['override'] = line.split(':')[1].strip()
        
        return size

    @staticmethod
    def run_device_diagnostics(device_id: str) -> Dict:
        """Run comprehensive device diagnostics"""
        return {
            'battery': DiagnosticsTools.check_battery_health(device_id),
            'storage': DiagnosticsTools.check_storage_health(device_id),
            'temperature': DiagnosticsTools.get_device_temperature(device_id),
            'sim': DiagnosticsTools.get_sim_status(device_id),
            'imei': DiagnosticsTools.get_imei(device_id),
            'build_fingerprint': DiagnosticsTools.get_build_fingerprint(device_id),
            'screen_density': DiagnosticsTools.test_screen_density(device_id),
            'screen_size': DiagnosticsTools.test_screen_size(device_id)
        }
