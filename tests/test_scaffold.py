import re
import subprocess
import sys

import pytest
from conftest import SCRIPTS
from wslib.scaffold import arduino_fqbn, plan_project, platformio_ini, render_header, sdkconfig_defaults, write_project

ALL_FRAMEWORKS = ["idf", "arduino", "pio"]


def test_header_defines(boards):
    h = render_header(boards["esp32-s3-touch-lcd-1.28"])
    assert "#define WS_LCD_BL 2" in h
    assert "#define WS_LCD_H_RES 240" in h
    assert "#define WS_TOUCH_I2C_ADDR 0x15" in h
    assert "#pragma once" in h


def test_header_exio_and_unknown(boards):
    h = render_header(boards["esp32-s3-touch-lcd-4.3"])
    assert "#define WS_LCD_BL_EXIO 2" in h
    assert "#define WS_LCD_BL " not in h  # must not look like a GPIO
    import copy
    b = copy.deepcopy(boards["esp32-c6-zero"])
    b["peripherals"][0]["pins"]["data"] = None
    assert "/* WS_RGB_LED_DATA: unknown" in render_header(b)


def test_header_no_duplicate_macros(boards):
    for b in boards.values():
        names = re.findall(r"^#define (\w+)", render_header(b), re.M)
        assert len(names) == len(set(names)), b["id"]


def test_sdkconfig(boards, chips):
    b = boards["esp32-s3-touch-lcd-4.3"]
    s = sdkconfig_defaults(b, chips[b["chip"]])
    assert "CONFIG_SPIRAM_MODE_OCT=y" in s and "CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y" in s
    assert "USB_SERIAL_JTAG" not in s  # console is UART on this board
    b = boards["esp32-s3-touch-lcd-1.28"]
    assert "CONFIG_SPIRAM_MODE_QUAD=y" in sdkconfig_defaults(b, chips[b["chip"]])
    b = boards["esp32-c6-lcd-1.47"]
    s = sdkconfig_defaults(b, chips[b["chip"]])
    assert "SPIRAM" not in s and 'CONFIG_IDF_TARGET="esp32c6"' in s
    assert "CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y" in s


def test_fqbn(boards, chips):
    b = boards["esp32-s3-lcd-1.47"]
    assert arduino_fqbn(b, chips[b["chip"]]) == "esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,CDCOnBoot=cdc"
    b = boards["esp32-c6-zero"]
    assert arduino_fqbn(b, chips[b["chip"]]) == "esp32:esp32:esp32c6:FlashSize=4M,CDCOnBoot=cdc"


def test_p4_revisions(boards, chips):
    v1, v3 = boards["esp32-p4-nano"], boards["esp32-p4-nano-wifi6-db"]
    s = sdkconfig_defaults(v1, chips["esp32p4"])
    assert "CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y" in s and "CONFIG_SPIRAM_MODE_HEX=y" in s
    assert "# CONFIG_ESP32P4_SELECTS_REV_LESS_V3 is not set" in sdkconfig_defaults(v3, chips["esp32p4"])
    assert arduino_fqbn(v1, chips["esp32p4"]) == "esp32:esp32:esp32p4:FlashSize=16M,PSRAM=enabled,ChipVariant=prev3"
    assert arduino_fqbn(v3, chips["esp32p4"]).endswith("ChipVariant=postv3")
    assert "board = esp32-p4\n" in platformio_ini(v1, chips["esp32p4"], "app")
    ini = platformio_ini(v3, chips["esp32p4"], "app")
    assert "board = esp32-p4_r3" in ini and "memory_type" not in ini


def test_platformio(boards, chips):
    b = boards["esp32-s3-touch-lcd-1.28"]
    ini = platformio_ini(b, chips[b["chip"]], "app")
    assert "board_build.arduino.memory_type = qio_qspi" in ini
    assert "default_16MB.csv" in ini and "ARDUINO_USB_CDC_ON_BOOT" not in ini


@pytest.mark.parametrize("framework", ALL_FRAMEWORKS)
def test_plan_every_board(boards, chips, framework):
    for b in boards.values():
        files = plan_project(b, chips[b["chip"]], framework, "demo")
        assert not any(re.search(r"\{\{[A-Z_]+\}\}", c) for c in files.values()), (b["id"], framework)
        assert any(p.endswith("board_pins.h") for p in files)


def test_arduino_layout(boards, chips):
    b = boards["esp32-s3-zero"]
    files = plan_project(b, chips[b["chip"]], "arduino", "blinky")
    assert "blinky/blinky.ino" in files and "blinky/sketch.yaml" in files


def test_bad_name(boards, chips):
    b = boards["esp32-s3-zero"]
    with pytest.raises(ValueError):
        plan_project(b, chips[b["chip"]], "idf", "../evil")


def test_write_refuses_overwrite(tmp_path, boards, chips):
    b = boards["esp32-s3-zero"]
    files = plan_project(b, chips[b["chip"]], "idf", "demo")
    write_project(files, tmp_path)
    with pytest.raises(FileExistsError):
        write_project(files, tmp_path)
    write_project(files, tmp_path, force=True)
    assert (tmp_path / "main" / "main.c").exists()


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPTS / "wsesp.py"), *args],
                          capture_output=True, text=True)


def test_cli_smoke(tmp_path):
    assert run_cli("boards").returncode == 0
    assert run_cli("show", "1.28").returncode == 0
    assert run_cli("validate-data").returncode == 0
    assert run_cli("pins", "1.28", "--use", "16=gpio_out").returncode == 0
    assert run_cli("pins", "1.28", "--use", "2=gpio_out").returncode == 1
    r = run_cli("new", "s3 zero", "--framework", "pio", "--name", "p", "--out", str(tmp_path / "p"))
    assert r.returncode == 0 and (tmp_path / "p" / "platformio.ini").exists()
    assert run_cli("show", "no-such-board").returncode != 0
