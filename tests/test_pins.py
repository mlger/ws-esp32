import pytest
from wslib.pins import check_pins, has_errors, parse_use


def levels(findings):
    return [f["level"] for f in findings]


def check(boards, chips, board_id, *specs, wifi=True):
    return check_pins(boards[board_id], chips, [parse_use(s) for s in specs], wifi=wifi)


def test_parse_use():
    assert parse_use("GPIO16=gpio_out:relay") == {"gpio": 16, "function": "gpio_out", "label": "relay"}
    assert parse_use("5") == {"gpio": 5, "function": "gpio", "label": ""}
    assert parse_use("i2c@0x3C:oled") == {"bus": "i2c", "addr": "0x3C", "label": "oled"}
    with pytest.raises(ValueError):
        parse_use("abc=gpio")


def test_free_pin_ok(boards, chips):
    f = check(boards, chips, "esp32-s3-touch-lcd-1.28", "16=gpio_out")
    assert levels(f) == ["ok"]


def test_onboard_conflict(boards, chips):
    f = check(boards, chips, "esp32-s3-touch-lcd-1.28", "2=pwm")
    assert has_errors(f) and "lcd.bl" in f[0]["message"]


def test_flash_pin(boards, chips):
    f = check(boards, chips, "esp32-s3-zero", "27=gpio_out")
    assert has_errors(f) and "flash" in f[0]["message"]


def test_octal_psram_pin(boards, chips):
    f = check(boards, chips, "esp32-s3-lcd-1.47", "35=gpio_out")
    assert any("octal PSRAM" in x["message"] for x in f)


def test_not_exposed(boards, chips):
    f = check(boards, chips, "esp32-s3-zero", "34=gpio_in")
    assert has_errors(f) and "not broken out" in f[0]["message"]


def test_invalid_gpio(boards, chips):
    f = check(boards, chips, "esp32-c6-lcd-1.47", "40=gpio_out")
    assert has_errors(f)


def test_native_usb_only_is_error(boards, chips):
    f = check(boards, chips, "esp32-s3-zero", "19=gpio_out")
    assert has_errors(f)


def test_usb_with_bridge_is_warning(boards, chips):
    f = check(boards, chips, "esp32-s3-touch-lcd-4.3", "19=gpio_out")
    usb = [x for x in f if "native USB" in x["message"]]
    assert usb and usb[0]["level"] == "warn"


def test_strapping_warning(boards, chips):
    f = check(boards, chips, "esp32-s3-zero", "46=gpio_out")
    assert "warn" in levels(f) and not has_errors(f)


def test_soft_boot_button_warns(boards, chips):
    f = check(boards, chips, "esp32-c6-zero", "9=button")
    assert not has_errors(f) and any("boot_button" in x["message"] for x in f)


def test_duplicate_assignment(boards, chips):
    f = check(boards, chips, "esp32-s3-touch-lcd-1.28", "16=gpio_out:a", "16=gpio_in:b")
    assert any("assigned twice" in x["message"] for x in f)


def test_adc2_wifi(boards, chips):
    on = check(boards, chips, "esp32-s3-touch-lcd-1.28", "16=adc")
    off = check(boards, chips, "esp32-s3-touch-lcd-1.28", "16=adc", wifi=False)
    assert any("ADC2" in x["message"] for x in on)
    assert not any("ADC2" in x["message"] for x in off)


def test_no_adc_pin(boards, chips):
    f = check(boards, chips, "esp32-s3-touch-lcd-1.28", "33=adc")
    assert has_errors(f)


def test_input_only(chips):
    board = {"id": "x", "name": "x", "chip": "esp32", "psram_mode": "none", "usb": {"console": "uart0"},
             "verification": {"status": "wiki"}, "peripherals": []}
    f = check_pins(board, chips, [parse_use("34=gpio_out")])
    assert any("input-only" in x["message"] for x in f)


def test_i2c_address_conflict(boards, chips):
    f = check(boards, chips, "esp32-s3-touch-lcd-1.28", "i2c@0x15:dup", "i2c@0x3C:oled", "i2c@0x3c:oled2")
    assert levels(f) == ["error", "ok", "error"]


def test_i2c_reserved_range(boards, chips):
    f = check(boards, chips, "esp32-s3-touch-lcd-4.3", "i2c@0x24:x")
    assert has_errors(f)


def test_unknown_bus(boards, chips):
    f = check(boards, chips, "esp32-s3-zero", "i2c@0x3C:oled")
    assert has_errors(f)


def test_partial_profile_warns(boards, chips):
    f = check(boards, chips, "esp32-s3-touch-amoled-1.8", "10=gpio_out")
    assert f[0]["level"] == "warn" and "partial" in f[0]["message"]
