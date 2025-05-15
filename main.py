from cpu6502 import cpu6502
from monitor import monitor
from printer import printer
import pygame
import pygame.locals
import threading
from sys import argv
# Create memory
Memory = [0]*(1<<16)

# Load file into memory
with open(argv[1], "rb") as f:
    i = 0
    while(byte := f.read(1)):
        Memory[i] = int.from_bytes(byte)
        i+=1
# Create objects
Cpu = cpu6502(Memory)
Monitor = monitor(Memory,Scale=2)
Printer = printer(Memory)


# Multithreading
killThread2 = 0
def miscLoop():
    """
        A function to offload the monitor and printer updates to another thread
    """
    while(killThread2 == 0):
        # monitors 0x200 - 0x5FF and displays colors
        Monitor.update()
        # monitors 0xFF for character and if 0xFE == 1 then print character
        Printer.update()

thread2 = threading.Thread(target=miscLoop, daemon=True)
thread2.start()


# Main loop
while(Monitor.WindowOpen):
    # if this address is set to 127 than the program ends
    if(Memory[0xFE] == 127):
        break
    # pygame wants events in main thread
    for event in pygame.event.get():
        if event.type == pygame.locals.QUIT:
            Monitor.WindowOpen = 0
    # using step function instead of cycle to speed up the cpu
    Cpu.step()

killThread2 = 1
thread2.join()