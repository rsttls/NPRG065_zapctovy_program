def unsignedToSigned8bit(Value: int) -> int:
    return (Value - 256) if Value & 0x80 else Value


def signedToUnsigned8bit(Value: int) -> int:
    return Value & 0xFF


class cpu6502:
    ### @param1 memory reference
    def __init__(Self, memory: list):
        Self.Memory = memory
        # cycles measure how many cycles to wait
        Self.Cycles = 0
        # Accumulator
        Self.A = 0
        # X, Y registers
        Self.X = 0
        Self.Y = 0
        # Stack Pointer
        Self.SP = 0xFF
        # $FFFA, $FFFB ... NMI (Non-Maskable Interrupt) vector, 16-bit (LB, HB)
        Self.NMI = 0xFFFA
        # $FFFC, $FFFD ... RES (Reset) vector, 16-bit (LB, HB)
        Self.RES = 0xFFFC
        # $FFFE, $FFFF ... IRQ (Interrupt Request) vector, 16-bit (LB, HB)
        Self.IRQ = 0xFFFE
        # Program counter(defaultly set reser vector)
        Self.PC = Self._readShort(Self.RES)
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
    def _readShort(Self, Address: int, zeropage: int = 0) -> int:
        if zeropage == 0:
            return Self.Memory[Address & 0xFFFF] + (
                Self.Memory[(Address + 1) & 0xFFFF] << 8
            )
        else:  # if we have 0xFF in zeropage than the next address is 0x00
            return Self.Memory[Address & 0xFF] + (
                Self.Memory[(Address + 1) & 0xFF] << 8
            )

    # writes 16bits
    def _writeShort(Self, Address: int, Value: int, zeropage: int = 0):
        if zeropage == 0:
            Self.Memory[Address & 0xFFFF] = Value & 0xFF
            Self.Memory[(Address + 1) & 0xFFFF] = (Value >> 8) & 0xFF
        else:  # if we have 0xFF in zeropage than the next address is 0x00
            Self.Memory[Address & 0xFF] = Value & 0xFF
            Self.Memory[(Address + 1) & 0xFF] = (Value >> 8) & 0xFF

    def _push(Self, Value: int):
        Self.Memory[Self.SP + 0x100] = Value
        Self.SP = (Self.SP - 1) & 0xFF

    def _pull(Self) -> int:
        Self.SP = (Self.SP + 1) & 0xFF
        return Self.Memory[Self.SP + 0x100]

    # more coplicated addressing modes
    def _addressingZeropageX(Self, Address: int):
        p = Self.Memory[Address] + Self.X  # address in zeropage + X
        return p & 0xFF

    def _addressingZeropageY(Self, Address: int):
        p = Self.Memory[Address] + Self.Y  # address in zeropage + Y
        return p & 0xFF

    def _addressingAbsoluteX(Self, Address: int):
        orig = Self._readShort(Address)
        p = orig + Self.X  # address + X
        if orig & 0xFF00 != p & 0xFF00:  # if the high byte increases add 1 to cycle
            Self.Cycles += 1
        return p & 0xFFFF

    def _addressingAbsoluteY(Self, Address: int):
        orig = Self._readShort(Address)
        p = orig + Self.Y  # address + Y
        if orig & 0xFF00 != p & 0xFF00:  # if the high byte increases add 1 to cycle
            Self.Cycles += 1
        return p & 0xFFFF

    def _addressingIndirectX(Self, Address: int):
        pp = Self.Memory[Address] + Self.X
        pp = pp & 0xFF
        return Self._readShort(pp, zeropage=1)

    def _addressingIndirectY(Self, Address: int):
        orig = Self._readShort(Self.Memory[Address], zeropage=1)
        p = orig + Self.Y
        if orig & 0xFF00 != p & 0xFF00:  # if the high byte increases add 1 to cycle
            Self.Cycles += 1
        return p & 0xFFFF

    # updates flags N,Z based on value operated on
    def _updateNZ(Self, Value: int):
        Self.Z = 1 if (Value & 0xFF == 0) else 0
        Self.N = 1 if (Value & 0x80 != 0) else 0

    def _ADCFlags(Self, Original: int, Operand: int, Result: int):
        Self._updateNZ(Result)
        # unsigned overflow 255 + 1 = 0
        Self.C = 1 if Result > 0xFF else 0
        # signed overflow 127 + 1 = -128
        # idk chat did it
        Self.V = ((Original ^ Result) & (Operand ^ Result) & 0x80) != 0

    def _SBCFlags(Self, Original: int, Operand: int, Result: int):
        Self._updateNZ(Result)
        Self.C = 1 if Result >= 0 else 0
        Self.V = ((Original ^ Operand) & (Original ^ Result) & 0x80) != 0

    def _ASLFLags(Self, Value: int):
        Self._updateNZ(Value)
        Self.C = 1 if Value & 0x100 != 0 else 0

    def cycle(Self):
        if Self.Cycles == 0:
            Self.step()
        Self.Cycles -= 1

    def step(Self):
        match Self.Memory[Self.PC]:

            # ADC add with carry ---------------------------------
            case 0x69:  # ADC immediate
                Self.Cycles = 2
                Operand = Self.Memory[Self.PC + 1]
                Result = Self.A + Operand + Self.C
                Self._ADCFlags(Self.A, Operand, Result)
                Self.A = Result & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x65:  # ADC zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]  # address in zeropage
                Operand = Self.Memory[p]
                Result = Self.A + Operand + Self.C
                Self._ADCFlags(Self.A, Operand, Result)
                Self.A = Result & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x75:  # ADC zeropage, X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                Operand = Self.Memory[p]
                Result = Self.A + Operand + Self.C
                Self._ADCFlags(Self.A, Operand, Result)
                Self.A = Result & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x6D:  # ADC absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)  # address
                Operand = Self.Memory[p]
                Result = Self.A + Operand + Self.C
                Self._ADCFlags(Self.A, Operand, Result)
                Self.A = Result & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x7D:  # ADC absolute,X
                Self.Cycles = 4
                p = Self._addressingAbsoluteX(Self.PC + 1)
                Operand = Self.Memory[p]
                Result = Self.A + Operand + Self.C
                Self._ADCFlags(Self.A, Operand, Result)
                Self.A = Result & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x79:  # ADC absolute,Y
                Self.Cycles = 4
                p = Self._addressingAbsoluteY(Self.PC + 1)
                Operand = Self.Memory[p]
                Result = Self.A + Operand + Self.C
                Self._ADCFlags(Self.A, Operand, Result)
                Self.A = Result & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x61:  # ADC (indirect, X)
                Self.Cycles = 6
                p = Self._addressingIndirectX(Self.PC + 1)
                Operand = Self.Memory[p]
                Result = Self.A + Operand + Self.C
                Self._ADCFlags(Self.A, Operand, Result)
                Self.A = Result & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x71:  # ADC (indirect), Y
                Self.Cycles = 5
                p = Self._addressingIndirectY(Self.PC + 1)
                Operand = Self.Memory[p]
                Result = Self.A + Operand + Self.C
                Self._ADCFlags(Self.A, Operand, Result)
                Self.A = Result & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF

            # AND -------------------------------------------
            case 0x29:  # AND immediate
                Self.Cycles = 2
                Self.A = Self.A & Self.Memory[Self.PC + 1]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x25:  # AND zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.A = Self.A & Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x35:  # AND zeropage,X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.A = Self.A & Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x2D:  # AND absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.A = Self.A & Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x3D:  # AND absolute,X
                Self.Cycles = 4
                p = Self._addressingAbsoluteX(Self.PC + 1)
                Self.A = Self.A & Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x39:  # AND absolute,Y
                Self.Cycles = 4
                p = Self._addressingAbsoluteY(Self.PC + 1)
                Self.A = Self.A & Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x21:  # AND indirect,X
                Self.Cycles = 6
                p = Self._addressingIndirectX(Self.PC + 1)
                Self.A = Self.A & Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x31:  # AND indirect,y
                Self.Cycles = 5
                p = Self._addressingIndirectY(Self.PC + 1)
                Self.A = Self.A & Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            # ASL Shift Left One Bit -----------------------
            case 0x0A:  # ASL accumulator
                Self.Cycles = 2
                A = Self.A << 1
                Self._ASLFLags(A)
                Self.A = A & 0xFF
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x06:  # ASL zeropage
                Self.Cycles = 5
                p = Self.Memory[Self.PC + 1]
                S = Self.Memory[p] << 1
                Self._ASLFLags(S)
                Self.Memory[p] = S & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x16:  # ASL zeropage,X
                Self.Cycles = 6
                p = Self._addressingZeropageX(Self.PC + 1)
                S = Self.Memory[p] << 1
                Self._ASLFLags(S)
                Self.Memory[p] = S & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x0E:  # ASL absolute
                Self.Cycles = 6
                p = Self._readShort(Self.PC + 1)
                S = Self.Memory[p] << 1
                Self._ASLFLags(S)
                Self.Memory[p] = S & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x1E:  # ASL absolute,X
                Self.Cycles = 7
                p = Self._addressingAbsoluteX(Self.PC + 1)
                S = Self.Memory[p] << 1
                Self._ASLFLags(S)
                Self.Memory[p] = S & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF

            # Branching ---------------------------------------------------

            case 0x90:  # BCC Branch Carry Clear - relative
                Self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if Self.C == 0:
                    Self.Cycles += 1
                    ToJump = unsignedToSigned8bit(Self.Memory[Self.PC + 1])
                    if Self.PC & 0xFF00 != (Self.PC + ToJump + 2) & 0xFF00:
                        Self.Cycles += 1
                    Self.PC += ToJump
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0xB0:  # BCS Branch Carry Set - relative
                Self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if Self.C == 1:
                    Self.Cycles += 1
                    ToJump = unsignedToSigned8bit(Self.Memory[Self.PC + 1])
                    if Self.PC & 0xFF00 != (Self.PC + ToJump + 2) & 0xFF00:
                        Self.Cycles += 1
                    Self.PC += ToJump
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0xF0:  # BEQ Branch On Result Zero - relative
                Self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if Self.Z == 1:
                    Self.Cycles += 1
                    ToJump = unsignedToSigned8bit(Self.Memory[Self.PC + 1])
                    if Self.PC & 0xFF00 != (Self.PC + ToJump + 2) & 0xFF00:
                        Self.Cycles += 1
                    Self.PC += ToJump
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x30:  # BMI Branch On Result Minus - relative
                Self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if Self.N == 1:
                    Self.Cycles += 1
                    ToJump = unsignedToSigned8bit(Self.Memory[Self.PC + 1])
                    if Self.PC & 0xFF00 != (Self.PC + ToJump + 2) & 0xFF00:
                        Self.Cycles += 1
                    Self.PC += ToJump
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0xD0:  # BNE Branch On Result not Zero - relative
                Self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if Self.Z == 0:
                    Self.Cycles += 1
                    ToJump = unsignedToSigned8bit(Self.Memory[Self.PC + 1])
                    if Self.PC & 0xFF00 != (Self.PC + ToJump + 2) & 0xFF00:
                        Self.Cycles += 1
                    Self.PC += ToJump
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x10:  # BPL Branch On Result Plus - relative
                Self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if Self.N == 0:
                    Self.Cycles += 1
                    ToJump = unsignedToSigned8bit(Self.Memory[Self.PC + 1])
                    if Self.PC & 0xFF00 != (Self.PC + ToJump + 2) & 0xFF00:
                        Self.Cycles += 1
                    Self.PC += ToJump
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x50:  # BVC Branch On Overflow Clear - relative
                Self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if Self.V == 0:
                    Self.Cycles += 1
                    ToJump = unsignedToSigned8bit(Self.Memory[Self.PC + 1])
                    if Self.PC & 0xFF00 != (Self.PC + ToJump + 2) & 0xFF00:
                        Self.Cycles += 1
                    Self.PC += ToJump
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x70:  # BVS Branch On Overflow Set - relative
                Self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if Self.V == 1:
                    Self.Cycles += 1
                    ToJump = unsignedToSigned8bit(Self.Memory[Self.PC + 1])
                    if Self.PC & 0xFF00 != (Self.PC + ToJump + 2) & 0xFF00:
                        Self.Cycles += 1
                    Self.PC += ToJump
                Self.PC = (Self.PC + 2) & 0xFFFF
            # -----------------------------------------------------------------

            case 0x24:  # BIT zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                M = Self.Memory[p]
                Self.N = 1 if M & 0x80 else 0
                Self.V = 1 if M & 0x40 else 0
                Self.Z = 1 if M & Self.A == 0 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x2C:  # BIT absolute
                Self.Cycles = 4
                M = Self.Memory[Self._readShort(Self.PC + 1)]
                Self.N = 1 if M & 0x80 else 0
                Self.V = 1 if M & 0x40 else 0
                Self.Z = 1 if (M & Self.A) == 0 else 0
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x00:  # BRK
                Self.Cycles = 7
                SR = 0
                SR += Self.N * (1 << 7)
                SR += Self.V * (1 << 6)
                SR += 1 * (1 << 5)  # IDK chat said it's always 1 during break
                SR += 1 * (1 << 4)  # Self.B = 1
                SR += Self.D * (1 << 3)
                SR += Self.I * (1 << 2)
                SR += Self.Z * (1 << 1)
                SR += Self.C * (1 << 0)
                Self._push((Self.PC + 2) >> 8)
                Self._push((Self.PC + 2) & 0xFF)
                Self._push(SR)
                Self.I = 1
                Self.PC = Self._readShort(0xFFFE)

            # Flag Clear ------------------------------------------------------

            case 0x18:  # CLC Clear Carry Flag
                Self.Cycles = 2
                Self.C = 0
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0xD8:  # CLD Clear Deciaml Flag
                Self.Cycles = 2
                Self.D = 0
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x58:  # CLI Clear Interrupt Disable Flag
                Self.Cycles = 2
                Self.I = 0
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0xB8:  # CLV Clear Overflow Flag
                Self.Cycles = 2
                Self.V = 0
                Self.PC = (Self.PC + 1) & 0xFFFF

            # CMP Compare Memory with Accumulator ------------------------------
            case 0xC9:  # CMP immediate
                Self.Cycles = 2
                B = Self.Memory[Self.PC + 1]
                Self.C = 1 if Self.A >= B else 0
                Self.Z = 1 if Self.A == B else 0
                Self.N = 1 if (Self.A - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xC5:  # CMP zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                B = Self.Memory[p]
                Self.C = 1 if Self.A >= B else 0
                Self.Z = 1 if Self.A == B else 0
                Self.N = 1 if (Self.A - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xD5:  # CMP zeropage,x
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                B = Self.Memory[p]
                Self.C = 1 if Self.A >= B else 0
                Self.Z = 1 if Self.A == B else 0
                Self.N = 1 if (Self.A - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xCD:  # CMP absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                B = Self.Memory[p]
                Self.C = 1 if Self.A >= B else 0
                Self.Z = 1 if Self.A == B else 0
                Self.N = 1 if (Self.A - B) & 0x80 else 0
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xDD:  # CMP absolute,X
                Self.Cycles = 4
                p = Self._addressingAbsoluteX(Self.PC + 1)
                B = Self.Memory[p]
                Self.C = 1 if Self.A >= B else 0
                Self.Z = 1 if Self.A == B else 0
                Self.N = 1 if (Self.A - B) & 0x80 else 0
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xD9:  # CMP absolute,Y
                Self.Cycles = 4
                p = Self._addressingAbsoluteY(Self.PC + 1)
                B = Self.Memory[p]
                Self.C = 1 if Self.A >= B else 0
                Self.Z = 1 if Self.A == B else 0
                Self.N = 1 if (Self.A - B) & 0x80 else 0
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xC1:  # CMP indirect,X
                Self.Cycles = 6
                p = Self._addressingIndirectX(Self.PC + 1)
                B = Self.Memory[p]
                Self.C = 1 if Self.A >= B else 0
                Self.Z = 1 if Self.A == B else 0
                Self.N = 1 if (Self.A - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xD1:  # CMP indirect,Y
                Self.Cycles = 5
                p = Self._addressingIndirectY(Self.PC + 1)
                B = Self.Memory[p]
                Self.C = 1 if Self.A >= B else 0
                Self.Z = 1 if Self.A == B else 0
                Self.N = 1 if (Self.A - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF

            # CPX Compare Memory and X -------------------------

            case 0xE0:  # CPX immediate
                Self.Cycles = 2
                B = Self.Memory[Self.PC + 1]
                Self.C = 1 if Self.X >= B else 0
                Self.Z = 1 if Self.X == B else 0
                Self.N = 1 if (Self.X - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xE4:  # CPX zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                B = Self.Memory[p]
                Self.C = 1 if Self.X >= B else 0
                Self.Z = 1 if Self.X == B else 0
                Self.N = 1 if (Self.X - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xEC:  # CPX absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                B = Self.Memory[p]
                Self.C = 1 if Self.X >= B else 0
                Self.Z = 1 if Self.X == B else 0
                Self.N = 1 if (Self.X - B) & 0x80 else 0
                Self.PC = (Self.PC + 3) & 0xFFFF

            # CPY Compare Memory and X -------------------------
            case 0xC0:  # CPY immediate
                Self.Cycles = 2
                B = Self.Memory[Self.PC + 1]
                Self.C = 1 if Self.Y >= B else 0
                Self.Z = 1 if Self.Y == B else 0
                Self.N = 1 if (Self.Y - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xC4:  # CPY zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                B = Self.Memory[p]
                Self.C = 1 if Self.Y >= B else 0
                Self.Z = 1 if Self.Y == B else 0
                Self.N = 1 if (Self.Y - B) & 0x80 else 0
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xCC:  # CPY absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                B = Self.Memory[p]
                Self.C = 1 if Self.Y >= B else 0
                Self.Z = 1 if Self.Y == B else 0
                Self.N = 1 if (Self.Y - B) & 0x80 else 0
                Self.PC = (Self.PC + 3) & 0xFFFF

            # DEC Decrement Memory by One -----------------

            case 0xC6:  # DEC zeropage
                Self.Cycles = 5
                p = Self.Memory[Self.PC + 1]
                Self.Memory[p] = (Self.Memory[p] - 1) & 0xFF
                Self._updateNZ(Self.Memory[p])
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xD6:  # DEC zeropage,X
                Self.Cycles = 6
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.Memory[p] = (Self.Memory[p] - 1) & 0xFF
                Self._updateNZ(Self.Memory[p])
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xCE:  # DEC absolute
                Self.Cycles = 6
                p = Self._readShort(Self.PC + 1)
                Self.Memory[p] = (Self.Memory[p] - 1) & 0xFF
                Self._updateNZ(Self.Memory[p])
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xDE:  # DEC absolute,X
                Self.Cycles = 7
                p = (Self._readShort(Self.PC + 1) + Self.X) & 0xFFFF
                Self.Memory[p] = (Self.Memory[p] - 1) & 0xFF
                Self._updateNZ(Self.Memory[p])
                Self.PC = (Self.PC + 3) & 0xFFFF

            # --------------------------------------------------

            case 0xCA:  # DEX Decreament X by one
                Self.Cycles = 2
                Self.X = (Self.X - 1) & 0xFF
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x88:  # DEY Decreament Y by one
                Self.Cycles = 2
                Self.Y = (Self.Y - 1) & 0xFF
                Self._updateNZ(Self.Y)
                Self.PC = (Self.PC + 1) & 0xFFFF

            # Copied 'AND' Section
            # EOR Exclusive-OR Memory with Accumulator -----------------
            case 0x49:  # EOR immediate
                Self.Cycles = 2
                Self.A = Self.A ^ Self.Memory[Self.PC + 1]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x45:  # EOR zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.A = Self.A ^ Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x55:  # EOR zeropage,X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.A = Self.A ^ Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x4D:  # EOR absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.A = Self.A ^ Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x5D:  # EOR absolute,X
                Self.Cycles = 4
                p = Self._addressingAbsoluteX(Self.PC + 1)
                Self.A = Self.A ^ Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x59:  # EOR absolute,Y
                Self.Cycles = 4
                p = Self._addressingAbsoluteY(Self.PC + 1)
                Self.A = Self.A ^ Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x41:  # EOR indirect,X
                Self.Cycles = 6
                p = Self._addressingIndirectX(Self.PC + 1)
                Self.A = Self.A ^ Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x51:  # EOR indirect,y
                Self.Cycles = 5
                p = Self._addressingIndirectY(Self.PC + 1)
                Self.A = Self.A ^ Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            # Copied DEC section
            # INC Increment Memory by One -----------------

            case 0xE6:  # INC zeropage
                Self.Cycles = 5
                p = Self.Memory[Self.PC + 1]
                Self.Memory[p] = (Self.Memory[p] + 1) & 0xFF
                Self._updateNZ(Self.Memory[p])
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xF6:  # INC zeropage,X
                Self.Cycles = 6
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.Memory[p] = (Self.Memory[p] + 1) & 0xFF
                Self._updateNZ(Self.Memory[p])
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xEE:  # INC absolute
                Self.Cycles = 6
                p = Self._readShort(Self.PC + 1)
                Self.Memory[p] = (Self.Memory[p] + 1) & 0xFF
                Self._updateNZ(Self.Memory[p])
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xFE:  # INC absolute,X
                Self.Cycles = 7
                p = (Self._readShort(Self.PC + 1) + Self.X) & 0xFFFF
                Self.Memory[p] = (Self.Memory[p] + 1) & 0xFF
                Self._updateNZ(Self.Memory[p])
                Self.PC = (Self.PC + 3) & 0xFFFF

            # --------------------------------------------------

            case 0xE8:  # INX Increament X by one
                Self.Cycles = 2
                Self.X = (Self.X + 1) & 0xFF
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0xC8:  # INY Increament Y by one
                Self.Cycles = 2
                Self.Y = (Self.Y + 1) & 0xFF
                Self._updateNZ(Self.Y)
                Self.PC = (Self.PC + 1) & 0xFFFF

            # JMP -------------------------------------------
            case 0x4C:  # JMP absolute
                Self.Cycles = 3
                Self.PC = Self._readShort(Self.PC + 1)
            case 0x6C:  # jmp indirect
                Self.Cycles = 5
                # p address of value where to jmp
                # some hardware bug said by chat
                pL = Self.Memory[Self.PC + 1]
                pH = Self.Memory[Self.PC + 2]
                PCL = Self.Memory[pL + pH * (1 << 8)]
                PCH = Self.Memory[((pL + 1) & 0xFF) + pH * (1 << 8)]
                Self.PC = PCL + PCH * (1 << 8)
            case (
                0x20
            ):  # JSR Jump to New Location Saving Return Address (jmp sub-routine)
                Self.Cycles = 6
                PC = Self.PC + 2
                Self._push(PC >> 8)
                Self._push(PC & 0xFF)
                Self.PC = Self._readShort(Self.PC + 1)

            # LDA Load A with Memory
            case 0xA9:  # LDA immediate
                Self.Cycles = 2
                Self.A = Self.Memory[Self.PC + 1]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xA5:  # LDA zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.A = Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xB5:  # LDA zeropage,X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.A = Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xAD:  # LDA absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.A = Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xBD:  # LDA absolute,X
                Self.Cycles = 4
                p = Self._addressingAbsoluteX(Self.PC + 1)
                Self.A = Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xB9:  # LDA absolute,Y
                Self.Cycles = 4
                p = Self._addressingAbsoluteY(Self.PC + 1)
                Self.A = Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xA1:  # LDA indirect,X
                Self.Cycles = 6
                p = Self._addressingIndirectX(Self.PC + 1)
                Self.A = Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xB1:  # LDA indirect,Y
                Self.Cycles = 5
                p = Self._addressingIndirectY(Self.PC + 1)
                Self.A = Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            # Copied LDA
            # LDX Load X with Memory
            case 0xA2:  # LDX immediate
                Self.Cycles = 2
                Self.X = Self.Memory[Self.PC + 1]
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xA6:  # LDX zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.X = Self.Memory[p]
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xB6:  # LDX zeropage,Y
                Self.Cycles = 4
                p = Self._addressingZeropageY(Self.PC + 1)
                Self.X = Self.Memory[p]
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xAE:  # LDX absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.X = Self.Memory[p]
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xBE:  # LDX absolute,Y
                Self.Cycles = 4
                p = Self._addressingAbsoluteY(Self.PC + 1)
                Self.X = Self.Memory[p]
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 3) & 0xFFFF

            # Copied LDX
            # LDY Load Y with Memory
            case 0xA0:  # LDY immediate
                Self.Cycles = 2
                Self.Y = Self.Memory[Self.PC + 1]
                Self._updateNZ(Self.Y)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xA4:  # LDY zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.Y = Self.Memory[p]
                Self._updateNZ(Self.Y)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xB4:  # LDY zeropage,X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.Y = Self.Memory[p]
                Self._updateNZ(Self.Y)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xAC:  # LDY absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.Y = Self.Memory[p]
                Self._updateNZ(Self.Y)
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xBC:  # LDY absolute,X
                Self.Cycles = 4
                p = Self._addressingAbsoluteX(Self.PC + 1)
                Self.Y = Self.Memory[p]
                Self._updateNZ(Self.Y)
                Self.PC = (Self.PC + 3) & 0xFFFF

            # LSR Shift Right
            case 0x4A:  # LSR accumulator
                Self.Cycles = 2
                Self.C = Self.A & 0x01
                Self.A = (Self.A >> 1) & 0xFF
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x46:  # LSR zeropage
                Self.Cycles = 5
                p = Self.Memory[Self.PC + 1]
                M = Self.Memory[p]
                Self.C = M & 0x01
                M = (M >> 1) & 0xFF
                Self._updateNZ(M)
                Self.Memory[p] = M
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x56:  # LSR zeropage,X
                Self.Cycles = 6
                p = Self._addressingZeropageX(Self.PC + 1)
                M = Self.Memory[p]
                Self.C = M & 0x01
                M = (M >> 1) & 0xFF
                Self._updateNZ(M)
                Self.Memory[p] = M
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x4E:  # LSR absolute
                Self.Cycles = 6
                p = Self._readShort(Self.PC + 1)
                M = Self.Memory[p]
                Self.C = M & 0x01
                M = (M >> 1) & 0xFF
                Self._updateNZ(M)
                Self.Memory[p] = M
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x5E:  # LSR absolute,X
                Self.Cycles = 7
                p = (Self._readShort(Self.PC + 1) + Self.X) & 0xFFFF
                M = Self.Memory[p]
                Self.C = M & 0x01
                M = (M >> 1) & 0xFF
                Self._updateNZ(M)
                Self.Memory[p] = M
                Self.PC = (Self.PC + 3) & 0xFFFF

            # --------------------------------------------------------
            case 0xEA:  # NOP
                Self.Cycles = 2
                Self.PC = (Self.PC + 1) & 0xFFFF

            # Copied 'EOR' Section
            # ORA OR Memory with Accumulator -----------------
            case 0x09:  # ORA immediate
                Self.Cycles = 2
                Self.A = Self.A | Self.Memory[Self.PC + 1]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x05:  # ORA zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.A = Self.A | Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x15:  # ORA zeropage,X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.A = Self.A | Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x0D:  # ORA absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.A = Self.A | Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x1D:  # ORA absolute,X
                Self.Cycles = 4
                p = Self._addressingAbsoluteX(Self.PC + 1)
                Self.A = Self.A | Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x19:  # ORA absolute,Y
                Self.Cycles = 4
                p = Self._addressingAbsoluteY(Self.PC + 1)
                Self.A = Self.A | Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 3) & 0xFFFF

            case 0x01:  # ORA indirect,X
                Self.Cycles = 6
                p = Self._addressingIndirectX(Self.PC + 1)
                Self.A = Self.A | Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x11:  # ORA indirect,y
                Self.Cycles = 5
                p = Self._addressingIndirectY(Self.PC + 1)
                Self.A = Self.A | Self.Memory[p]
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 2) & 0xFFFF

            # Stack operations -----------------------------------
            case 0x48:  # PHA Push A on Stack
                Self.Cycles = 3
                Self._push(Self.A)
                Self.PC = (Self.PC + 1) & 0xFFFF

            case 0x08:  # PHP Push Processor Status on Stack
                Self.Cycles = 3
                SR = 0
                SR += Self.N * (1 << 7)
                SR += Self.V * (1 << 6)
                SR += 1 * (1 << 5)  # IDK chat said it's always 1 during break
                SR += 1 * (1 << 4)  # Self.B = 1
                SR += Self.D * (1 << 3)
                SR += Self.I * (1 << 2)
                SR += Self.Z * (1 << 1)
                SR += Self.C * (1 << 0)
                Self._push(SR)
                Self.PC = (Self.PC + 1) & 0xFFFF

            case 0x68:  # PLA Pull A from Stack
                Self.Cycles = 4
                Self.A = Self._pull()
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 1) & 0xFFFF

            case 0x28:  # PLP Pull Processor Status from Stack
                Self.Cycles = 4
                SR = Self._pull()
                Self.C = (SR >> 0) & 0x1
                Self.Z = (SR >> 1) & 0x1
                Self.I = (SR >> 2) & 0x1
                Self.D = (SR >> 3) & 0x1
                Self.V = (SR >> 6) & 0x1
                Self.N = (SR >> 7) & 0x1
                Self.PC = (Self.PC + 1) & 0xFFFF

            # ROL Rotate One Bit Left ---------------------------------
            case 0x2A:  # ROL accumulator
                Self.Cycles = 2
                M = (Self.A << 1) + Self.C
                Self.C = M >> 8
                Self.A = M & 0xFF
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x26:  # ROL zeropage
                Self.Cycles = 5
                p = Self.Memory[Self.PC + 1]
                M = Self.Memory[p]
                M = (M << 1) + Self.C
                Self.C = M >> 8
                Self.Memory[p] = M & 0xFF
                Self._updateNZ(M)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x36:  # ROL zeropage,X
                Self.Cycles = 6
                p = Self._addressingZeropageX(Self.PC + 1)
                M = Self.Memory[p]
                M = (M << 1) + Self.C
                Self.C = M >> 8
                Self.Memory[p] = M & 0xFF
                Self._updateNZ(M)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x2E:  # ROL absolute
                Self.Cycles = 6
                p = Self._readShort(Self.PC + 1)
                M = Self.Memory[p]
                M = (M << 1) + Self.C
                Self.C = M >> 8
                Self.Memory[p] = M & 0xFF
                Self._updateNZ(M)
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x3E:  # ROL absolute,X
                Self.Cycles = 7
                p = (Self._readShort(Self.PC + 1) + Self.X) & 0xFFFF
                M = Self.Memory[p]
                M = (M << 1) + Self.C
                Self.C = M >> 8
                Self.Memory[p] = M & 0xFF
                Self._updateNZ(M)
                Self.PC = (Self.PC + 3) & 0xFFFF

            # Copied ROL
            # ROR Rotate One Bit Right ---------------------------------
            case 0x6A:  # ROR accumulator
                Self.Cycles = 2
                M = (Self.A >> 1) + (Self.C << 7)
                Self.C = Self.A & 0x1
                Self.A = M & 0xFF
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x66:  # ROR zeropage
                Self.Cycles = 5
                p = Self.Memory[Self.PC + 1]
                M = Self.Memory[p]
                NM = (M >> 1) + (Self.C << 7)
                Self.C = M & 0x1
                Self.Memory[p] = NM & 0xFF
                Self._updateNZ(NM)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x76:  # ROR zeropage,X
                Self.Cycles = 6
                p = Self._addressingZeropageX(Self.PC + 1)
                M = Self.Memory[p]
                NM = (M >> 1) + (Self.C << 7)
                Self.C = M & 0x1
                Self.Memory[p] = NM & 0xFF
                Self._updateNZ(NM)
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x6E:  # ROR absolute
                Self.Cycles = 6
                p = Self._readShort(Self.PC + 1)
                M = Self.Memory[p]
                NM = (M >> 1) + (Self.C << 7)
                Self.C = M & 0x1
                Self.Memory[p] = NM & 0xFF
                Self._updateNZ(NM)
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x7E:  # ROR absolute,X
                Self.Cycles = 7
                p = (Self._readShort(Self.PC + 1) + Self.X) & 0xFFFF
                M = Self.Memory[p]
                NM = (M >> 1) + (Self.C << 7)
                Self.C = M & 0x1
                Self.Memory[p] = NM & 0xFF
                Self._updateNZ(NM)
                Self.PC = (Self.PC + 3) & 0xFFFF

            # -----------------------------------------------------------

            case 0x40:  # RTI Return from Interrupt
                Self.Cycles = 6
                SR = Self._pull()
                Self.C = (SR >> 0) & 0x1
                Self.Z = (SR >> 1) & 0x1
                Self.I = (SR >> 2) & 0x1
                Self.D = (SR >> 3) & 0x1
                Self.V = (SR >> 6) & 0x1
                Self.N = (SR >> 7) & 0x1
                PCL = Self._pull()
                PCH = Self._pull()
                Self.PC = PCL + (PCH << 8)

            case 0x60:  # RTS Return from Subroutine
                Self.Cycles = 6
                PCL = Self._pull()
                PCH = Self._pull()
                PC = PCL + (PCH << 8)
                Self.PC = (PC + 1) & 0xFFFF

            # SBC Subtract Memory from Accumulator with Borrow

            case 0xE9:  # SBC immediate
                Self.Cycles = 2
                M = Self.Memory[Self.PC + 1]
                R = Self.A - M - (1 - Self.C)
                Self._SBCFlags(Self.A, M, R)
                Self.A = R & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xE5:  # SBC zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                M = Self.Memory[p]
                R = Self.A - M - (1 - Self.C)
                Self._SBCFlags(Self.A, M, R)
                Self.A = R & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xF5:  # SBC zeropage,X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                M = Self.Memory[p]
                R = Self.A - M - (1 - Self.C)
                Self._SBCFlags(Self.A, M, R)
                Self.A = R & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xED:  # SBC absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                M = Self.Memory[p]
                R = Self.A - M - (1 - Self.C)
                Self._SBCFlags(Self.A, M, R)
                Self.A = R & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xFD:  # SBC absolute,X
                Self.Cycles = 4
                p = Self._addressingAbsoluteX(Self.PC + 1)
                M = Self.Memory[p]
                R = Self.A - M - (1 - Self.C)
                Self._SBCFlags(Self.A, M, R)
                Self.A = R & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xF9:  # SBC absolute,Y
                Self.Cycles = 4
                p = Self._addressingAbsoluteY(Self.PC + 1)
                M = Self.Memory[p]
                R = Self.A - M - (1 - Self.C)
                Self._SBCFlags(Self.A, M, R)
                Self.A = R & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0xE1:  # SBC indirect,X
                Self.Cycles = 6
                p = Self._addressingIndirectX(Self.PC + 1)
                M = Self.Memory[p]
                R = Self.A - M - (1 - Self.C)
                Self._SBCFlags(Self.A, M, R)
                Self.A = R & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0xF1:  # SBC indirect,Y
                Self.Cycles = 5
                p = Self._addressingIndirectY(Self.PC + 1)
                M = Self.Memory[p]
                R = Self.A - M - (1 - Self.C)
                Self._SBCFlags(Self.A, M, R)
                Self.A = R & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF

            # Set Flags ---------------------------------------

            case 0x38:  # Set Carry Flag
                Self.Cycles = 2
                Self.C = 1
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0xF8:  # Set Decimal Flag
                Self.Cycles = 2
                Self.D = 1
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x78:  # Set Interrupt Disable Flag
                Self.Cycles = 2
                Self.I = 1
                Self.PC = (Self.PC + 1) & 0xFFFF

            # STA Store Accumulator in Memory

            case 0x85:  # STA zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.Memory[p] = Self.A & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x95:  # STA zeropage,X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.Memory[p] = Self.A & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x8D:  # STA absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.Memory[p] = Self.A & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x9D:  # STA absolute,X
                Self.Cycles = 5
                p = (Self._readShort(Self.PC + 1) + Self.X) & 0xFFFF
                Self.Memory[p] = Self.A & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x99:  # STA absolute,Y
                Self.Cycles = 5
                p = (Self._readShort(Self.PC + 1) + Self.Y) & 0xFFFF
                Self.Memory[p] = Self.A & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF
            case 0x81:  # STA indirect,X
                Self.Cycles = 6
                p = Self._addressingIndirectX(Self.PC + 1)
                Self.Memory[p] = Self.A & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF
            case 0x91:  # STA indirect,Y
                Self.Cycles = 6
                pp = Self.Memory[Self.PC + 1]
                p = (Self._readShort(pp) + Self.Y) & 0xFFFF
                Self.Memory[p] = Self.A & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF

            # STX Store X in Memory--------------------------------

            case 0x86:  # STX zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.Memory[p] = Self.X & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x96:  # STX zeropage,Y
                Self.Cycles = 4
                p = Self._addressingZeropageY(Self.PC + 1)
                Self.Memory[p] = Self.X & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x8E:  # STX absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.Memory[p] = Self.X & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF

            # Copied STX

            # STX Store X in Memory--------------------------------

            case 0x84:  # STY zeropage
                Self.Cycles = 3
                p = Self.Memory[Self.PC + 1]
                Self.Memory[p] = Self.Y & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x94:  # STY zeropage,X
                Self.Cycles = 4
                p = Self._addressingZeropageX(Self.PC + 1)
                Self.Memory[p] = Self.Y & 0xFF
                Self.PC = (Self.PC + 2) & 0xFFFF

            case 0x8C:  # STY absolute
                Self.Cycles = 4
                p = Self._readShort(Self.PC + 1)
                Self.Memory[p] = Self.Y & 0xFF
                Self.PC = (Self.PC + 3) & 0xFFFF

            # Transfer operations --------------------------------------

            case 0xAA:  # TAX Transfer A to X
                Self.Cycles = 2
                Self.X = Self.A
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0xA8:  # TAY Transfer A to Y
                Self.Cycles = 2
                Self.Y = Self.A
                Self._updateNZ(Self.Y)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0xBA:  # TSX Transfer Stack Pointer to X
                Self.Cycles = 2
                Self.X = Self.SP
                Self._updateNZ(Self.X)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x8A:  # TXA Transfer X to A
                Self.Cycles = 2
                Self.A = Self.X
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x9A:  # TXS Transfer X to Stack Pointer
                Self.Cycles = 2
                Self.SP = Self.X
                Self.PC = (Self.PC + 1) & 0xFFFF
            case 0x98:  # TYA Transfer Y to A
                Self.Cycles = 2
                Self.A = Self.Y
                Self._updateNZ(Self.A)
                Self.PC = (Self.PC + 1) & 0xFFFF
            case _:
                Self.Cycles = 2
                Self.PC = (Self.PC + 1) & 0xFFFF
