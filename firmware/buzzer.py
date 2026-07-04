from machine import Pin

_buzzer = None


def Buzzer_Init():
    """
    PB12
    低电平响，高电平不响
    """
    global _buzzer

    if hasattr(Pin, "OUT_PP"):
        _buzzer = Pin("PB12", Pin.OUT_PP)
    else:
        _buzzer = Pin("PB12", Pin.OUT)

    # 默认关闭蜂鸣器，避免上电就响
    _buzzer.high()


def _Buzzer_CheckInit():
    global _buzzer
    if _buzzer is None:
        Buzzer_Init()


def Buzzer_ON():
    """
    低电平响
    """
    _Buzzer_CheckInit()
    _buzzer.low()


def Buzzer_OFF():
    """
    高电平不响
    """
    _Buzzer_CheckInit()
    _buzzer.high()


def Buzzer_TOGGLE():
    _Buzzer_CheckInit()
    if _buzzer.value() == 0:
        _buzzer.high()
    else:
        _buzzer.low()


