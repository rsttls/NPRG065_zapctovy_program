# NPRG065_zapctovy_program

# Running programs

To run a program you need a binary file which is loaded as is. So 0x00(File) -> 0x00(Memory) and the starting address (PC register) is set to the reset vector (0xFFFC)lowbyte and (0xFFFD)highbyte.

There are special addresses like 0x200 - 0x5FF which is the graphics memory.
Then 0xFF where you can store a character and 0xFE is a "instruction byte" if set to 1 python prints the character at 0xFF and sets it back to 0 or if set 127 then the program terminates.

To run the examples use 
```bash
python main.py example3/main.bin
```


# cc65

cc65 is a compiler for 6502. To use it here just add cc65/bin to PATH and you can make the example.
In c it is a basic entry point function called void entry(void).

# Cycles

There a call for cpu6502.cycle() which accounts for accurate timing but we are not using it in this example.