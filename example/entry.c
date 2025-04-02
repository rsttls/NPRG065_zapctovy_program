
#include <stdint.h>

void setByte(uint16_t Address, uint8_t Value)
{
    *(volatile uint8_t*)Address = Value;
}

uint8_t readByte(uint16_t Address)
{
    return *(volatile uint8_t*)Address;
}


void prinfChar(char C)
{
    setByte(0xFF, C);
    setByte(0xFE, 1);
    while(readByte(0xFE) == 1);
}

void print(char* str)
{
    int i = 0;
    while(str[i] != 0)
    {
        prinfChar(str[i]);
        setByte(0x200+i,255);
        i++;
    }
}


void entry()
{
    char* hi = "Hello world\n";
    print(hi);
}