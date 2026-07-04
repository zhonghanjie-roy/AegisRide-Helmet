# main.py

import utime
import bmi160
import tim2
import gnss
import MQTT_V3 as mqtt
import temp_humi

from Head_rate import hr_init, hr_sample_and_process, hr_calc_bpm

from machine import Pin
from i2c_init import I2C1_Init
from buzzer import Buzzer_Init, Buzzer_ON, Buzzer_OFF


# B1 USER，按下 = 低电平
button = Pin("PC13", Pin.IN)


def scale_int(value, scale):
    """
    把小数放大成整数。
    例如：
    38.1 * 10 -> 381
    1.23 * 100 -> 123
    """
    if value >= 0:
        return int(value * scale + 0.5)
    else:
        return int(value * scale - 0.5)


def main():
    I2C1_Init()
    Buzzer_Init()

    if bmi160.BMI160_Init(bmi160.current_acc_range, bmi160.current_gyr_range):
        print("BMI160 Init OK")
    else:
        print("BMI160 Init Fail")
        while True:
            utime.sleep_ms(100)

    # 先开 MQTT 后台线程
    mqtt.mqtt_start()

    # 再开定时器
    tim2.tim()

    # 初始化心率模块
    hr_init()
    
    # 启动 GNSS
    if gnss.GNSS_Start():
        print("GNSS Start OK")
    else:
        print("GNSS Start Fail")
        
    # 初始化温湿度模块
    try:
        temp_humi.init_temp_humi()
    except Exception as e:
        print("AHT20 Init Fail:", e)
        
    latest_hr = 0.0
    latest_latitude = 0.0
    latest_longitude = 0.0
    latest_speed = 0.0
    latest_temp = 0.0
    latest_humi = 0.0
    force_read_temp_humi = 0

    # =========================
    # 省电模式变量
    # save_cnt：长按计数器
    # save_flag：1=正常模式，0=省电模式
    #
    # save_cnt = 0：没有按下，等待计时
    # save_cnt > 0：正在长按计时
    # save_cnt = -1：已经触发过一次，等松手
    # =========================
    save_cnt = 0
    save_flag = 1
    
    print("main loop start")

    while True:

        # =========================
        # 40ms：碰撞检测
        # 任何模式都运行
        # =========================
        if tim2.flag_40ms:
            tim2.flag_40ms = 0

            bmi160.caculate_collisions()
            
            # 调试阶段可以打印，正式运行建议注释掉
            #print("acc_x={:.3f}, acc_y={:.3f}, acc_z={:.3f}, gyr_x={:.3f}, gyr_y={:.3f}, gyr_z={:.3f}".format(
            #     bmi160.data.acc_x * 8 / 32768,
            #     bmi160.data.acc_y * 8 / 32768,
            #     bmi160.data.acc_z * 8 / 32768,
            #     bmi160.data.gyr_x * 2000 / 32768,
            #     bmi160.data.gyr_y * 2000 / 32768,
            #     bmi160.data.gyr_z * 2000 / 32768
            #))

            # 报警锁存：只要 st_flag = 1，就一直响
            if bmi160.st_flag == 1:
                Buzzer_ON()

            # 注意：
            # 你前面写的是“B1 USER，按下 = 高电平”
            # 所以这里应该是 button.value() == 1
            #
            # 如果你实际测试是“按下 = 低电平”，
            # 这里要改成 button.value() == 0
            if button.value() == 1:
                bmi160.st_flag = 0
                Buzzer_OFF()

                # =========================
                # 长按 2 秒切换省电/正常模式
                # 40ms 一次
                # 50 次 = 2 秒
                # =========================
                if save_cnt >= 0:
                    save_cnt += 1

                    if save_cnt >= 50:
                        if save_flag == 1:
                            save_flag = 0
                            print("进入省电模式：只运行碰撞检测和MQTT")
                        else:
                            save_flag = 1
                            force_read_temp_humi = 1
                            print("恢复正常模式：心率/GNSS/温湿度恢复运行")

                        # 锁住，防止一直按住反复切换
                        save_cnt = -1

            else:
                # 松手后清零，下一次长按才会重新计时
                save_cnt = 0

        # =========================
        # 40ms：心率采样
        # 省电模式下不运行
        # =========================
        if tim2.flag1_40ms:
            tim2.flag1_40ms = 0

            if save_flag == 1:
                hr_sample_and_process()

        # =========================
        # 3s：计算心率 BPM
        # 省电模式下不运行
        # =========================
        if tim2.flag_3s:
            tim2.flag_3s = 0

            if save_flag == 1:
                bpm = hr_calc_bpm()

                if bpm is not None:
                    latest_hr = bpm

                # 调试用
                # print("latest_hr =", latest_hr)
        
        # =========================
        # 600s：读取温湿度
        # 省电模式下不运行
        # 加个省点模式退出后，根据force_read_temp_humi=1强行读取一次温湿度
        # =========================
        if tim2.flag_600s or force_read_temp_humi:
            tim2.flag_600s = 0
            force_read_temp_humi = 0

            if save_flag == 1:
                try:
                    temp, humi = temp_humi.read_temp_humidity()
                    latest_temp = temp
                    latest_humi = humi

                    print("AHT20:",
                          "temp=", latest_temp,
                          "humi=", latest_humi)

                except Exception as e:
                    print("AHT20读取异常:", e)

        # =========================
        # 800ms：读取 GNSS 缓存
        # 省电模式下不运行
        # =========================
        if tim2.flag_800ms:
            tim2.flag_800ms = 0

            if save_flag == 1:
                try:
                    data = gnss.GNSS_GetData()

                    latest_latitude = data["latitude"]
                    latest_longitude = data["longitude"]
                    latest_speed = data["speed_kmh"] / 3.6

                    # 调试阶段可以打开
                    print(
                        "GNSS cache: cost={}ms, fix={}, lat={:.6f}, lon={:.6f}, speed={:.2f}m/s, sat={}".format(
                            data["cost_ms"],
                            data["fix"],
                            data["latitude"],
                            data["longitude"],
                            latest_speed,
                            data["satellites"]
                        )
                    )

                except Exception as e:
                    print("GNSS读取缓存异常:", e)

        # =========================
        # 
        # 省电模式下我把湿度置为0，小程序根据此判断
        # =========================
        if save_flag == 0:
            latest_humi = 0

            

        # =========================
        # 1s：把最新数据写入 mqtt.py
        # MQTT线程会自己读取并发布
        # 省电模式下也运行
        # =========================
        if tim2.flag_1s:
            tim2.flag_1s = 0

            mqtt.heart_rate = int(latest_hr)*10

            # 这里温湿度你目前是固定值
            mqtt.temperature = int(latest_temp* 10)
            mqtt.humidity = int(latest_humi* 10)

            # 经纬度放大 1000000 倍
            mqtt.longitude = int(latest_longitude*1000000)
            mqtt.latitude = int(latest_latitude* 1000000)

            # 速度单位 m/s，放大 100 倍
            mqtt.speed = int(latest_speed* 100)

            # 碰撞状态 0/1
            mqtt.collision = int(bmi160.st_flag)

            # 调试用，正式运行可以注释掉
            print("已写入MQTT数据:",
                  mqtt.heart_rate,
                  mqtt.temperature,
                  mqtt.humidity,
                  mqtt.longitude,
                  mqtt.latitude,
                  mqtt.speed,
                  mqtt.collision)
          
        # 关键：
        # 给 MQTT 后台线程让出 CPU
        utime.sleep_ms(0)


try:
    main()

except KeyboardInterrupt:
    print("收到 Ctrl+C，正在停止程序")
    
    try:
        gnss.GNSS_Stop()
    except Exception as e:
        print("停止GNSS异常:", e)
     
    try:
        mqtt.mqtt_stop()
    except Exception as e:
        print("停止 MQTT 异常:", e)

    try:
        Buzzer_OFF()
    except Exception:
        pass

    print("程序已停止")

except Exception as e:
    print("main 异常:", e)

    try:
        mqtt.mqtt_stop()
    except Exception:
        pass

    try:
        Buzzer_OFF()
    except Exception:
        pass

