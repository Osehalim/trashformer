#!/usr/bin/env python3
import time
import pygame

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    raise RuntimeError("No joystick found")

js = pygame.joystick.Joystick(0)
js.init()

print(f"Controller: {js.get_name()}")
print(f"Axes: {js.get_numaxes()}")
print("Move the sticks. Press Ctrl+C to quit.\n")

try:
    while True:
        pygame.event.pump()
        values = []
        for i in range(js.get_numaxes()):
            v = js.get_axis(i)
            values.append(f"axis {i}: {v:+.3f}")
        print(" | ".join(values), end="\r", flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nDone.")
    pygame.quit()