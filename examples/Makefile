compile: main.asm
	ca65 -o main.o main.asm
	ld65 -o main.bin -C linker.cfg main.o
cleanup: 
	rm main.o
	rm main.bin