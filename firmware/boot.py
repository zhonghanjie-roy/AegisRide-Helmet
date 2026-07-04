# boot.py -- run on boot to configure USB and filesystem
# Put app code in main.py

import machine
import pyb
#pyb.main('main.py') # main script to run after this one
# boot.py -- run on boot


# 可选：延时 1 秒，方便你上电后用 Thonny 按 Ctrl+C 中断
pyb.delay(1000)

# 指定上电后运行 main.py
pyb.main('main.py')