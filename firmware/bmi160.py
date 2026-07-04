from i2c_init import I2C1_WriteBytes, I2C1_ReadBytes
import time

# =========================
# BMI160 寄存器定义
# =========================
BMI160_ADDR = 0x69      # 若扫描出来是 0x68，就改成 0x68

BMI160_CHIP_ID    = 0x00
BMI160_ERR_REG    = 0x02
BMI160_PMU_STATUS = 0x03
BMI160_DATA_0     = 0x0C
BMI160_ACC_CONF   = 0x40
BMI160_ACC_RANGE  = 0x41
BMI160_GYR_CONF   = 0x42
BMI160_GYR_RANGE  = 0x43
BMI160_CMD        = 0x7E

BMI160_CMD_ACC_PMU_NORMAL = 0x11
BMI160_CMD_GYR_PMU_NORMAL = 0x15
BMI160_CMD_SOFT_RESET     = 0xB6

BMI160_CHIP_ID_VALUE = 0xD1

# =========================
# 量程枚举
# =========================
ACC_RANGE_2G  = 0x03
ACC_RANGE_4G  = 0x05
ACC_RANGE_8G  = 0x08
ACC_RANGE_16G = 0x0C

GYR_RANGE_2000DPS = 0x00
GYR_RANGE_1000DPS = 0x01
GYR_RANGE_500DPS  = 0x02
GYR_RANGE_250DPS  = 0x03
GYR_RANGE_125DPS  = 0x04

# =========================
# 数据结构
# =========================
class BMI160_Data:
    def __init__(self):
        self.acc_x = 0
        self.acc_y = 0
        self.acc_z = 0
        self.gyr_x = 0
        self.gyr_y = 0
        self.gyr_z = 0

# =========================
# 全局变量
# =========================
current_acc_range = ACC_RANGE_8G
current_gyr_range = GYR_RANGE_2000DPS

clock_flag0 = 0
clock_flag1 = 0
clock_flag2 = 0

ac_gy_flag = 0
st_flag = 0

data = BMI160_Data()
bmi160_data = BMI160_Data()

# =========================
# 预分配缓冲区（关键）
# ISR 里不再临时创建对象
# =========================
_write_buf1 = bytearray(1)
_chip_id_buf = bytearray(1)
_raw_buf12 = bytearray(12)

# =========================
# 阈值改成整数平方比较
# 当前对应：±8g、±2000dps
# 3.5g -> 14336
# 0.9g -> 3686
# 1.1g -> 4506
# 250dps -> 4096
# 20dps -> 328
# =========================
# 3.0g -> 12288
ACC_IMPACT_SQ     = 12288 * 12288
#ACC_IMPACT_SQ     = 14336 * 14336
ACC_STABLE_MIN_SQ = 3686  * 3686
ACC_STABLE_MAX_SQ = 4506  * 4506

GYR_IMPACT_SQ     = 4096 * 4096
GYR_STABLE_MAX_SQ = 328  * 328

# =========================
# 内部函数
# =========================
def BMI160_WriteReg(reg, value):
    _write_buf1[0] = value
    return I2C1_WriteBytes(BMI160_ADDR << 1, reg, _write_buf1, 1)


def BMI160_ReadReg(reg, buf, length):
    return I2C1_ReadBytes(BMI160_ADDR << 1, reg, buf, length)


def _to_int16(low, high):
    value = (high << 8) | low
    if value & 0x8000:
        value -= 65536
    return value

# =========================
# 初始化
# =========================
def BMI160_Init(acc_range, gyr_range):
    global current_acc_range, current_gyr_range

    if not BMI160_ReadReg(BMI160_CHIP_ID, _chip_id_buf, 1):
        return 0

    if _chip_id_buf[0] != BMI160_CHIP_ID_VALUE:
        return 0

    BMI160_WriteReg(BMI160_CMD, BMI160_CMD_SOFT_RESET)
    time.sleep_ms(50)

    BMI160_WriteReg(BMI160_ACC_CONF, 0x28)
    time.sleep_ms(5)

    current_acc_range = acc_range
    BMI160_WriteReg(BMI160_ACC_RANGE, acc_range)
    time.sleep_ms(5)

    BMI160_WriteReg(BMI160_GYR_CONF, 0x28)
    time.sleep_ms(5)

    current_gyr_range = gyr_range
    BMI160_WriteReg(BMI160_GYR_RANGE, gyr_range)
    time.sleep_ms(5)

    BMI160_WriteReg(BMI160_CMD, BMI160_CMD_ACC_PMU_NORMAL)
    time.sleep_ms(5)

    BMI160_WriteReg(BMI160_CMD, BMI160_CMD_GYR_PMU_NORMAL)
    time.sleep_ms(100)

    return 1

# =========================
# 读原始数据
# =========================
def BMI160_ReadData(out_data):
    if not BMI160_ReadReg(BMI160_DATA_0, _raw_buf12, 12):
        return 0

    out_data.gyr_x = _to_int16(_raw_buf12[0],  _raw_buf12[1])
    out_data.gyr_y = _to_int16(_raw_buf12[2],  _raw_buf12[3])
    out_data.gyr_z = _to_int16(_raw_buf12[4],  _raw_buf12[5])

    out_data.acc_x = _to_int16(_raw_buf12[6],  _raw_buf12[7])
    out_data.acc_y = _to_int16(_raw_buf12[8],  _raw_buf12[9])
    out_data.acc_z = _to_int16(_raw_buf12[10], _raw_buf12[11])

    return 1

