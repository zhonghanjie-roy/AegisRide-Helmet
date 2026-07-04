# MQTT_V3.py
# EC200U / QuecPython MQTT 长连接上传
# V3: 使用单次 socket.write 发送完整 MQTT QoS0 PUBLISH 报文，减少底层 QISEND 次数。
# 支持 Ctrl+C 后由 main.py 调用 mqtt_stop() 停止线程

import quectel
import utime
import _thread


try:
    import log
    log.basicConfig(log.ERROR)
except Exception:
    pass


try:
    from umqtt import robust
    MQTTClient = robust.MQTTClient
except Exception:
    from umqtt import simple
    MQTTClient = simple.MQTTClient


# =========================
# MQTT 配置
# =========================

MQTT_SERVER = "43.139.52.249"
MQTT_PORT = 1883

CLIENT_ID = "h001"
TOPIC = "h/1"


# =========================
# 线程控制变量
# =========================

_running = False
_mqtt_started = False

_client = None
_net = None


# =========================
# main.py 直接写入这些变量
# =========================

heart_rate = 0
temperature = 381
humidity = 536
longitude = 0
latitude = 0
speed = 0
collision = 0


# =========================
# 可中断 sleep
# =========================

def safe_sleep_ms(total_ms):
    global _running

    elapsed = 0
    step = 100

    while elapsed < total_ms:
        if not _running:
            break

        utime.sleep_ms(step)
        elapsed += step


# =========================
# 启动 MQTT 线程
# =========================

def mqtt_start():
    global _running
    global _mqtt_started

    if _mqtt_started:
        print("MQTT线程已经启动，不重复启动")
        return

    _running = True
    _mqtt_started = True

    try:
        _thread.stack_size(16 * 1024)
        print("MQTT线程栈设置为16KB")
    except Exception as e:
        print("设置MQTT线程栈失败:", e)

    _thread.start_new_thread(mqtt_task, ())


# =========================
# 停止 MQTT
# =========================

def mqtt_stop():
    global _running
    global _mqtt_started
    global _client
    global _net

    print("正在停止MQTT...")

    _running = False
    _mqtt_started = False

    if _client is not None:
        try:
            _client.disconnect()
            print("MQTT client disconnect OK")
        except Exception as e:
            print("MQTT disconnect异常:", e)

    if _net is not None:
        try:
            _net.deinit()
            print("Network deinit OK")
        except Exception as e:
            print("Network deinit异常:", e)

    print("MQTT停止请求已发送")


# =========================
# 构造上传数据
# =========================

def build_msg():
    global heart_rate
    global temperature
    global humidity
    global longitude
    global latitude
    global speed
    global collision

    msg = "%d,%d,%d,%d,%d,%d,%d" % (
        int(heart_rate),
        int(temperature),
        int(humidity),
        int(longitude),
        int(latitude),
        int(speed),
        int(collision)
    )

    return msg


# =========================
# MQTT V3 快速 QoS0 发布
# =========================

def to_mqtt_bytes(value):
    if isinstance(value, bytes):
        return value

    if isinstance(value, bytearray):
        return bytes(value)

    return str(value).encode()


def encode_remaining_length(length):
    encoded = bytearray()

    while True:
        digit = length % 128
        length = length // 128

        if length > 0:
            digit |= 0x80

        encoded.append(digit)

        if length == 0:
            break

    return encoded


def build_publish_packet(topic, msg):
    topic = to_mqtt_bytes(topic)
    msg = to_mqtt_bytes(msg)

    topic_len = len(topic)
    if topic_len > 65535:
        raise ValueError("topic too long")

    remaining_len = 2 + topic_len + len(msg)

    packet = bytearray()
    packet.append(0x30)
    packet.extend(encode_remaining_length(remaining_len))
    packet.append((topic_len >> 8) & 0xFF)
    packet.append(topic_len & 0xFF)
    packet.extend(topic)
    packet.extend(msg)

    return packet


def get_mqtt_socket(client):
    sock = getattr(client, "sock", None)

    if sock is None:
        sock = getattr(client, "_sock", None)

    return sock


def socket_write_all(sock, data):
    total = len(data)
    sent = sock.write(data)

    if sent is None:
        return True

    while sent < total:
        n = sock.write(data[sent:])

        if n is None:
            return True

        if n <= 0:
            raise OSError("socket write failed")

        sent += n

    return True


def fast_publish_qos0(client, topic, msg):
    sock = get_mqtt_socket(client)

    if sock is None:
        return client.publish(topic, msg, qos=0)

    packet = build_publish_packet(topic, msg)
    socket_write_all(sock, packet)
    return True


def publish_message(client, msg):
    return fast_publish_qos0(client, TOPIC, msg)


# =========================
# MQTT 主线程任务
# =========================

def mqtt_task():
    global _running
    global _mqtt_started
    global _client
    global _net

    print("MQTT线程启动，长连接模式")

    while _running:
        _client = None
        _net = None

        try:
            _net = quectel.Network()

            if not wait_network(_net, timeout_s=30):
                print("网络连接失败")

                try:
                    _net.deinit()
                except Exception:
                    pass

                if _running:
                    print("10秒后重试网络")
                    safe_sleep_ms(10000)

                continue

            if not _running:
                break

            print("创建MQTT客户端")

            _client = MQTTClient(
                client_id=CLIENT_ID,
                server=MQTT_SERVER,
                port=MQTT_PORT,
                keepalive=60
            )

            print("连接MQTT Broker...")

            try:
                ret = _client.connect(clean_session=True, timeout=10)
            except TypeError:
                ret = _client.connect(clean_session=True)

            print("MQTT connect返回:", ret)
            print("MQTT长连接建立成功")

            while _running:
                msg = build_msg()

                try:
                    publish_message(_client, msg)
                except Exception as e:
                    print("MQTT publish异常:", e)
                    break

                safe_sleep_ms(1000)

        except Exception as e:
            print("MQTT异常，准备重连:", e)

        finally:
            if _client is not None:
                try:
                    _client.disconnect()
                    print("MQTT已断开")
                except Exception:
                    pass

            if _net is not None:
                try:
                    _net.deinit()
                    print("Network deinitialized")
                except Exception:
                    pass

            _client = None
            _net = None

            if _running:
                print("10秒后重新建立网络和MQTT")
                safe_sleep_ms(10000)

    _mqtt_started = False
    print("MQTT线程已退出")


# =========================
# 等待网络连接
# =========================

def wait_network(net, timeout_s=30):
    global _running

    if not _running:
        return False

    print("初始化网络...")

    if not net.init():
        print("网络初始化失败")
        return False

    if not _running:
        return False

    print("检查SIM卡...")

    if not net.query_usim():
        print("SIM卡异常")
        return False

    if not _running:
        return False

    print("注册蜂窝网络...")

    try:
        net.attach()
    except Exception as e:
        print("attach异常:", e)

    print("等待网络连接...")

    start = utime.time()

    while _running and utime.time() - start < timeout_s:
        try:
            if net.is_connected():
                print("网络已连接")
                return True
        except Exception as e:
            print("is_connected异常:", e)

        safe_sleep_ms(1000)

    print("网络连接超时或被停止")
    return False

