compile: main.asm
	ca65 -o main.o main.asm
	cc65 -o entry.asm entry.C
	ca65 -o entry.o entry.asm
	ld65 -o main.bin -C linker.cfg main.o entry.o ../cc65/lib/none.lib
cleanup: 
	rm main.o
	rm main.bin
	rm entry.asm
	rm entry.o