# =========================
# 这些浮点函数可以保留
# 但不要在硬中断里调用
# 主循环/OLED里用可以
# =========================
def BMI160_GetAccX():
    if BMI160_ReadData(bmi160_data):
        if current_acc_range == ACC_RANGE_2G:
            range_factor = 2.0 / 32768.0
        elif current_acc_range == ACC_RANGE_4G:
            range_factor = 4.0 / 32768.0
        elif current_acc_range == ACC_RANGE_8G:
            range_factor = 8.0 / 32768.0
        elif current_acc_range == ACC_RANGE_16G:
            range_factor = 16.0 / 32768.0
        else:
            range_factor = 2.0 / 32768.0
        return bmi160_data.acc_x * range_factor
    return 0.0


def BMI160_GetAccY():
    if BMI160_ReadData(bmi160_data):
        if current_acc_range == ACC_RANGE_2G:
            range_factor = 2.0 / 32768.0
        elif current_acc_range == ACC_RANGE_4G:
            range_factor = 4.0 / 32768.0
        elif current_acc_range == ACC_RANGE_8G:
            range_factor = 8.0 / 32768.0
        elif current_acc_range == ACC_RANGE_16G:
            range_factor = 16.0 / 32768.0
        else:
            range_factor = 2.0 / 32768.0
        return bmi160_data.acc_y * range_factor
    return 0.0


def BMI160_GetAccZ():
    if BMI160_ReadData(bmi160_data):
        if current_acc_range == ACC_RANGE_2G:
            range_factor = 2.0 / 32768.0
        elif current_acc_range == ACC_RANGE_4G:
            range_factor = 4.0 / 32768.0
        elif current_acc_range == ACC_RANGE_8G:
            range_factor = 8.0 / 32768.0
        elif current_acc_range == ACC_RANGE_16G:
            range_factor = 16.0 / 32768.0
        else:
            range_factor = 2.0 / 32768.0
        return bmi160_data.acc_z * range_factor
    return 0.0


def BMI160_GetGyrX():
    if BMI160_ReadData(bmi160_data):
        if current_gyr_range == GYR_RANGE_2000DPS:
            range_factor = 2000.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_1000DPS:
            range_factor = 1000.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_500DPS:
            range_factor = 500.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_250DPS:
            range_factor = 250.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_125DPS:
            range_factor = 125.0 / 32768.0
        else:
            range_factor = 2000.0 / 32768.0
        return bmi160_data.gyr_x * range_factor
    return 0.0


def BMI160_GetGyrY():
    if BMI160_ReadData(bmi160_data):
        if current_gyr_range == GYR_RANGE_2000DPS:
            range_factor = 2000.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_1000DPS:
            range_factor = 1000.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_500DPS:
            range_factor = 500.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_250DPS:
            range_factor = 250.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_125DPS:
            range_factor = 125.0 / 32768.0
        else:
            range_factor = 2000.0 / 32768.0
        return bmi160_data.gyr_y * range_factor
    return 0.0


def BMI160_GetGyrZ():
    if BMI160_ReadData(bmi160_data):
        if current_gyr_range == GYR_RANGE_2000DPS:
            range_factor = 2000.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_1000DPS:
            range_factor = 1000.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_500DPS:
            range_factor = 500.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_250DPS:
            range_factor = 250.0 / 32768.0
        elif current_gyr_range == GYR_RANGE_125DPS:
            range_factor = 125.0 / 32768.0
        else:
            range_factor = 2000.0 / 32768.0
        return bmi160_data.gyr_z * range_factor
    return 0.0

# =========================
# 碰撞检测（硬中断版）
# 去掉 float / sqrt
# =========================
def caculate_collisions():
    global clock_flag0, clock_flag1, clock_flag2
    global ac_gy_flag, st_flag, data

    # 这里保留你原来的计数风格
    clock_flag0 += 1
    #clock_flag1 += 1
    #clock_flag2 += 1

    if not BMI160_ReadData(data):
        return 0

    ax = data.acc_x
    ay = data.acc_y
    az = data.acc_z

    gx = data.gyr_x
    gy = data.gyr_y
    gz = data.gyr_z

    acc_mag_sq = ax * ax + ay * ay + az * az
    gyr_mag_sq = gx * gx + gy * gy + gz * gz

    if clock_flag0 >= 1:
        clock_flag0 = 0

        if acc_mag_sq > ACC_IMPACT_SQ and gyr_mag_sq > GYR_IMPACT_SQ:
            ac_gy_flag = 1

        if ac_gy_flag == 1 and st_flag == 0:
            clock_flag1 += 1

            if clock_flag1 >= 7500:
                ac_gy_flag = 0
                clock_flag1 = 0
                clock_flag2 = 0

            if (acc_mag_sq >= ACC_STABLE_MIN_SQ and
                acc_mag_sq <= ACC_STABLE_MAX_SQ and
                gyr_mag_sq < GYR_STABLE_MAX_SQ):
                clock_flag2 += 1

                if clock_flag2 >= 100:
                    st_flag = 1
                    ac_gy_flag = 0
                    clock_flag1 = 0
                    clock_flag2 = 0

    return st_flag

