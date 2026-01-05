"""
Workflow orchestration for Void.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .device import DeviceDetector
from .display import DisplayAnalyzer
from .edl_toolkit import list_partitions_via_adb, read_partition_table
from .logging import logger
from .network import NetworkAnalyzer
from .performance import PerformanceAnalyzer
from .report import ReportGenerator
from .setup_wizard import SetupWizardDiagnostics
from .tools import check_android_tools
from .utils import SafeSubprocess, ToolCheckResult


ConfirmCallback = Callable[[str], bool]
EmitCallback = Callable[[str, str], None]


@dataclass
class WorkflowAction:
    name: str
    label: str
    commands: List[List[str]]
    enabled: bool = True


@dataclass
class WorkflowActionResult:
    name: str
    label: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = False
    skipped: bool = False
    reason: Optional[str] = None


class RepairWorkflow:
    """Orchestrate a multi-step device repair workflow."""

    def __init__(
        self,
        device_id: str,
        *,
        confirm_callback: Optional[ConfirmCallback] = None,
        emit_callback: Optional[EmitCallback] = None,
        save_report: bool = False,
    ) -> None:
        self.device_id = device_id
        self.confirm_callback = confirm_callback
        self.emit_callback = emit_callback
        self.save_report = save_report

    def run(self, progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        self._emit("Initializing workflow...", level="info", progress_callback=progress_callback)
        init_result = self._initialize()
        if not init_result["success"]:
            return init_result

        self._emit("Running scans...", level="info", progress_callback=progress_callback)
        scan_result = self._scan(init_result)

        self._emit(
            "Evaluating remediation actions...", level="info", progress_callback=progress_callback
        )
        clear_result = self._clear(init_result, scan_result)

        self._emit(
            "Re-running targeted checks...", level="info", progress_callback=progress_callback
        )
        restore_result = self._restore(init_result, scan_result, clear_result)

        result = {
            "success": True,
            "device_id": self.device_id,
            "initialize": init_result,
            "scan": scan_result,
            "clear": clear_result,
            "restore": restore_result,
        }
        self._emit("Workflow complete.", level="success", progress_callback=progress_callback)
        return result

    def _initialize(self) -> Dict[str, Any]:
        tools = check_android_tools()
        prerequisites = self._serialize_tools(tools)
        devices, errors = DeviceDetector.detect_all()
        device_info = next(
            (device for device in devices if device.get("id") == self.device_id), None
        )
        if not device_info:
            message = f"Device {self.device_id} not found during initialization."
            self._emit(message, level="error")
            return {
                "success": False,
                "message": message,
                "device_id": self.device_id,
                "prerequisites": prerequisites,
                "devices": devices,
                "errors": errors,
            }

        mode = device_info.get("mode")
        self._emit(f"Detected device {self.device_id} in {mode or 'unknown'} mode.", level="info")
        return {
            "success": True,
            "device_id": self.device_id,
            "mode": mode,
            "device_info": device_info,
            "prerequisites": prerequisites,
            "devices": devices,
            "errors": errors,
        }

    def _scan(self, init_result: Dict[str, Any]) -> Dict[str, Any]:
        adb_available = init_result["prerequisites"].get("adb", {}).get("available", False)
        if not adb_available:
            message = "ADB not available; skipping device scans."
            self._emit(message, level="warning")
            return {
                "success": False,
                "message": message,
                "performance": {},
                "network": {},
                "display": {},
                "report": None,
            }

        performance = PerformanceAnalyzer.analyze(self.device_id)
        network = NetworkAnalyzer.analyze(self.device_id)
        display = DisplayAnalyzer.analyze(self.device_id)
        setup_wizard = SetupWizardDiagnostics.analyze(self.device_id)
        report_result = None
        if self.save_report:
            report_result = ReportGenerator.generate_device_report(self.device_id)

        return {
            "success": True,
            "performance": performance,
            "network": network,
            "display": display,
            "startup_wizard": setup_wizard,
            "partitions": self._scan_partitions(init_result),
            "report": report_result,
        }

    def _clear(self, init_result: Dict[str, Any], scan_result: Dict[str, Any]) -> Dict[str, Any]:
        mode = str(init_result.get("mode") or "").lower()
        if mode != "adb":
            message = "Device is not in ADB mode; remediation actions skipped."
            self._emit(message, level="warning")
            return {
                "success": False,
                "message": message,
                "actions": [],
            }

        actions = self._build_actions(scan_result)
        action_results: List[WorkflowActionResult] = []
        for action in actions:
            action_results.append(self._execute_action(action))

        return {
            "success": True,
            "actions": [self._action_result_to_dict(result) for result in action_results],
        }

    def _restore(
        self,
        init_result: Dict[str, Any],
        scan_result: Dict[str, Any],
        clear_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        adb_available = init_result["prerequisites"].get("adb", {}).get("available", False)
        if not adb_available:
            message = "ADB not available; restore checks skipped."
            self._emit(message, level="warning")
            return {"success": False, "message": message}

        performance = PerformanceAnalyzer.analyze(self.device_id)
        network = NetworkAnalyzer.analyze(self.device_id)
        display = DisplayAnalyzer.analyze(self.device_id)
        summary = self._summarize_restore(scan_result, clear_result, performance, network, display)
        return {
            "success": True,
            "performance": performance,
            "network": network,
            "display": display,
            "summary": summary,
            "report": scan_result.get("report"),
        }

    def _scan_partitions(self, init_result: Dict[str, Any]) -> Dict[str, Any]:
        mode = str(init_result.get("mode") or "").lower()
        adb_available = init_result["prerequisites"].get("adb", {}).get("available", False)
        results: Dict[str, Any] = {}
        if adb_available and mode == "adb":
            adb_partitions = list_partitions_via_adb(self.device_id)
            results["adb"] = {
                "success": adb_partitions.success,
                "message": adb_partitions.message,
                "data": adb_partitions.data,
            }
        if mode in {"edl", "download"}:
            edl_partitions = read_partition_table()
            results["edl"] = {
                "success": edl_partitions.success,
                "message": edl_partitions.message,
                "data": edl_partitions.data,
            }
        return results

    def _build_actions(self, scan_result: Dict[str, Any]) -> List[WorkflowAction]:
        network_info = scan_result.get("network") or {}
        wifi_status = (network_info.get("wifi") or {}).get("status")
        interfaces = network_info.get("interfaces") or []

        actions = [
            WorkflowAction(
                name="reboot_recovery",
                label="Reboot into recovery (bootloop recovery)",
                commands=[
                    ["adb", "-s", self.device_id, "reboot", "recovery"],
                ],
            ),
            WorkflowAction(
                name="restart_adbd",
                label="Restart ADB daemon",
                commands=[
                    ["adb", "-s", self.device_id, "shell", "stop", "adbd"],
                    ["adb", "-s", self.device_id, "shell", "start", "adbd"],
                ],
            ),
            WorkflowAction(
                name="clear_setup_wizard",
                label="Clear setup wizard data",
                commands=[
                    [
                        "adb",
                        "-s",
                        self.device_id,
                        "shell",
                        "pm",
                        "clear",
                        "com.google.android.setupwizard",
                    ],
                    [
                        "adb",
                        "-s",
                        self.device_id,
                        "shell",
                        "pm",
                        "clear",
                        "com.android.setupwizard",
                    ],
                    ["adb", "-s", self.device_id, "shell", "pm", "clear", "com.android.provision"],
                ],
            ),
            WorkflowAction(
                name="network_reset",
                label="Reset Wi-Fi and mobile data",
                commands=[
                    ["adb", "-s", self.device_id, "shell", "svc", "wifi", "disable"],
                    ["adb", "-s", self.device_id, "shell", "svc", "wifi", "enable"],
                    ["adb", "-s", self.device_id, "shell", "svc", "data", "disable"],
                    ["adb", "-s", self.device_id, "shell", "svc", "data", "enable"],
                ],
                enabled=bool(interfaces) or wifi_status in {None, "disabled"},
            ),
            WorkflowAction(
                name="factory_reset",
                label="Factory reset (wipe user data)",
                commands=[
                    ["adb", "-s", self.device_id, "shell", "recovery", "--wipe_data"],
                    [
                        "adb",
                        "-s",
                        self.device_id,
                        "shell",
                        "am",
                        "broadcast",
                        "-a",
                        "android.intent.action.MASTER_CLEAR",
                    ],
                ],
            ),
        ]

        return actions

    def _execute_action(self, action: WorkflowAction) -> WorkflowActionResult:
        if not action.enabled:
            message = f"Skipped {action.label} (not required)."
            self._emit(message, level="info")
            return WorkflowActionResult(
                name=action.name,
                label=action.label,
                skipped=True,
                reason="not_required",
            )

        if not self._confirm(f"{action.label} on {self.device_id}?"):
            message = f"Skipped {action.label} (user declined)."
            self._emit(message, level="info")
            return WorkflowActionResult(
                name=action.name,
                label=action.label,
                skipped=True,
                reason="user_declined",
            )

        result = WorkflowActionResult(name=action.name, label=action.label)
        for cmd in action.commands:
            code, stdout, stderr = SafeSubprocess.run(cmd)
            detail = (stderr or stdout or "").strip() or None
            step = {
                "command": " ".join(cmd),
                "success": code == 0,
                "detail": detail,
            }
            result.steps.append(step)
        result.success = all(step["success"] for step in result.steps)
        message = f"{action.label} {'succeeded' if result.success else 'completed with issues'}."
        self._emit(message, level="success" if result.success else "warning")
        return result

    def _summarize_restore(
        self,
        scan_result: Dict[str, Any],
        clear_result: Dict[str, Any],
        performance: Dict[str, Any],
        network: Dict[str, Any],
        display: Dict[str, Any],
    ) -> Dict[str, Any]:
        actions = clear_result.get("actions") or []
        restored = {
            "performance_keys": len(performance),
            "network_interfaces": len(network.get("interfaces") or []),
            "display_state": display.get("screen_state") or display.get("power_state"),
            "actions_applied": sum(1 for action in actions if action.get("success")),
            "actions_skipped": sum(1 for action in actions if action.get("skipped")),
        }
        previous_network = scan_result.get("network") or {}
        restored["network_interfaces_before"] = len(previous_network.get("interfaces") or [])
        previous_partitions = scan_result.get("partitions") or {}
        adb_partitions = previous_partitions.get("adb", {}).get("data", {}).get("partitions") or []
        restored["partition_count"] = len(adb_partitions)
        return restored

    def _confirm(self, prompt: str) -> bool:
        if not self.confirm_callback:
            return False
        return self.confirm_callback(prompt)

    def _serialize_tools(self, tools: List[ToolCheckResult]) -> Dict[str, Dict[str, Any]]:
        output: Dict[str, Dict[str, Any]] = {}
        for tool in tools:
            output[tool.name] = {
                "available": tool.available,
                "label": tool.label,
                "path": tool.path,
                "version": tool.version,
                "error": tool.error,
            }
        return output

    def _action_result_to_dict(self, result: WorkflowActionResult) -> Dict[str, Any]:
        return {
            "name": result.name,
            "label": result.label,
            "steps": result.steps,
            "success": result.success,
            "skipped": result.skipped,
            "reason": result.reason,
        }

    def _emit(
        self,
        message: str,
        *,
        level: str = "info",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        logger.log(level, "workflow", message, device_id=self.device_id, method="repair-flow")
        if self.emit_callback:
            self.emit_callback(message, level.upper())
        if progress_callback:
            progress_callback(message)
