from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ..config import Config
from .apps import AppManager
from .database import db
from .device import DeviceDetector
from .display import DisplayAnalyzer
from .logging import logger
from .network import NetworkAnalyzer
from .performance import PerformanceAnalyzer
from .privacy import redact_event_data


class ReportGenerator:
    """Automated report generation"""

    @staticmethod
    def _sanitize_device_id(device_id: str) -> str:
        safe_id = re.sub(r'[^A-Za-z0-9]+', '_', device_id).strip('_')
        return safe_id or "unknown"

    @staticmethod
    def generate_device_report(
        device_id: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive device report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_device_id = ReportGenerator._sanitize_device_id(device_id)
        report_name = f"device_report_{safe_device_id}_{timestamp}"
        report_dir = Config.REPORTS_DIR / report_name
        report_dir.mkdir(parents=True, exist_ok=True)

        report = {
            'generated': datetime.now().isoformat(),
            'device_id': device_id,
            'sections': {},
        }

        # Device info
        if progress_callback:
            progress_callback("Collecting device info...")
        devices, _ = DeviceDetector.detect_all()
        device_info = next((d for d in devices if d.get('id') == device_id), {})
        if not device_info:
            logger.log(
                'warning',
                'report',
                f'Device metadata could not be resolved for {device_id}.',
                device_id=device_id,
            )
        report['sections']['device_info'] = device_info

        # Performance analysis
        if progress_callback:
            progress_callback("Analyzing performance...")
        report['sections']['performance'] = PerformanceAnalyzer.analyze(device_id)

        # Network analysis
        if progress_callback:
            progress_callback("Analyzing network...")
        report['sections']['network'] = NetworkAnalyzer.analyze(device_id)

        # Display diagnostics
        if progress_callback:
            progress_callback("Analyzing display...")
        report['sections']['display'] = DisplayAnalyzer.analyze(device_id)

        # App list
        if progress_callback:
            progress_callback("Gathering app inventory...")
        report['sections']['apps'] = {
            'total': len(AppManager.list_apps(device_id)),
            'system': len(AppManager.list_apps(device_id, 'system')),
            'user': len(AppManager.list_apps(device_id, 'user')),
        }

        report = redact_event_data(report)

        # Save as JSON
        if progress_callback:
            progress_callback("Saving report data...")
        json_path = report_dir / "report.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Generate HTML report
        if progress_callback:
            progress_callback("Rendering report...")
        html_path = report_dir / "report.html"
        ReportGenerator._generate_html(report, html_path)

        logger.log('success', 'report', f'Report generated: {report_name}')
        db.track_event(
            'report',
            {
                'report_name': report_name,
                'json_path': str(json_path),
                'html_path': str(html_path),
            },
            device_id,
        )
        if progress_callback:
            progress_callback("Report complete.")

        return {
            'success': True,
            'report_name': report_name,
            'json_path': str(json_path),
            'html_path': str(html_path),
        }

    @staticmethod
    def _generate_html(report: Dict, output_path: Path):
        """Generate HTML report"""
        def _escape(value: Any) -> str:
            return html.escape(str(value), quote=True)

        device_id = _escape(report.get('device_id', 'Unknown'))
        generated = _escape(report.get('generated', ''))
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <title>Void Device Report</title>
    <style>
        body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }}
        .section h2 {{ color: #2196F3; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #2196F3; color: white; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 12px; }}
        .badge-success {{ background: #4CAF50; color: white; }}
        .badge-info {{ background: #2196F3; color: white; }}
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
            <h1>📱 Void Device Report</h1>
            <p>Device: {device_id}</p>
            <p>Generated: {generated}</p>
        </div>
"""

        # Device Info
        if 'device_info' in report['sections']:
            info = report['sections']['device_info']
            html += """        <div class=\"section\">
            <h2>Device Information</h2>
            <table>
"""
            for key, value in info.items():
                if not isinstance(value, dict):
                    label = _escape(key.replace('_', ' ').title())
                    escaped_value = _escape(value)
                    html += f"<tr><td><strong>{label}</strong></td><td>{escaped_value}</td></tr>"

            html += """            </table>
        </div>
"""

            for nested_key in ["battery", "storage", "screen"]:
                nested = info.get(nested_key)
                if isinstance(nested, dict) and nested:
                    nested_title = _escape(nested_key.replace('_', ' ').title())
                    html += f"""        <div class=\"section\">
            <h2>{nested_title} Details</h2>
            <table>
"""
                    for key, value in nested.items():
                        label = _escape(key.replace('_', ' ').title())
                        escaped_value = _escape(value)
                        html += f"<tr><td><strong>{label}</strong></td><td>{escaped_value}</td></tr>"
                    html += """            </table>
        </div>
"""

        # Performance
        if 'performance' in report['sections']:
            perf = report['sections']['performance']
            html += """        <div class=\"section\">
            <h2>Performance Analysis</h2>
            <table>
"""
            for key, value in perf.items():
                if not isinstance(value, (dict, list)):
                    label = _escape(key.replace('_', ' ').title())
                    escaped_value = _escape(value)
                    html += f"<tr><td><strong>{label}</strong></td><td>{escaped_value}</td></tr>"

            html += """            </table>
        </div>
"""

        # Display diagnostics
        if 'display' in report['sections']:
            display = report['sections']['display']
            html += """        <div class=\"section\">
            <h2>Display Diagnostics</h2>
            <table>
"""
            for key, value in display.items():
                if not isinstance(value, (dict, list)):
                    label = _escape(key.replace('_', ' ').title())
                    escaped_value = _escape(value)
                    html += f"<tr><td><strong>{label}</strong></td><td>{escaped_value}</td></tr>"
            html += """            </table>
        </div>
"""

        html += """    </div>
</body>
</html>
"""

        with open(output_path, 'w') as f:
            f.write(html)
