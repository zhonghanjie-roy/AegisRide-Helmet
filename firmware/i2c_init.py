from machine import Pin, SoftI2C
import time

# ----------------------------
# 全局 I2C1 对象
# 方案B：I2C1 -> PB8(SCL), PB9(SDA)
# ----------------------------
_i2c1 = None


def I2C1_Init():
    """
    对应 C 版:
    void I2C1_Init(void)
    """
    global _i2c1

    _i2c1 = SoftI2C(
        scl=Pin("PB8", Pin.OPEN_DRAIN),
        sda=Pin("PB9", Pin.OPEN_DRAIN),
        freq=400000
    )

    time.sleep_ms(10)


def _I2C1_CheckInit():
    global _i2c1
    if _i2c1 is None:
        I2C1_Init()


def _Addr8bit_To_7bit(addr):
    """
    你的 C 代码习惯传 8位地址:
    例如 BMI160_ADDR << 1
    MicroPython 要 7位地址，所以这里兼容一下
    """
    if addr > 0x7F:
        return addr >> 1
    return addr


def I2C1_WriteBytes(addr, reg, data, length):
    """
    对应 C 版:
    uint8_t I2C1_WriteBytes(uint8_t addr, uint8_t reg, uint8_t *data, uint8_t len)

    返回:
    1 -> 成功
    0 -> 失败
    """
    _I2C1_CheckInit()

    dev_addr = _Addr8bit_To_7bit(addr)

    try:
        if isinstance(data, int):
            buf = bytes([data])
        elif isinstance(data, bytes):
            if len(data) != length:
                return 0
            buf = data
        elif isinstance(data, bytearray):
            if len(data) != length:
                return 0
            buf = data
        else:
            buf = bytes(list(data)[:length])
            if len(buf) != length:
                return 0

        _i2c1.writeto_mem(dev_addr, reg, buf)
        return 1

    except Exception:
        return 0


def I2C1_ReadBytes(addr, reg, data, length):
    """
    对应 C 版:
    uint8_t I2C1_ReadBytes(uint8_t addr, uint8_t reg, uint8_t *data, uint8_t len)

    注意:
    data 必须传预先分配好的 bytearray
    例如:
        buf = bytearray(1)
        I2C1_ReadBytes(0xD0, 0x00, buf, 1)

    返回:
    1 -> 成功
    0 -> 失败
    """
    _I2C1_CheckInit()

    dev_addr = _Addr8bit_To_7bit(addr)

    try:
        if not isinstance(data, bytearray):
            return 0

        if len(data) != length:
            return 0

        # 关键：直接读进现成缓冲区，不创建新的 bytes 对象
        _i2c1.readfrom_mem_into(dev_addr, reg, data)
        return 1

    except Exception:
        return 0


def I2C1_Scan():
    """
    调试用：扫描总线设备
    返回的是 7 位地址
    """
    _I2C1_CheckInit()

    try:
        return _i2c1.scan()
    except Exception:
        return []
    
def I2C1_GetBus():
    """
    返回全局 I2C1 对象，给 BMI160、MAX30102 共用。
    """
    _I2C1_CheckInit()
    return _i2c1

