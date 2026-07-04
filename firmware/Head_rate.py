import machine
import utime
from i2c_init import I2C1_GetBus, I2C1_Scan

MAX30102_ADDR = 0x57


MAX30102_ADDR = 0x57


def try_make_i2c():
    """
    使用项目统一 I2C1。
    不再重新创建 I2C(1)、I2C(2)、SoftI2C(D14/D15)，避免影响 BMI160。
    """
    i2c = I2C1_GetBus()

    addrs = I2C1_Scan()
    print("共享 I2C scan:", [hex(a) for a in addrs])

    if MAX30102_ADDR not in addrs:
        raise OSError("没有扫描到 MAX30102(0x57)，请检查接线/地址/I2C总线")

    print("MAX30102 使用共享 I2C1")
    return i2c


class MAX30102:
    REG_INTR_STATUS_1 = 0x00
    REG_INTR_STATUS_2 = 0x01
    REG_INTR_ENABLE_1 = 0x02
    REG_INTR_ENABLE_2 = 0x03
    REG_FIFO_WR_PTR = 0x04
    REG_OVF_COUNTER = 0x05
    REG_FIFO_RD_PTR = 0x06
    REG_FIFO_DATA = 0x07
    REG_FIFO_CONFIG = 0x08
    REG_MODE_CONFIG = 0x09
    REG_SPO2_CONFIG = 0x0A
    REG_LED1_PA = 0x0C
    REG_LED2_PA = 0x0D
    REG_REV_ID = 0xFE
    REG_PART_ID = 0xFF

    PART_ID_EXPECTED = 0x15
    MODE_RESET = 0x40
    MODE_SPO2 = 0x03

    SAMPLE_RATE_HZ = 100
    SAMPLE_PERIOD_MS = 10
    FIFO_BATCH_SAMPLES = 32

    FIFO_CONFIG_VALUE = 0x0F
    SPO2_CONFIG_VALUE = 0x27
    LED1_PA_VALUE = 0x3F
    LED2_PA_VALUE = 0x3F

    def __init__(self, i2c, addr=MAX30102_ADDR):
        self.i2c = i2c
        self.addr = addr

        if addr not in self.i2c.scan():
            raise OSError("MAX30102 不在 I2C 总线上")

    def write_reg(self, reg, value):
        self.i2c.writeto_mem(self.addr, reg, bytes([value & 0xFF]))

    def read_reg(self, reg, n=1):
        return self.i2c.readfrom_mem(self.addr, reg, n)

    def read_u8(self, reg):
        return self.read_reg(reg, 1)[0]

    def clear_interrupts(self):
        self.read_reg(self.REG_INTR_STATUS_1, 2)

    def clear_fifo(self):
        self.write_reg(self.REG_FIFO_WR_PTR, 0x00)
        self.write_reg(self.REG_OVF_COUNTER, 0x00)
        self.write_reg(self.REG_FIFO_RD_PTR, 0x00)
        self.clear_interrupts()

    def reset(self):
        self.write_reg(self.REG_MODE_CONFIG, self.MODE_RESET)
        start = utime.ticks_ms()

        while utime.ticks_diff(utime.ticks_ms(), start) < 100:
            if (self.read_u8(self.REG_MODE_CONFIG) & self.MODE_RESET) == 0:
                return
            utime.sleep_ms(2)

        raise OSError("MAX30102 复位超时")

    def is_present(self):
        try:
            return self.read_u8(self.REG_PART_ID) == self.PART_ID_EXPECTED
        except Exception:
            return False

    def setup(self):
        if not self.is_present():
            raise OSError("MAX30102 PART_ID 不匹配")

        self.reset()

        # 轮询 FIFO，关闭中断
        self.write_reg(self.REG_INTR_ENABLE_1, 0x00)
        self.write_reg(self.REG_INTR_ENABLE_2, 0x00)

        self.write_reg(self.REG_FIFO_CONFIG, self.FIFO_CONFIG_VALUE)
        self.write_reg(self.REG_SPO2_CONFIG, self.SPO2_CONFIG_VALUE)
        self.write_reg(self.REG_LED1_PA, self.LED1_PA_VALUE)
        self.write_reg(self.REG_LED2_PA, self.LED2_PA_VALUE)
        self.write_reg(self.REG_MODE_CONFIG, self.MODE_SPO2)
        self.clear_fifo()
        utime.sleep_ms(50)

    def summary(self):
        return {
            "part": self.read_u8(self.REG_PART_ID),
            "rev": self.read_u8(self.REG_REV_ID),
            "mode": self.read_u8(self.REG_MODE_CONFIG),
            "fifo": self.read_u8(self.REG_FIFO_CONFIG),
            "spo2": self.read_u8(self.REG_SPO2_CONFIG),
            "red_pa": self.read_u8(self.REG_LED1_PA),
            "ir_pa": self.read_u8(self.REG_LED2_PA),
        }

    def diagnostics(self):
        block = self.read_reg(self.REG_FIFO_WR_PTR, 3)
        wr = block[0] & 0x1F
        ovf = block[1]
        rd = block[2] & 0x1F
        avail = (wr - rd) & 0x1F
        return wr, rd, ovf, avail

    def read_samples(self, max_samples=FIFO_BATCH_SAMPLES):
        wr, rd, ovf, avail = self.diagnostics()
        overflowed = ovf != 0

        if avail == 0 and overflowed:
            samples_to_read = max_samples
        elif avail == 0:
            return [], overflowed, (wr, rd, ovf, avail)
        else:
            samples_to_read = avail
            if samples_to_read > max_samples:
                samples_to_read = max_samples

        if samples_to_read > self.FIFO_BATCH_SAMPLES:
            samples_to_read = self.FIFO_BATCH_SAMPLES

        data = self.read_reg(self.REG_FIFO_DATA, samples_to_read * 6)
        samples = []

        for index in range(samples_to_read):
            base = index * 6
            red = ((data[base] << 16) | (data[base + 1] << 8) | data[base + 2]) & 0x03FFFF
            ir = ((data[base + 3] << 16) | (data[base + 4] << 8) | data[base + 5]) & 0x03FFFF
            samples.append((red, ir))

        return samples, overflowed, (wr, rd, ovf, avail)


