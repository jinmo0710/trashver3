# main.py로 저장
import bluetooth
import gc  # 메모리 관리를 위한 가비지 컬렉터 모듈
import utime
from ble_simple_peripheral import BLESimplePeripheral
from machine import PWM, Pin

# 1. BLE 객체 생성 및 초기화
ble = bluetooth.BLE()
sp = BLESimplePeripheral(ble)

# 2. 보드 내장 LED
led = Pin("LED", Pin.OUT)
led.value(1)

# 3. GP 핀 설정 (GP0 ~ GP5)
ena = PWM(Pin(0))
enb = PWM(Pin(5))
ena.freq(1000)
enb.freq(1000)

m1 = Pin(1, Pin.OUT)  # IN1
m2 = Pin(2, Pin.OUT)  # IN2
m3 = Pin(3, Pin.OUT)  # IN3
m4 = Pin(4, Pin.OUT)  # IN4

# 모터 속도 밸런스 설정
LEFT_SPEED = 52000
RIGHT_SPEED = 60000

# 원본 바이트 데이터를 담을 변수
latest_data = None


def set_motors_speed(l_speed, r_speed):
    l_val = min(65535, int(l_speed))
    r_val = min(65535, int(r_speed))
    ena.duty_u16(l_val)
    enb.duty_u16(r_val)


# ==========================================
# 주행 제어 함수 모음
# ==========================================
def go():
    m1.value(1)
    m2.value(0)
    m3.value(0)
    m4.value(1)
    set_motors_speed(LEFT_SPEED, RIGHT_SPEED)


def back():
    m1.value(0)
    m2.value(1)
    m3.value(1)
    m4.value(0)
    set_motors_speed(LEFT_SPEED, RIGHT_SPEED)


def left():
    m1.value(0)
    m2.value(1)
    m3.value(0)
    m4.value(1)
    set_motors_speed(LEFT_SPEED, RIGHT_SPEED * 1.2)


def right():
    m1.value(1)
    m2.value(0)
    m3.value(1)
    m4.value(0)
    set_motors_speed(LEFT_SPEED * 1.2, RIGHT_SPEED)


def stop():
    m1.value(0)
    m2.value(0)
    m3.value(0)
    m4.value(0)
    set_motors_speed(0, 0)


def toggle_led():
    led.value(not led.value())


stop()


# 4. 블루투스 콜백 (변환 없이 원본 바이트만 저장 - 메모리 할당 0)
def on_rx(data):
    global latest_data
    latest_data = data


sp.on_write(on_rx)

# 5. 메인 루프
print("BLE 연결 대기 중...")
gc_counter = 0

while True:
    if sp.is_connected():
        led.value(1)

        # 처리할 데이터가 있는 경우
        if latest_data is not None:
            raw = latest_data
            latest_data = None  # 즉시 비우기

            # decode 없이 바이트 단위 직접 비교 (b'...' 형식)
            if b"go" in raw:
                go()
            elif b"back" in raw:
                back()
            elif b"left" in raw:
                left()
            elif b"right" in raw:
                right()
            elif b"stop" in raw:
                stop()
            elif b"my" in raw:
                go()
                utime.sleep_ms(2000)
                stop()
                utime.sleep_ms(100)
                right()
                utime.sleep_ms(1000)
                stop()
                utime.sleep_ms(100)
                go()
                utime.sleep_ms(1000)
                stop()
            elif b"led" in raw:
                toggle_led()
    else:
        stop()
        latest_data = None
        led.value(0)

    # 메모리 자동 정리 (루프 50회마다 수동 GC 실행)
    gc_counter += 1
    if gc_counter >= 50:
        gc.collect()
        gc_counter = 0

    utime.sleep_ms(5)
