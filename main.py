from cpu6502 import cpu6502

memory = [0]*(1<<16)
with open("./examples/main.bin", "rb") as f:
    i = 0
    while(byte := f.read(1)):
        memory[i] = int.from_bytes(byte)
        i+=1


cpu = cpu6502(memory)
for _ in range(1024):
    cpu.step()
    print(hex(cpu.PC))