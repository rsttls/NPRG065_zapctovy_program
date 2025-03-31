class cpu6502:
    ### @param1 memory reference
    def __init__(Self, memory: list):
        Self.memory = memory
        # cycles measure how many cycles to wait
        Self.Cycles = 0
        # Accumulator
        Self.A = 0
        # X, Y registers
        Self.X = 0
        Self.Y = 0
        # Stack Pointer
        Self.SP = 0xFF
        # Program counter(defaultly we set 0x8000)
        Self.PC = 0x8000
        # $FFFA, $FFFB ... NMI (Non-Maskable Interrupt) vector, 16-bit (LB, HB)
        Self.NMI = 0xFFFA
        # $FFFC, $FFFD ... RES (Reset) vector, 16-bit (LB, HB)
        Self.RES = 0xFFFC
        # $FFFE, $FFFF ... IRQ (Interrupt Request) vector, 16-bit (LB, HB)
        Self.IRQ = 0xFFFE
        # Flags
        # N	Negative
        Self.N = 0
        # V	Overflow
        Self.V = 0
        # B	Break
        Self.B = 0
        # D	Decimal (use BCD for arithmetics)
        Self.D = 0
        # I	Interrupt (IRQ disable)
        Self.I = 0
        # Z	Zero
        Self.Z = 0
        # C	Carry
        Self.C = 0

    # reads 16bits
    def _readShort(Self, Address: int, zeropage:int = 0) -> int:
        if zeropage == 0:
            return Self.memory[Address&0xFFFF] + (Self.memory[(Address + 1) & 0xFFFF] << 8)
        else: # if we have 0xFF in zeropage than the next address is 0x00
            return Self.memory[Address&0xFF] + (Self.memory[(Address + 1) & 0xFF] << 8)
            

    # writes 16bits
    def _writeShort(Self, Address: int, Value: int, zeropage:int = 0):
        if zeropage == 0:
            Self.memory[Address & 0xFFFF] = Value & 0xFF
            Self.memory[(Address + 1) & 0xFFFF] = (Value >> 8) & 0xFF
        else: # if we have 0xFF in zeropage than the next address is 0x00
            Self.memory[Address & 0xFF] = Value & 0xFF
            Self.memory[(Address + 1) & 0xFF] = (Value >> 8) & 0xFF


    # updates flags N,Z based on value operated on
    def _updateNZ(Self, Value: int):
        Self.Z = 1 if (Value & 0xFF == 0) else 0
        Self.N = 1 if (Value & 0x80 != 0) else 0

    def _ADCFlags(Self, Original:int, Value: int):
        Self._updateNZ(Value)
        # unsigned overflow 255 + 1 = 0
        Self.C = 1 if Value >= 256 else 0
        # signed overflow 127 + 1 = -128
        Self.V = 1 if Original <= 127 and Value > 127 else 0


    def step(Self):
        match Self.memory[Self.PC]:
            case 0x69: # ADC immediate
                Self.Cycles = 2
                A = Self.A + Self.memory[Self.PC + 1] + Self.C
                Self._ADCFlags(Self.A, A)
                Self.A = A & 0xFF
                Self.PC += 2
            case 0x65: # ADC zeropage
                Self.Cycles = 3
                p = Self.memory[Self.PC + 1] # address in zeropage
                A = Self.A + Self.memory[p] + Self.C
                Self._ADCFlags(Self.A, A)
                Self.A = A & 0xFF
                Self.PC += 2
            case 0x75: # ADC zeropage, X
                Self.Cycles = 4
                p = Self.memory[Self.PC + 1] + Self.X  # address in zeropage + X
                p = p & 0xFF
                A = Self.A + Self.memory[p] + Self.C
                Self._ADCFlags(Self.A, A)
                Self.A = A & 0xFF
                Self.PC += 2
            case 0x6D: #ADC absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1) # address
                A = Self.A + Self.memory[p] + Self.C
                Self._ADCFlags(Self.A, A)
                Self.A = A & 0xFF
                Self.PC += 3
            case 0x7D: #ADC absolute,X
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1) + Self.X # address + X
                if(Self._readShort(Self.PC + 1) & 0xFF00 < p): # if the high byte increases add 1 to cycle
                    Self.Cycles+=1
                A = Self.A + Self.memory[p] + Self.C
                Self._ADCFlags(Self.A, A)
                Self.A = A & 0xFF
                Self.PC += 3
            case 0x79: #ADC absolute,Y
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1) + Self.Y # address + Y
                if(Self._readShort(Self.PC + 1) & 0xFF00 < p & 0xFF00): # if the high byte increases add 1 to cycle
                    Self.Cycles+=1
                A = Self.A + Self.memory[p] + Self.C
                Self._ADCFlags(Self.A, A)
                Self.A = A & 0xFF
                Self.PC += 3
            case 0x61: # ADC (indirect, X)
                Self.Cycles = 6
                pp = Self.memory[Self.PC + 1] + Self.X
                pp = pp & 0xFF
                p = Self._readShort(pp, zeropage=1)
                A = Self.A + Self.memory[p] + Self.C
                Self._ADCFlags(Self.A, A)
                Self.A = A & 0xFF
                Self.PC += 2
            case 0x71: # ADC (indirect), Y
                Self.Cycles = 5
                p = Self._readShort(Self.memory[Self.PC + 1], zeropage=1) + Self.Y
                if (Self._readShort(Self.memory[Self.PC + 1], zeropage=1) & 0xFF00 < p&0xFF00): # if the high byte increases add 1 to cycle
                    Self.Cycles+=1
                A = Self.A + Self.memory[p] + Self.C
                Self._ADCFlags(Self.A, A)
                Self.A = A & 0xFF
                Self.PC += 2

            case 0x4C:  # jmp absolute
                Self.Cycles = 3
                Self.PC = Self._readShort(Self.PC + 1)
            case 0x6C:  # jmp indirect
                Self.Cycles = 5
                # p address of value where to jmp
                p = Self._readShort(Self.PC + 1)
                Self.PC = Self._readShort(p)
