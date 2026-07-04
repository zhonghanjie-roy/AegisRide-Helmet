import micropython
from pyb import Timer

micropython.alloc_emergency_exception_buf(100)

_tim2 = None

flag_40ms = 0
flag1_40ms = 0
flag_800ms = 0
flag_3s = 0
flag_1s = 0
flag_600s = 1

_tick_25hz = 0


def TIM2_IRQHandler(timer):
    global flag_40ms, flag1_40ms, flag_800ms, flag_3s, flag_1s, flag_600s
    global _tick_25hz

    flag_40ms = 1
    flag1_40ms = 1
    _tick_25hz += 1

    if (_tick_25hz % 20) == 0:
        flag_800ms = 1    
        
    if (_tick_25hz % 26) == 0:
        flag_1s = 1
    
    if (_tick_25hz % 76) == 0:
        flag_3s = 1
        flag1_40ms = 0
               
    if _tick_25hz >= 15000:
       flag_600s = 1 
       _tick_25hz = 0 
    

def tim():
    global _tim2
    _tim2 = Timer(2)
    _tim2.init(
        freq=25,
        callback=TIM2_IRQHandler,
        hard=False
    )


def tim_stop():
    global _tim2
    if _tim2 is not None:
        _tim2.callback(None)
        _tim2.deinit()
        _tim2 = None


