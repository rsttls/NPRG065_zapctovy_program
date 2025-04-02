from cpu6502 import cpu6502
from monitor import monitor
from printer import printer
import threading
from sys import argv
# Create and load memory
Memory = [0]*(1<<16)

with open(argv[1], "rb") as f:
    i = 0
    while(byte := f.read(1)):
        Memory[i] = int.from_bytes(byte)
        i+=1

Cpu = cpu6502(Memory)
Monitor = monitor(Memory)
Printer = printer(Memory)

killThread2 = 0
def miscLoop():
    while(killThread2 == 0):
        # monitors 0x200 - 0x5FF and displays colors
        Monitor.update()
        # monitors 0xFF for character and if 0xFE == 1 then print character
        Printer.update()

thread2 = threading.Thread(target=miscLoop, daemon=True)
thread2.start()


while(Monitor.WindowOpen):
    # if this address is set than the program ends
    if(Memory[0xFE] == 127):
        break
    Cpu.step()

killThread2 = 1
thread2.join()