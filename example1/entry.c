
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
    while (readByte(0xFE) == 1)
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

void entry()
{
    char *hi = "Hello world from C\n";
    unsigned short x;
    unsigned short y;
    int i = 0;
    print(hi);
    while (1)
    {
        for (y = 0; y < 32; y++)
        {
            for (x = 0; x < 32; x++)
            {
                setByte(0x200 + (y * 32) + x, ((x ^ y) + i) & 0xFF);
            }
        }
        i+=16;
    }
}