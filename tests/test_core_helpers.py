"""
Core helpers tests.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

import importlib
import io
import subprocess


def load_core(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    import void.config as config

    importlib.reload(config)
    config.Config.setup()
    import void.core as core

    return importlib.reload(core)


def test_safe_subprocess_run_success(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)

    def fake_run(cmd, capture_output, text, timeout, shell):
        return subprocess.CompletedProcess(cmd, 0, "ok", "")

    monkeypatch.setattr(core.subprocess, "run", fake_run)

    code, stdout, stderr = core.SafeSubprocess.run(["echo", "ok"])

    assert code == 0
    assert stdout == "ok"
    assert stderr == ""


def test_safe_subprocess_run_timeout(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)

    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="sleep", timeout=1)

    monkeypatch.setattr(core.subprocess, "run", fake_run)

    code, stdout, stderr = core.SafeSubprocess.run(["sleep", "1"], timeout=1)

    assert code == -1
    assert stdout == ""
    assert stderr == "Timeout"


def test_networktools_download_file_success(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)
    dest = tmp_path / "payload.bin"

    class DummyResponse:
        def __init__(self, data):
            self._io = io.BytesIO(data)

        def read(self, *args, **kwargs):
            return self._io.read(*args, **kwargs)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        core.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: DummyResponse(b"payload"),
    )

    assert core.NetworkTools.download_file("https://example.com/file", dest)
    assert dest.read_bytes() == b"payload"


def test_networktools_download_file_rejects_scheme(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)
    dest = tmp_path / "payload.bin"

    assert not core.NetworkTools.download_file("ftp://example.com/file", dest)
    assert not dest.exists()


def test_networktools_check_internet_failure(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)

    def fake_connection(*_args, **_kwargs):
        raise OSError("offline")

    monkeypatch.setattr(core.socket, "create_connection", fake_connection)

    assert core.NetworkTools.check_internet() is False


def test_parse_adb_listing(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)

    info = core.DeviceDetector._parse_adb_listing(
        ["product:sailfish", "model:Pixel", "device:marlin", "transport_id:1", "usb:1-1"]
    )

    assert info == {
        "product": "sailfish",
        "model": "Pixel",
        "device": "marlin",
        "transport_id": "1",
        "usb_path": "1-1",
    }


def test_classify_usb_device_mapping(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)

    mapping = core.DeviceDetector._classify_usb_device("05c6", "9008")

    assert mapping["mode"] == "edl"
    assert mapping["usb_vendor"] == "Qualcomm"
    assert mapping["chipset_vendor_hint"] == "Qualcomm"


def test_classify_usb_device_fallback(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)

    mapping = core.DeviceDetector._classify_usb_device("05c6", "1234")

    assert mapping["mode"] == "usb-unknown"
    assert mapping["usb_vendor"] == "Qualcomm"

    mapping_unknown = core.DeviceDetector._classify_usb_device("ffff", "0001")
    assert mapping_unknown["mode"] == "usb-unknown"
    assert mapping_unknown["usb_vendor"] == "Unknown"


def test_classify_usb_device_online_lookup(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, *_args, **_kwargs):
            return b"ffff OnlineVendor\n\t0001 OnlineDevice\n"

    monkeypatch.setattr(
        core.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: DummyResponse(),
    )

    mapping = core.DeviceDetector._classify_usb_device("ffff", "0001")

    assert mapping["usb_vendor"] == "OnlineVendor"
    assert mapping["usb_product_hint"] == "OnlineDevice"
    assert mapping["mode"] == "usb-unknown"


def test_detect_usb_modes_handles_unknown_vid_pid(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)
    import void.core.device as device_module

    lsusb_output = "Bus 001 Device 004: ID ffff:0001 Unknown Device"

    monkeypatch.setattr(device_module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        core.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: type(
            "Resp",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, exc_type, exc, tb: False,
                "read": lambda self, *_a, **_k: b"ffff OnlineVendor\n\t0001 OnlineDevice\n",
            },
        )(),
    )
    monkeypatch.setattr(
        core.SafeSubprocess,
        "run",
        lambda *_args, **_kwargs: (0, lsusb_output, ""),
    )

    devices, errors = core.DeviceDetector._detect_usb_modes()

    assert errors == []
    assert len(devices) == 1
    device = devices[0]
    assert device["id"] == "usb-001-004-ffff:0001"
    assert device["mode"] == "usb-unknown"
    assert device["usb_vendor"] == "OnlineVendor"
    assert device["usb_product"] == "OnlineDevice"
    assert device["usb_id"] == "ffff:0001"


def test_detect_usb_modes_handles_multiple_identical_vid_pid(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)
    import void.core.device as device_module

    lsusb_output = "\n".join(
        [
            "Bus 001 Device 002: ID 05c6:9008 Qualcomm HS-USB QDLoader 9008",
            "Bus 002 Device 003: ID 05c6:9008 Qualcomm HS-USB QDLoader 9008",
        ]
    )

    monkeypatch.setattr(device_module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        core.SafeSubprocess,
        "run",
        lambda *_args, **_kwargs: (0, lsusb_output, ""),
    )

    devices, errors = core.DeviceDetector._detect_usb_modes()

    assert errors == []
    assert len(devices) == 2
    ids = {device["id"] for device in devices}
    assert "usb-001-002-05c6:9008" in ids
    assert "usb-002-003-05c6:9008" in ids
    for device in devices:
        assert device["usb_id"] == "05c6:9008"
        assert device["usb_bus"] in {"001", "002"}
        assert device["usb_device_number"] in {"002", "003"}


def test_check_adb_ready(tmp_path, monkeypatch):
    core = load_core(tmp_path, monkeypatch)

    monkeypatch.setattr(
        core.SafeSubprocess,
        "run",
        lambda *_args, **_kwargs: (0, "serial", ""),
    )

    assert core.DeviceDetector._check_adb_ready("device-1") is True

    monkeypatch.setattr(
        core.SafeSubprocess,
        "run",
        lambda *_args, **_kwargs: (1, "", ""),
    )

    assert core.DeviceDetector._check_adb_ready("device-2") is False
