# Control the brightness of Inky Frame's LEDs using PWM
# More about PWM / frequency / duty cycle here:
# https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/7

import machine
import time 
import math

led_activity = machine.PWM(machine.Pin(6))
print(led_activity)
led_activity.freq(1000)
print(led_activity)

led_connect = machine.PWM(machine.Pin(7))
print(led_connect)
led_connect.freq(1000)
print(led_connect)

def pulse(l, t):
    for i in range(200):
        l.duty_u16(int(math.sin(i / 10 * math.pi) * 500 + 500))
        time.sleep_ms(t)

pulse(led_activity, 1000)

# led_a = PWM(Pin(11))
# led_b = PWM(Pin(12))
# led_c = PWM(Pin(13))
# led_d = PWM(Pin(14))
# led_e = PWM(Pin(15))

# led_activity.freq(1000)

# leds = [led_a, led_b, led_c, led_d, led_e]

# led_activity.duty_u16(0)
# led_connect.duty_u16(0)

# n = 0
# while True:
#     leds[n].duty_u16(65025)
#     sleep(0.1)
#     leds[n].duty_u16(0)
#     n += 1
#     n %= len(leds)