# temp_humi.py

from ahtx0 import AHT20
from i2c_init import I2C1_GetBus, I2C1_Scan

AHT20_ADDR = 0x38

_i2c = None
_sensor = None


def init_temp_humi():
    global _i2c, _sensor

    if _sensor is None:
        # 使用项目统一 I2C1
        # 不要再 machine.I2C(1, freq=400000)
        _i2c = I2C1_GetBus()

        addrs = I2C1_Scan()
        print("共享 I2C scan:", [hex(a) for a in addrs])

        if AHT20_ADDR not in addrs:
            raise OSError("没有扫描到 AHT20(0x38)，请检查接线/地址/I2C总线")

        _sensor = AHT20(_i2c)

        print("AHT20 使用共享 I2C1")


def read_temp_humidity():
    global _sensor

    if _sensor is None:
        init_temp_humi()

    temp = _sensor.temperature
    humi = _sensor.relative_humidity

    return temp, humi
