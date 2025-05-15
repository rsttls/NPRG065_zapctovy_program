
#include <stdint.h>

void setByte(uint16_t Address, uint8_t Value)
{
    *(volatile uint8_t *)Address = Value;
}

uint8_t readByte(uint16_t Address)
{
    return *(volatile uint8_t *)Address;
}

void prinfChar(char C)
{
    setByte(0xFF, C);
    setByte(0xFE, 1);
    while (readByte(0xFE) != 0)
        ;
}

void print(char *str)
{
    int i = 0;
    while (str[i] != 0)
    {
        prinfChar(str[i]);
        i++;
    }
}

void delay(short cycles)
{
    int i;
    for(i = 0; i < cycles; i++)
    {
        __asm__("NOP");
    }
}



void entry()
{
    // cc65 wants all variables declared before the code section
    char *hi = "This a red square walking on the screen\n";
    unsigned short i = 0;
    print(hi);
    while (1)
    {
        setByte(0x200 + i, 0x0);
        i = (i + 1) % (32 * 32);
        setByte(0x200 + i, 0xE0);
        delay(100);
    }
}