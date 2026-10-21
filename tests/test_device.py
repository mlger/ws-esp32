from wslib.device import match_boards, parse_backtrace, parse_esptool

ESPTOOL_V4_S3 = """esptool.py v4.8.1
Serial port COM5
Connecting...
Chip is ESP32-S3 (QFN56) (revision v0.2)
Features: WiFi, BLE, Embedded PSRAM 8MB (AP_3v3)
Crystal is 40MHz
MAC: 34:85:18:aa:bb:cc
Manufacturer: 20
Device: 4018
Detected flash size: 16MB
"""

ESPTOOL_V5_C6 = """esptool v5.0.2
Connected to ESP32-C6 on /dev/ttyACM0:
Chip type:          ESP32-C6 (QFN32) (revision v0.1)
Features:           Wi-Fi 6, BT 5 (LE), IEEE802.15.4, Single Core + LP Core, 160MHz
MAC:                40:4c:ca:11:22:33
Detected flash size: 4MB
"""

XTENSA_PANIC = """Guru Meditation Error: Core  1 panic'ed (LoadProhibited). Exception was unhandled.
PC      : 0x42008a1b  PS      : 0x00060830  A0      : 0x82008b4c
Backtrace: 0x42008a18:0x3fc9a2f0 0x42008b49:0x3fc9a310 0x4037a8d6:0x3fc9a330 |<-CORRUPTED
"""

RISCV_PANIC = """Guru Meditation Error: Core  0 panic'ed (Load access fault). Exception was unhandled.
MEPC    : 0x4200a3c2  RA      : 0x4200a3b8  SP      : 0x4080f2a0
"""


def test_parse_v4():
    info = parse_esptool(ESPTOOL_V4_S3)
    assert info == {"chip": "esp32s3", "chip_name": "ESP32-S3", "psram_mb": 8, "flash_mb": 16,
                    "mac": "34:85:18:aa:bb:cc"}


def test_parse_v5():
    info = parse_esptool(ESPTOOL_V5_C6)
    assert info["chip"] == "esp32c6" and info["flash_mb"] == 4 and info["psram_mb"] == 0


def test_match_s3r8(boards):
    hits = match_boards(parse_esptool(ESPTOOL_V4_S3), boards)
    assert set(hits) == {"esp32-s3-lcd-1.47", "esp32-s3-touch-amoled-1.8", "esp32-s3-touch-lcd-4.3",
                         "esp32-s3-touch-lcd-7", "esp32-s3-touch-lcd-2.8", "esp32-s3-eth"}


def test_match_c6(boards):
    assert set(match_boards(parse_esptool(ESPTOOL_V5_C6), boards)) == {"esp32-c6-lcd-1.47", "esp32-c6-zero"}


def test_backtrace_xtensa():
    assert parse_backtrace(XTENSA_PANIC) == ["0x42008a1b", "0x42008a18", "0x42008b49", "0x4037a8d6"]


def test_backtrace_riscv():
    assert parse_backtrace(RISCV_PANIC) == ["0x4200a3c2"]


def test_backtrace_none():
    assert parse_backtrace("I (123) main: hello") == []
