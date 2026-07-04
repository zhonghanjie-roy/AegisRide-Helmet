# gnss.py

import quectel
import utime
import _thread

_gnss = None
_running = False
_started = False

_lock = _thread.allocate_lock()

_fix = False
_latitude = 0.0
_longitude = 0.0
_speed_kmh = 0.0
_raw_speed_kmh = 0.0
_satellites = 0
_fix_mode = ""
_altitude = 0.0
_cog = 0.0
_last_cost_ms = 0
_update_count = 0
_last_error = ""

# 固定 800ms 读取一次
READ_INTERVAL_MS = 800

# 默认不在 gnss.py 内部打印，避免刷屏
GNSS_DEBUG = False

# ====== 速度滤波参数 ======
_SPEED_BUF = []
_SPEED_BUF_LEN = 5

STOP_THRESHOLD = 1.5
MOVE_THRESHOLD = 2.5

_stop_count = 0
_move_count = 0
_is_moving = False


def safe_sleep_ms(total_ms):
    global _running

    elapsed = 0
    step = 50

    while elapsed < total_ms:
        if not _running:
            break

        utime.sleep_ms(step)
        elapsed += step


def _avg_speed():
    if not _SPEED_BUF:
        return 0.0

    return sum(_SPEED_BUF) / len(_SPEED_BUF)


def _filter_speed(raw_speed):
    global _stop_count, _move_count, _is_moving

    _SPEED_BUF.append(raw_speed)

    if len(_SPEED_BUF) > _SPEED_BUF_LEN:
        _SPEED_BUF.pop(0)

    avg = _avg_speed()

    if _is_moving:
        if avg < STOP_THRESHOLD:
            _stop_count += 1
            _move_count = 0

            if _stop_count >= 3:
                _is_moving = False
                _stop_count = 0
                return 0.0
        else:
            _stop_count = 0

        return avg

    else:
        if avg > MOVE_THRESHOLD:
            _move_count += 1
            _stop_count = 0

            if _move_count >= 2:
                _is_moving = True
                _move_count = 0
                return avg
        else:
            _move_count = 0

        return 0.0


def _read_once():
    global _fix, _latitude, _longitude, _speed_kmh, _raw_speed_kmh
    global _satellites, _fix_mode, _altitude, _cog
    global _last_cost_ms, _update_count, _last_error

    if _gnss is None:
        return 0

    t0 = utime.ticks_ms()

    try:
        # 主要耗时就在这里，约 68ms
        loc = _gnss.get_location()
        cost = utime.ticks_diff(utime.ticks_ms(), t0)

        if loc:
            lat = loc.get("latitude", 0.0) or 0.0
            lon = loc.get("longitude", 0.0) or 0.0
            raw_speed = loc.get("speed_kmh", 0.0) or 0.0
            filtered_speed = _filter_speed(raw_speed)
            satellites = loc.get("satellites", 0) or 0
            fix_mode = loc.get("fix_mode", "") or ""
            altitude = loc.get("altitude", 0.0) or 0.0
            cog = loc.get("cog", 0.0) or 0.0

            _lock.acquire()
            try:
                _fix = True
                _latitude = lat
                _longitude = lon
                _raw_speed_kmh = raw_speed
                _speed_kmh = filtered_speed
                _satellites = satellites
                _fix_mode = fix_mode
                _altitude = altitude
                _cog = cog
                _last_cost_ms = cost
                _update_count += 1
                _last_error = ""
            finally:
                _lock.release()

            return 1

        else:
            _lock.acquire()
            try:
                _fix = False
                _raw_speed_kmh = 0.0
                _speed_kmh = 0.0
                _satellites = 0
                _last_cost_ms = cost
                _update_count += 1
                _last_error = ""
            finally:
                _lock.release()

            return 0

    except Exception as e:
        cost = utime.ticks_diff(utime.ticks_ms(), t0)

        _lock.acquire()
        try:
            _fix = False
            _raw_speed_kmh = 0.0
            _speed_kmh = 0.0
            _last_cost_ms = cost
            _update_count += 1
            _last_error = str(e)
        finally:
            _lock.release()

        if GNSS_DEBUG:
            print("GNSS read error:", e)

        return 0


def _worker():
    global _gnss, _running, _started

    print("GNSS线程启动")

    try:
        _gnss = quectel.GNSS()

        if not _running:
            return

        if not _gnss.start():
            print("GNSS start failed")
            return

        print("GNSS started")

        while _running:
            loop_start = utime.ticks_ms()

            _read_once()

            if GNSS_DEBUG:
                data = GNSS_GetData()
                print(
                    "GNSS cost={}ms, fix={}, lat={:.6f}, lon={:.6f}, sat={}".format(
                        data["cost_ms"],
                        data["fix"],
                        data["latitude"],
                        data["longitude"],
                        data["satellites"]
                    )
                )

            # 固定 800ms 周期
            cost = utime.ticks_diff(utime.ticks_ms(), loop_start)
            wait_ms = READ_INTERVAL_MS - cost

            if wait_ms > 0:
                safe_sleep_ms(wait_ms)
            else:
                utime.sleep_ms(0)

    finally:
        try:
            if _gnss is not None:
                _gnss.stop()
                print("GNSS stop OK")
        except Exception as e:
            print("GNSS stop error:", e)

        _gnss = None
        _running = False
        _started = False
        print("GNSS线程已退出")


def GNSS_Start():
    global _running, _started

    if _started:
        print("GNSS线程已经启动，不重复启动")
        return 1

    _running = True
    _started = True

    try:
        _thread.stack_size(8 * 1024)
    except Exception as e:
        print("设置GNSS线程栈失败:", e)

    _thread.start_new_thread(_worker, ())

    return 1


def GNSS_Stop():
    global _running
    global _gnss

    print("正在停止GNSS...")

    _running = False

    # 主动 stop，尽量打断 GNSS 内部状态
    try:
        if _gnss is not None:
            _gnss.stop()
            print("GNSS stop请求已发送")
    except Exception as e:
        print("GNSS stop请求异常:", e)

    print("GNSS停止请求已发送")


def GNSS_GetData():
    _lock.acquire()
    try:
        return {
            "fix": _fix,
            "latitude": _latitude,
            "longitude": _longitude,
            "raw_speed_kmh": _raw_speed_kmh,
            "speed_kmh": _speed_kmh,
            "satellites": _satellites,
            "fix_mode": _fix_mode,
            "altitude": _altitude,
            "cog": _cog,
            "cost_ms": _last_cost_ms,
            "update_count": _update_count,
            "last_error": _last_error,
        }
    finally:
        _lock.release()