class HeartRateEstimator:
    RAW_WINDOW_SIZE = 100
    ALGO_WINDOW_SIZE = 300
    BPM_HISTORY_SIZE = 5

    CONTACT_MEAN_MIN = 12000
    CONTACT_INSTANT_MIN = 8000
    SIGNAL_SPAN_MIN = 150
    CONTACT_RELEASE_MEAN_MIN = 6000
    CONTACT_RELEASE_INSTANT_MIN = 4000
    SIGNAL_RELEASE_SPAN_MIN = 80
    SIGNAL_RELEASE_HOLD_SAMPLES = 25
    CONTACT_SETTLE_MS = 2000

    TRACK_LOCK_COUNT = 1
    STALE_TIMEOUT_MS = 6000
    LAST_BPM_HOLD_TIMEOUT_MS = 6000

    MIN_BPM_X10 = 400
    MAX_BPM_X10 = 1800
    PEAK_DEDUP_MAX_BPM_X10 = 1200
    STARTUP_MAX_BPM_X10 = 1100
    BPM_UP_JUMP_LIMIT_X10 = 150
    INTERVAL_JITTER_NUMERATOR = 2
    INTERVAL_JITTER_DENOMINATOR = 5
    MIN_GOOD_INTERVAL_RATIO_NUMERATOR = 3
    MIN_GOOD_INTERVAL_RATIO_DENOMINATOR = 5
    MA4_SIZE = 4
    HAMMING = (41, 276, 512, 276, 41)
    MAX_PEAKS = 15

    STATUS_INVALID = "INVALID"
    STATUS_SEARCHING = "SEARCHING"
    STATUS_TRACKING = "TRACKING"

    def __init__(self, sample_rate_hz=100):
        self.sample_rate_hz = sample_rate_hz
        self.raw_history = [0] * self.RAW_WINDOW_SIZE
        self.ir_window = [0] * self.ALGO_WINDOW_SIZE
        self.bpm_history = [0] * self.BPM_HISTORY_SIZE
        self.reset_all()

    def reset_all(self):
        self.sample_index = 0
        self.latest_ir_raw = 0
        self.raw_mean = 0
        self.raw_span = 0
        self.filtered_ir = 0
        self.contact_present = False
        self.status = self.STATUS_INVALID
        self.bpm_x10 = 0
        self.beat_history_count = 0
        self.window_fill = 0
        self.tracking_streak = 0
        self.last_valid_beat_tick_ms = None
        self.raw_sum = 0
        self.raw_index = 0
        self.raw_count = 0
        self.ir_window_head = 0
        self.ir_window_count = 0
        self.invalid_signal_streak = 0
        self.contact_settling = False
        self.contact_settle_start_tick_ms = None
        self.bpm_history_head = 0
        self.bpm_history_count = 0

        for index in range(self.RAW_WINDOW_SIZE):
            self.raw_history[index] = 0
        for index in range(self.ALGO_WINDOW_SIZE):
            self.ir_window[index] = 0
        for index in range(self.BPM_HISTORY_SIZE):
            self.bpm_history[index] = 0

    def clear_window_tracking(self):
        self.filtered_ir = 0
        self.bpm_x10 = 0
        self.beat_history_count = 0
        self.window_fill = 0
        self.tracking_streak = 0
        self.last_valid_beat_tick_ms = None
        self.ir_window_head = 0
        self.ir_window_count = 0
        self.invalid_signal_streak = 0
        self.bpm_history_head = 0
        self.bpm_history_count = 0

        for index in range(self.ALGO_WINDOW_SIZE):
            self.ir_window[index] = 0
        for index in range(self.BPM_HISTORY_SIZE):
            self.bpm_history[index] = 0

    def on_overflow(self):
        self.clear_window_tracking()
        self.contact_settling = False
        self.contact_settle_start_tick_ms = None
        self.status = self.STATUS_SEARCHING

    @staticmethod
    def _div_trunc(value, divisor):
        if value >= 0:
            return value // divisor
        return -((-value) // divisor)

    def _update_raw_window(self, ir_raw):
        if self.raw_count < self.RAW_WINDOW_SIZE:
            self.raw_history[self.raw_index] = ir_raw
            self.raw_sum += ir_raw
            self.raw_count += 1
        else:
            self.raw_sum -= self.raw_history[self.raw_index]
            self.raw_history[self.raw_index] = ir_raw
            self.raw_sum += ir_raw

        self.raw_index += 1
        if self.raw_index >= self.RAW_WINDOW_SIZE:
            self.raw_index = 0

    def _update_raw_stats(self):
        if self.raw_count == 0:
            self.raw_mean = 0
            self.raw_span = 0
            return

        min_value = self.raw_history[0]
        max_value = self.raw_history[0]

        for index in range(self.raw_count):
            sample = self.raw_history[index]
            if sample < min_value:
                min_value = sample
            if sample > max_value:
                max_value = sample

        self.raw_mean = self.raw_sum // self.raw_count
        self.raw_span = max_value - min_value

    def _push_ir_window_sample(self, ir_raw):
        self.ir_window[self.ir_window_head] = ir_raw
        self.ir_window_head += 1

        if self.ir_window_head >= self.ALGO_WINDOW_SIZE:
            self.ir_window_head = 0

        if self.ir_window_count < self.ALGO_WINDOW_SIZE:
            self.ir_window_count += 1

        self.window_fill = self.ir_window_count

    def _copy_linear_window(self):
        start_index = self.ir_window_head
        return [
            self.ir_window[(start_index + index) % self.ALGO_WINDOW_SIZE]
            for index in range(self.ALGO_WINDOW_SIZE)
        ]

    def _push_bpm_history(self, bpm_x10):
        self.bpm_history[self.bpm_history_head] = bpm_x10
        self.bpm_history_head += 1

        if self.bpm_history_head >= self.BPM_HISTORY_SIZE:
            self.bpm_history_head = 0

        if self.bpm_history_count < self.BPM_HISTORY_SIZE:
            self.bpm_history_count += 1

    def _median_bpm_history(self):
        if self.bpm_history_count == 0:
            return 0

        ordered = []
        for index in range(self.bpm_history_count):
            ordered.append(self.bpm_history[index])
        ordered.sort()

        count = len(ordered)
        if count & 1:
            return ordered[count // 2]

        upper = count // 2
        lower = upper - 1
        return (ordered[lower] + ordered[upper] + 1) // 2

    def _min_peak_distance_samples(self):
        return max(1, (self.sample_rate_hz * 600 + self.PEAK_DEDUP_MAX_BPM_X10 - 1) //
                   self.PEAK_DEDUP_MAX_BPM_X10)

    def _find_peaks(self, data, size, min_height, min_distance, max_peaks):
        peaks = []
        index = 1

        while index < size - 1:
            if data[index] > min_height and data[index] > data[index - 1]:
                width = 1
                while (index + width) < size and data[index] == data[index + width]:
                    width += 1

                if (index + width) < size and data[index] > data[index + width]:
                    peaks.append(index)
                    index += width + 1
                else:
                    index += width
            else:
                index += 1

        for index in range(1, len(peaks)):
            value = peaks[index]
            insert = index
            while insert > 0 and data[value] > data[peaks[insert - 1]]:
                peaks[insert] = peaks[insert - 1]
                insert -= 1
            peaks[insert] = value

        selected = []

        for peak in peaks:
            keep = True
            for existing in selected:
                distance = peak - existing
                if -min_distance <= distance <= min_distance:
                    keep = False
                    break

            if keep:
                selected.append(peak)
                if len(selected) >= max_peaks:
                    break

        selected.sort()
        return selected

    def _run_window_algorithm(self, ir_buffer):
        ir_mean = sum(ir_buffer) // self.ALGO_WINDOW_SIZE
        work = [sample - ir_mean for sample in ir_buffer]
        dx_size = self.ALGO_WINDOW_SIZE - self.MA4_SIZE
        dx = [0] * dx_size

        for index in range(self.ALGO_WINDOW_SIZE - self.MA4_SIZE):
            total = (work[index] + work[index + 1] +
                     work[index + 2] + work[index + 3])
            work[index] = self._div_trunc(total, 4)

        for index in range(self.ALGO_WINDOW_SIZE - self.MA4_SIZE - 1):
            dx[index] = work[index + 1] - work[index]

        for index in range(self.ALGO_WINDOW_SIZE - self.MA4_SIZE - 2):
            dx[index] = self._div_trunc(dx[index] + dx[index + 1], 2)

        for index in range(self.ALGO_WINDOW_SIZE - len(self.HAMMING) - self.MA4_SIZE - 2):
            weighted_sum = 0
            for tap in range(len(self.HAMMING)):
                weighted_sum -= dx[index + tap] * self.HAMMING[tap]
            dx[index] = self._div_trunc(weighted_sum, 1146)

        threshold_count = self.ALGO_WINDOW_SIZE - len(self.HAMMING)
        threshold = 0
        for index in range(threshold_count):
            value = dx[index]
            threshold += value if value >= 0 else -value
        threshold //= threshold_count

        peaks = self._find_peaks(
            dx,
            threshold_count,
            threshold,
            self._min_peak_distance_samples(),
            self.MAX_PEAKS
        )
        peak_count = len(peaks)

        if peak_count < 2:
            return 0, False, peak_count

        intervals = []
        for index in range(1, peak_count):
            interval = peaks[index] - peaks[index - 1]
            if interval <= 0:
                return 0, False, peak_count
            intervals.append(interval)

        intervals.sort()
        interval_count = len(intervals)
        trimmed_first = 0
        trimmed_last = interval_count - 1

        if interval_count >= 4:
            trimmed_first = 1
            trimmed_last = interval_count - 2

        trimmed = intervals[trimmed_first:trimmed_last + 1]
        if not trimmed:
            return 0, False, peak_count

        trimmed_count = len(trimmed)

        if trimmed_count & 1:
            median_interval = trimmed[trimmed_count // 2]
        else:
            upper = trimmed_count // 2
            lower = upper - 1
            median_interval = (trimmed[lower] + trimmed[upper]) // 2

        if median_interval <= 0:
            return 0, False, peak_count

        good_intervals = []
        for interval in trimmed:
            delta = interval - median_interval
            if delta < 0:
                delta = -delta

            if delta * self.INTERVAL_JITTER_DENOMINATOR <= median_interval * self.INTERVAL_JITTER_NUMERATOR:
                good_intervals.append(interval)

        if len(good_intervals) * self.MIN_GOOD_INTERVAL_RATIO_DENOMINATOR < trimmed_count * self.MIN_GOOD_INTERVAL_RATIO_NUMERATOR:
            return 0, False, peak_count

        good_intervals.sort()
        good_count = len(good_intervals)

        if good_count & 1:
            final_interval = good_intervals[good_count // 2]
        else:
            upper = good_count // 2
            lower = upper - 1
            final_interval = (good_intervals[lower] + good_intervals[upper]) // 2

        if final_interval <= 0:
            return 0, False, peak_count

        bpm_x10 = (60 * self.sample_rate_hz * 10) // final_interval
        valid = self.MIN_BPM_X10 <= bpm_x10 <= self.MAX_BPM_X10
        return bpm_x10, valid, peak_count

    def feed_sample(self, ir_raw, sample_tick_ms=None):
        if sample_tick_ms is None:
            sample_tick_ms = utime.ticks_ms()

        self.latest_ir_raw = ir_raw
        self._update_raw_window(ir_raw)
        self._update_raw_stats()

        if self.raw_count:
            self.filtered_ir = int(ir_raw) - int(self.raw_mean)
        else:
            self.filtered_ir = 0

        was_contact_present = self.contact_present

        contact_acquire = (
            self.raw_mean >= self.CONTACT_MEAN_MIN and
            ir_raw >= self.CONTACT_INSTANT_MIN and
            self.raw_span >= self.SIGNAL_SPAN_MIN
        )
        contact_hold = (
            self.contact_present and
            self.raw_mean >= self.CONTACT_RELEASE_MEAN_MIN and
            ir_raw >= self.CONTACT_RELEASE_INSTANT_MIN and
            self.raw_span >= self.SIGNAL_RELEASE_SPAN_MIN and
            self.invalid_signal_streak < self.SIGNAL_RELEASE_HOLD_SAMPLES
        )

        if contact_acquire:
            self.contact_present = True
            self.invalid_signal_streak = 0

            if not was_contact_present:
                self.clear_window_tracking()
                self.contact_settling = True
                self.contact_settle_start_tick_ms = sample_tick_ms

        elif contact_hold:
            self.contact_present = True
            self.invalid_signal_streak += 1

        else:
            self.contact_present = False
            self.invalid_signal_streak = 0
            self.clear_window_tracking()
            self.contact_settling = False
            self.contact_settle_start_tick_ms = None
            self.status = self.STATUS_INVALID
            self.sample_index += 1
            return self.result()

        if self.contact_settling:
            settled_ms = utime.ticks_diff(sample_tick_ms, self.contact_settle_start_tick_ms)

            if settled_ms < self.CONTACT_SETTLE_MS:
                self.status = self.STATUS_SEARCHING
                self.sample_index += 1
                return self.result()

            self.contact_settling = False
            self.clear_window_tracking()

        self._push_ir_window_sample(ir_raw)

        if self.ir_window_count < self.ALGO_WINDOW_SIZE:
            self.status = self.STATUS_SEARCHING
            self.sample_index += 1
            return self.result()

        if self.last_valid_beat_tick_ms is not None:
            stale_ms = utime.ticks_diff(sample_tick_ms, self.last_valid_beat_tick_ms)

            if stale_ms > self.STALE_TIMEOUT_MS:
                self.tracking_streak = 0
                self.status = self.STATUS_SEARCHING

            if stale_ms > self.LAST_BPM_HOLD_TIMEOUT_MS:
                self.bpm_x10 = 0

        self.sample_index += 1
        return self.result()

    def calc_now(self):
        if self.ir_window_count < self.ALGO_WINDOW_SIZE:
            print("HR calc -> 数据不足，当前窗口: {}/{}".format(
                self.ir_window_count,
                self.ALGO_WINDOW_SIZE
            ))
            return self.result()

        sample_tick_ms = utime.ticks_ms()

        bpm_candidate_x10, bpm_valid, detected_peaks = self._run_window_algorithm(
            self._copy_linear_window()
        )
        self.beat_history_count = detected_peaks

        if not bpm_valid:
            if self.last_valid_beat_tick_ms is not None:
                stale_ms = utime.ticks_diff(sample_tick_ms, self.last_valid_beat_tick_ms)
            else:
                stale_ms = self.LAST_BPM_HOLD_TIMEOUT_MS + 1

            if self.bpm_x10 != 0 and stale_ms <= self.LAST_BPM_HOLD_TIMEOUT_MS:
                self.status = self.STATUS_TRACKING
            else:
                self.tracking_streak = 0
                self.status = self.STATUS_SEARCHING
                self.bpm_x10 = 0

            print("HR calc -> status={}, bpm=--, beats={}".format(
                self.status,
                self.beat_history_count
            ))
            return self.result()

        if self.last_valid_beat_tick_ms is None and bpm_candidate_x10 > self.STARTUP_MAX_BPM_X10:
            self.tracking_streak = 0
            self.status = self.STATUS_SEARCHING
            print("HR calc -> status={}, bpm=--, beats={}".format(
                self.status,
                self.beat_history_count
            ))
            return self.result()

        if self.bpm_x10 != 0 and bpm_candidate_x10 > (self.bpm_x10 + self.BPM_UP_JUMP_LIMIT_X10):
            self.status = self.STATUS_TRACKING
            bpm_text = "{}.{}".format(self.bpm_x10 // 10, self.bpm_x10 % 10) if self.bpm_x10 else "--"
            print("HR calc -> status={}, bpm={}, beats={}".format(
                self.status,
                bpm_text,
                self.beat_history_count
            ))
            return self.result()

        self._push_bpm_history(bpm_candidate_x10)
        bpm_candidate_x10 = self._median_bpm_history()

        if self.status == self.STATUS_TRACKING and self.bpm_x10 != 0:
            if bpm_candidate_x10 > self.bpm_x10:
                self.bpm_x10 = (self.bpm_x10 * 3 + bpm_candidate_x10 + 2) // 4
            else:
                self.bpm_x10 = (self.bpm_x10 + bpm_candidate_x10 * 3 + 2) // 4
        else:
            self.bpm_x10 = bpm_candidate_x10

        if self.tracking_streak < 255:
            self.tracking_streak += 1

        self.last_valid_beat_tick_ms = sample_tick_ms
        if self.tracking_streak >= self.TRACK_LOCK_COUNT:
            self.status = self.STATUS_TRACKING
        else:
            self.status = self.STATUS_SEARCHING

        bpm_text = "{}.{}".format(self.bpm_x10 // 10, self.bpm_x10 % 10) if self.bpm_x10 else "--"
        print("HR calc -> status={}, bpm={}, beats={}".format(
            self.status,
            bpm_text,
            self.beat_history_count
        ))
        return self.result()

    def result(self):
        return {
            "latest_ir_raw": self.latest_ir_raw,
            "raw_mean": self.raw_mean,
            "raw_span": self.raw_span,
            "filtered_ir": self.filtered_ir,
            "contact_present": self.contact_present,
            "finger_present": self.contact_present,
            "status": self.status,
            "bpm_x10": self.bpm_x10,
            "beat_history_count": self.beat_history_count,
            "window_fill": self.window_fill,
            "settling": self.contact_settling,
        }


class HeartRateMonitor:
    def __init__(self):
        self.i2c = None
        self.sensor = None
        self.estimator = None
        self.summary = None
        self.latest_red = 0
        self.latest_diag = (0, 0, 0, 0)
        self.latest_samples_read = 0
        self.overflowed_latched = False

    def start(self):
        self.i2c = try_make_i2c()
        self.sensor = MAX30102(self.i2c)
        self.sensor.setup()
        self.summary = self.sensor.summary()
        self.estimator = HeartRateEstimator(MAX30102.SAMPLE_RATE_HZ)
        self.latest_red = 0
        self.latest_diag = (0, 0, 0, 0)
        self.latest_samples_read = 0
        self.overflowed_latched = False

        print("MAX30102 已初始化")
        print("cfg: part=0x{:02X} rev=0x{:02X} mode=0x{:02X} fifo=0x{:02X} spo2=0x{:02X} red=0x{:02X} ir=0x{:02X}".format(
            self.summary["part"],
            self.summary["rev"],
            self.summary["mode"],
            self.summary["fifo"],
            self.summary["spo2"],
            self.summary["red_pa"],
            self.summary["ir_pa"]
        ))
        return self.summary

    def sample_and_feed(self):
        if self.sensor is None or self.estimator is None:
            raise RuntimeError("HeartRateMonitor.start() 还没有调用")

        samples, overflowed, diag = self.sensor.read_samples(MAX30102.FIFO_BATCH_SAMPLES)
        self.latest_diag = diag
        self.latest_samples_read = len(samples)

        if overflowed:
            self.overflowed_latched = True
            self.estimator.on_overflow()

        now_ms = utime.ticks_ms()

        for index, sample in enumerate(samples):
            red, ir = sample
            sample_tick_ms = utime.ticks_add(
                now_ms,
                -((len(samples) - 1 - index) * MAX30102.SAMPLE_PERIOD_MS)
            )
            self.latest_red = red
            self.estimator.feed_sample(ir, sample_tick_ms)

        return self.estimator.result()


_hr = None


def hr_init():
    global _hr
    _hr = HeartRateMonitor()
    return _hr.start()


def hr_sample_and_process():
    global _hr
    if _hr is None:
        raise RuntimeError("请先调用 hr_init()")
    return _hr.sample_and_feed()


def hr_calc_bpm():
    global _hr
    if _hr is None:
        raise RuntimeError("请先调用 hr_init()")

    hr_info = _hr.estimator.calc_now()

    bpm_x10 = hr_info.get("bpm_x10", 0)
    status = hr_info.get("status", "INVALID")

    if status == "TRACKING" and bpm_x10 > 0:
        return bpm_x10 / 10.0

    return 0.0






