from cpu6502 import cpu6502

memory = [0]*(1<<16)
cpu = cpu6502(memory)

with open("./examples/main.bin", "rb") as f:
    i = 0
    while(byte := f.read(1)):
        memory[i] = int.from_bytes(byte)
        i+=1
for _ in range(1024):
    cpu.step()
    cpu.step()
    print(cpu.A)
    if(cpu.C == 1):
        print("carry trigger")
    if(cpu.V == 1):
        print("overflow trigger")
    if(cpu.Z == 1):
        print("zero trigger")
    if(cpu.N == 1):
        print("negative trigger")
    