def unsignedToSigned8bit(Value: int) -> int:
    return (Value - 256) if Value & 0x80 else Value


def signedToUnsigned8bit(Value: int) -> int:
    return Value & 0xFF


class cpu6502:
    def __init__(self, memory: list):
        """
        Creates a 6502 CPU

        Args:
            memory (list): A reference to a list of integers.
        """
        self.Memory = memory
        # cycles measure how many cycles to wait
        self.Cycles = 0
        # Accumulator
        self.A = 0
        # X, Y registers
        self.X = 0
        self.Y = 0
        # Stack Pointer
        self.SP = 0xFF
        # $FFFA, $FFFB ... NMI (Non-Maskable Interrupt) vector, 16-bit (LB, HB)
        self.NMI = 0xFFFA
        # $FFFC, $FFFD ... RES (Reset) vector, 16-bit (LB, HB)
        self.RES = 0xFFFC
        # $FFFE, $FFFF ... IRQ (Interrupt Request) vector, 16-bit (LB, HB)
        self.IRQ = 0xFFFE
        # Program counter(defaultly set reser vector)
        self.PC = self._readShort(self.RES)
        # Flags
        # N	Negative
        self.N = 0
        # V	Overflow
        self.V = 0
        # B	Break
        self.B = 0
        # D	Decimal (use BCD for arithmetics)
        self.D = 0
        # I	Interrupt (IRQ disable)
        self.I = 0
        # Z	Zero
        self.Z = 0
        # C	Carry
        self.C = 0

    # reads 16bits
    def _readShort(self, Address: int, zeropage: int = 0) -> int:
        """
        Reads a 16-bit value from memory

        Args:
            Address (int): The base address to read from.
            zeropage (int): If 1, wraps around zero-page addressing (0x00 to 0xFF) (A bug in 6502).

        Returns:
            int: The 16-bit value.
        """
        if zeropage == 0:
            return self.Memory[Address & 0xFFFF] + (
                self.Memory[(Address + 1) & 0xFFFF] << 8
            )
        else:  # if we have 0xFF in zeropage than the next address is 0x00
            return self.Memory[Address & 0xFF] + (
                self.Memory[(Address + 1) & 0xFF] << 8
            )

    # writes 16bits
    def _writeShort(self, Address: int, Value: int, zeropage: int = 0):
        """
        Write a 16-bit value to memory.

        Args:
            Address (int): The base address to write to.
            Value (int): The 16-bit value.
            zeropage (int): If 1, wraps around zero-page addressing (A bug in 6502).
        """
        if zeropage == 0:
            self.Memory[Address & 0xFFFF] = Value & 0xFF
            self.Memory[(Address + 1) & 0xFFFF] = (Value >> 8) & 0xFF
        else:  # if we have 0xFF in zeropage than the next address is 0x00
            self.Memory[Address & 0xFF] = Value & 0xFF
            self.Memory[(Address + 1) & 0xFF] = (Value >> 8) & 0xFF

    def _push(self, Value: int):
        """
        Push a 8-bit integer onto the stack

        Args:
            Value (int): Integer to push.
        """
        self.Memory[self.SP + 0x100] = Value
        self.SP = (self.SP - 1) & 0xFF

    def _pull(self) -> int:
        """
        Pull a 8-bit integer from the stack

        Returns:
            int: Integer from the stack.
        """
        self.SP = (self.SP + 1) & 0xFF
        return self.Memory[self.SP + 0x100]

    # more coplicated addressing modes
    def _addressingZeropageX(self, Address: int):
        """
        Zero-page,X addressing mode.

        Args:
            Address (int): Address of the operand.

        Returns:
            int: Final effective address.
        """
        p = self.Memory[Address] + self.X  # address in zeropage + X
        return p & 0xFF

    def _addressingZeropageY(self, Address: int):
        """
        Zero-page,Y addressing mode.

        Args:
            Address (int): Address of the operand.

        Returns:
            int: Final effective address.
        """
        p = self.Memory[Address] + self.Y  # address in zeropage + Y
        return p & 0xFF

    def _addressingAbsoluteX(self, Address: int):
        """
        Absolute,X addressing mode. Adds cycle on page crossing.

        Args:
            Address (int): Location holding the base address.

        Returns:
            int: Final effective address.
        """
        orig = self._readShort(Address)
        p = orig + self.X  # address + X
        if orig & 0xFF00 != p & 0xFF00:  # if the high byte increases add 1 to cycle
            self.Cycles += 1
        return p & 0xFFFF

    def _addressingAbsoluteY(self, Address: int):
        """
        Absolute,Y addressing mode. Adds cycle on page crossing.

        Args:
            Address (int): Location holding the base address.

        Returns:
            int: Final effective address.
        """
        orig = self._readShort(Address)
        p = orig + self.Y  # address + Y
        if orig & 0xFF00 != p & 0xFF00:  # if the high byte increases add 1 to cycle
            self.Cycles += 1
        return p & 0xFFFF

    def _addressingIndirectX(self, Address: int):
        """
        Indexed Indirect (Indirect,X) addressing.

        Args:
            Address (int): Address of base pointer in zero page.

        Returns:
            int: Effective address after dereferencing.
        """
        pp = self.Memory[Address] + self.X
        pp = pp & 0xFF
        return self._readShort(pp, zeropage=1)

    def _addressingIndirectY(self, Address: int):
        """
        Indirect Indexed (Indirect),Y addressing.

        Args:
            Address (int): Address of base pointer in zero page.

        Returns:
            int: Effective address after dereferencing and adding Y.
        """
        orig = self._readShort(self.Memory[Address], zeropage=1)
        p = orig + self.Y
        if orig & 0xFF00 != p & 0xFF00:  # if the high byte increases add 1 to cycle
            self.Cycles += 1
        return p & 0xFFFF

    # updates flags N,Z based on value operated on
    def _updateNZ(self, Value: int):
        """
        Update N (negative) and Z (zero) flags based on a result.

        Args:
            Value (int): The result to evaluate.
        """
        self.Z = 1 if (Value & 0xFF == 0) else 0
        self.N = 1 if (Value & 0x80 != 0) else 0

    def _ADCFlags(self, Original: int, Operand: int, Result: int):
        """
        Set flags for the ADC instruction result.

        Args:
            Original (int): Accumulator value before addition.
            Operand (int): Operand added.
            Result (int): Result after addition.
        """
        self._updateNZ(Result)
        # unsigned overflow 255 + 1 = 0
        self.C = 1 if Result > 0xFF else 0
        # signed overflow 127 + 1 = -128
        # idk chat did it
        self.V = ((Original ^ Result) & (Operand ^ Result) & 0x80) != 0

    def _SBCFlags(self, Original: int, Operand: int, Result: int):
        """
        Set flags for the SBC instruction result.

        Args:
            Original (int): Accumulator value before subtraction.
            Operand (int): Operand subtracted.
            Result (int): Result after subtraction.
        """
        self._updateNZ(Result)
        self.C = 1 if Result >= 0 else 0
        self.V = ((Original ^ Operand) & (Original ^ Result) & 0x80) != 0

    def _ASLFLags(self, Value: int):
        """
        Set flags for the ASL (Arithmetic Shift Left) result.

        Args:
            Value (int): Result of the ASL operation.
        """
        self._updateNZ(Value)
        self.C = 1 if Value & 0x100 != 0 else 0

    def cycle(self):
        """
        Advance the CPU by one cycle. Executes instruction if no cycles are left.
        """

        if self.Cycles == 0:
            self.step()
        self.Cycles -= 1

    def step(self):
        """
        Fetch and execute a single instruction.
        """
        match self.Memory[self.PC]:

            # ADC add with carry ---------------------------------
            case 0x69:  # ADC immediate
                self.Cycles = 2
                Operand = self.Memory[self.PC + 1]
                Result = self.A + Operand + self.C
                self._ADCFlags(self.A, Operand, Result)
                self.A = Result & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x65:  # ADC zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]  # address in zeropage
                Operand = self.Memory[p]
                Result = self.A + Operand + self.C
                self._ADCFlags(self.A, Operand, Result)
                self.A = Result & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x75:  # ADC zeropage, X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                Operand = self.Memory[p]
                Result = self.A + Operand + self.C
                self._ADCFlags(self.A, Operand, Result)
                self.A = Result & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x6D:  # ADC absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)  # address
                Operand = self.Memory[p]
                Result = self.A + Operand + self.C
                self._ADCFlags(self.A, Operand, Result)
                self.A = Result & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x7D:  # ADC absolute,X
                self.Cycles = 4
                p = self._addressingAbsoluteX(self.PC + 1)
                Operand = self.Memory[p]
                Result = self.A + Operand + self.C
                self._ADCFlags(self.A, Operand, Result)
                self.A = Result & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x79:  # ADC absolute,Y
                self.Cycles = 4
                p = self._addressingAbsoluteY(self.PC + 1)
                Operand = self.Memory[p]
                Result = self.A + Operand + self.C
                self._ADCFlags(self.A, Operand, Result)
                self.A = Result & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x61:  # ADC (indirect, X)
                self.Cycles = 6
                p = self._addressingIndirectX(self.PC + 1)
                Operand = self.Memory[p]
                Result = self.A + Operand + self.C
                self._ADCFlags(self.A, Operand, Result)
                self.A = Result & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x71:  # ADC (indirect), Y
                self.Cycles = 5
                p = self._addressingIndirectY(self.PC + 1)
                Operand = self.Memory[p]
                Result = self.A + Operand + self.C
                self._ADCFlags(self.A, Operand, Result)
                self.A = Result & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF

            # AND -------------------------------------------
            case 0x29:  # AND immediate
                self.Cycles = 2
                self.A = self.A & self.Memory[self.PC + 1]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x25:  # AND zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.A = self.A & self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x35:  # AND zeropage,X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                self.A = self.A & self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x2D:  # AND absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.A = self.A & self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x3D:  # AND absolute,X
                self.Cycles = 4
                p = self._addressingAbsoluteX(self.PC + 1)
                self.A = self.A & self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x39:  # AND absolute,Y
                self.Cycles = 4
                p = self._addressingAbsoluteY(self.PC + 1)
                self.A = self.A & self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x21:  # AND indirect,X
                self.Cycles = 6
                p = self._addressingIndirectX(self.PC + 1)
                self.A = self.A & self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x31:  # AND indirect,y
                self.Cycles = 5
                p = self._addressingIndirectY(self.PC + 1)
                self.A = self.A & self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            # ASL Shift Left One Bit -----------------------
            case 0x0A:  # ASL accumulator
                self.Cycles = 2
                A = self.A << 1
                self._ASLFLags(A)
                self.A = A & 0xFF
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x06:  # ASL zeropage
                self.Cycles = 5
                p = self.Memory[self.PC + 1]
                S = self.Memory[p] << 1
                self._ASLFLags(S)
                self.Memory[p] = S & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x16:  # ASL zeropage,X
                self.Cycles = 6
                p = self._addressingZeropageX(self.PC + 1)
                S = self.Memory[p] << 1
                self._ASLFLags(S)
                self.Memory[p] = S & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x0E:  # ASL absolute
                self.Cycles = 6
                p = self._readShort(self.PC + 1)
                S = self.Memory[p] << 1
                self._ASLFLags(S)
                self.Memory[p] = S & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x1E:  # ASL absolute,X
                self.Cycles = 7
                p = self._addressingAbsoluteX(self.PC + 1)
                S = self.Memory[p] << 1
                self._ASLFLags(S)
                self.Memory[p] = S & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF

            # Branching ---------------------------------------------------

            case 0x90:  # BCC Branch Carry Clear - relative
                self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if self.C == 0:
                    self.Cycles += 1
                    ToJump = unsignedToSigned8bit(self.Memory[self.PC + 1])
                    if self.PC & 0xFF00 != (self.PC + ToJump + 2) & 0xFF00:
                        self.Cycles += 1
                    self.PC += ToJump
                self.PC = (self.PC + 2) & 0xFFFF

            case 0xB0:  # BCS Branch Carry Set - relative
                self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if self.C == 1:
                    self.Cycles += 1
                    ToJump = unsignedToSigned8bit(self.Memory[self.PC + 1])
                    if self.PC & 0xFF00 != (self.PC + ToJump + 2) & 0xFF00:
                        self.Cycles += 1
                    self.PC += ToJump
                self.PC = (self.PC + 2) & 0xFFFF

            case 0xF0:  # BEQ Branch On Result Zero - relative
                self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if self.Z == 1:
                    self.Cycles += 1
                    ToJump = unsignedToSigned8bit(self.Memory[self.PC + 1])
                    if self.PC & 0xFF00 != (self.PC + ToJump + 2) & 0xFF00:
                        self.Cycles += 1
                    self.PC += ToJump
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x30:  # BMI Branch On Result Minus - relative
                self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if self.N == 1:
                    self.Cycles += 1
                    ToJump = unsignedToSigned8bit(self.Memory[self.PC + 1])
                    if self.PC & 0xFF00 != (self.PC + ToJump + 2) & 0xFF00:
                        self.Cycles += 1
                    self.PC += ToJump
                self.PC = (self.PC + 2) & 0xFFFF

            case 0xD0:  # BNE Branch On Result not Zero - relative
                self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if self.Z == 0:
                    self.Cycles += 1
                    ToJump = unsignedToSigned8bit(self.Memory[self.PC + 1])
                    if self.PC & 0xFF00 != (self.PC + ToJump + 2) & 0xFF00:
                        self.Cycles += 1
                    self.PC += ToJump
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x10:  # BPL Branch On Result Plus - relative
                self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if self.N == 0:
                    self.Cycles += 1
                    ToJump = unsignedToSigned8bit(self.Memory[self.PC + 1])
                    if self.PC & 0xFF00 != (self.PC + ToJump + 2) & 0xFF00:
                        self.Cycles += 1
                    self.PC += ToJump
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x50:  # BVC Branch On Overflow Clear - relative
                self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if self.V == 0:
                    self.Cycles += 1
                    ToJump = unsignedToSigned8bit(self.Memory[self.PC + 1])
                    if self.PC & 0xFF00 != (self.PC + ToJump + 2) & 0xFF00:
                        self.Cycles += 1
                    self.PC += ToJump
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x70:  # BVS Branch On Overflow Set - relative
                self.Cycles = 2
                # on branch 3 cycles
                # on branch with cross page 4 cycles
                if self.V == 1:
                    self.Cycles += 1
                    ToJump = unsignedToSigned8bit(self.Memory[self.PC + 1])
                    if self.PC & 0xFF00 != (self.PC + ToJump + 2) & 0xFF00:
                        self.Cycles += 1
                    self.PC += ToJump
                self.PC = (self.PC + 2) & 0xFFFF
            # -----------------------------------------------------------------

            case 0x24:  # BIT zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                M = self.Memory[p]
                self.N = 1 if M & 0x80 else 0
                self.V = 1 if M & 0x40 else 0
                self.Z = 1 if M & self.A == 0 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x2C:  # BIT absolute
                self.Cycles = 4
                M = self.Memory[self._readShort(self.PC + 1)]
                self.N = 1 if M & 0x80 else 0
                self.V = 1 if M & 0x40 else 0
                self.Z = 1 if (M & self.A) == 0 else 0
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x00:  # BRK
                self.Cycles = 7
                SR = 0
                SR += self.N * (1 << 7)
                SR += self.V * (1 << 6)
                SR += 1 * (1 << 5)  # IDK chat said it's always 1 during break
                SR += 1 * (1 << 4)  # self.B = 1
                SR += self.D * (1 << 3)
                SR += self.I * (1 << 2)
                SR += self.Z * (1 << 1)
                SR += self.C * (1 << 0)
                self._push((self.PC + 2) >> 8)
                self._push((self.PC + 2) & 0xFF)
                self._push(SR)
                self.I = 1
                self.PC = self._readShort(0xFFFE)

            # Flag Clear ------------------------------------------------------

            case 0x18:  # CLC Clear Carry Flag
                self.Cycles = 2
                self.C = 0
                self.PC = (self.PC + 1) & 0xFFFF
            case 0xD8:  # CLD Clear Deciaml Flag
                self.Cycles = 2
                self.D = 0
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x58:  # CLI Clear Interrupt Disable Flag
                self.Cycles = 2
                self.I = 0
                self.PC = (self.PC + 1) & 0xFFFF
            case 0xB8:  # CLV Clear Overflow Flag
                self.Cycles = 2
                self.V = 0
                self.PC = (self.PC + 1) & 0xFFFF

            # CMP Compare Memory with Accumulator ------------------------------
            case 0xC9:  # CMP immediate
                self.Cycles = 2
                B = self.Memory[self.PC + 1]
                self.C = 1 if self.A >= B else 0
                self.Z = 1 if self.A == B else 0
                self.N = 1 if (self.A - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xC5:  # CMP zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                B = self.Memory[p]
                self.C = 1 if self.A >= B else 0
                self.Z = 1 if self.A == B else 0
                self.N = 1 if (self.A - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xD5:  # CMP zeropage,x
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                B = self.Memory[p]
                self.C = 1 if self.A >= B else 0
                self.Z = 1 if self.A == B else 0
                self.N = 1 if (self.A - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xCD:  # CMP absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                B = self.Memory[p]
                self.C = 1 if self.A >= B else 0
                self.Z = 1 if self.A == B else 0
                self.N = 1 if (self.A - B) & 0x80 else 0
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xDD:  # CMP absolute,X
                self.Cycles = 4
                p = self._addressingAbsoluteX(self.PC + 1)
                B = self.Memory[p]
                self.C = 1 if self.A >= B else 0
                self.Z = 1 if self.A == B else 0
                self.N = 1 if (self.A - B) & 0x80 else 0
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xD9:  # CMP absolute,Y
                self.Cycles = 4
                p = self._addressingAbsoluteY(self.PC + 1)
                B = self.Memory[p]
                self.C = 1 if self.A >= B else 0
                self.Z = 1 if self.A == B else 0
                self.N = 1 if (self.A - B) & 0x80 else 0
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xC1:  # CMP indirect,X
                self.Cycles = 6
                p = self._addressingIndirectX(self.PC + 1)
                B = self.Memory[p]
                self.C = 1 if self.A >= B else 0
                self.Z = 1 if self.A == B else 0
                self.N = 1 if (self.A - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xD1:  # CMP indirect,Y
                self.Cycles = 5
                p = self._addressingIndirectY(self.PC + 1)
                B = self.Memory[p]
                self.C = 1 if self.A >= B else 0
                self.Z = 1 if self.A == B else 0
                self.N = 1 if (self.A - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF

            # CPX Compare Memory and X -------------------------

            case 0xE0:  # CPX immediate
                self.Cycles = 2
                B = self.Memory[self.PC + 1]
                self.C = 1 if self.X >= B else 0
                self.Z = 1 if self.X == B else 0
                self.N = 1 if (self.X - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xE4:  # CPX zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                B = self.Memory[p]
                self.C = 1 if self.X >= B else 0
                self.Z = 1 if self.X == B else 0
                self.N = 1 if (self.X - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xEC:  # CPX absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                B = self.Memory[p]
                self.C = 1 if self.X >= B else 0
                self.Z = 1 if self.X == B else 0
                self.N = 1 if (self.X - B) & 0x80 else 0
                self.PC = (self.PC + 3) & 0xFFFF

            # CPY Compare Memory and X -------------------------
            case 0xC0:  # CPY immediate
                self.Cycles = 2
                B = self.Memory[self.PC + 1]
                self.C = 1 if self.Y >= B else 0
                self.Z = 1 if self.Y == B else 0
                self.N = 1 if (self.Y - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xC4:  # CPY zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                B = self.Memory[p]
                self.C = 1 if self.Y >= B else 0
                self.Z = 1 if self.Y == B else 0
                self.N = 1 if (self.Y - B) & 0x80 else 0
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xCC:  # CPY absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                B = self.Memory[p]
                self.C = 1 if self.Y >= B else 0
                self.Z = 1 if self.Y == B else 0
                self.N = 1 if (self.Y - B) & 0x80 else 0
                self.PC = (self.PC + 3) & 0xFFFF

            # DEC Decrement Memory by One -----------------

            case 0xC6:  # DEC zeropage
                self.Cycles = 5
                p = self.Memory[self.PC + 1]
                self.Memory[p] = (self.Memory[p] - 1) & 0xFF
                self._updateNZ(self.Memory[p])
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xD6:  # DEC zeropage,X
                self.Cycles = 6
                p = self._addressingZeropageX(self.PC + 1)
                self.Memory[p] = (self.Memory[p] - 1) & 0xFF
                self._updateNZ(self.Memory[p])
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xCE:  # DEC absolute
                self.Cycles = 6
                p = self._readShort(self.PC + 1)
                self.Memory[p] = (self.Memory[p] - 1) & 0xFF
                self._updateNZ(self.Memory[p])
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xDE:  # DEC absolute,X
                self.Cycles = 7
                p = (self._readShort(self.PC + 1) + self.X) & 0xFFFF
                self.Memory[p] = (self.Memory[p] - 1) & 0xFF
                self._updateNZ(self.Memory[p])
                self.PC = (self.PC + 3) & 0xFFFF

            # --------------------------------------------------

            case 0xCA:  # DEX Decreament X by one
                self.Cycles = 2
                self.X = (self.X - 1) & 0xFF
                self._updateNZ(self.X)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x88:  # DEY Decreament Y by one
                self.Cycles = 2
                self.Y = (self.Y - 1) & 0xFF
                self._updateNZ(self.Y)
                self.PC = (self.PC + 1) & 0xFFFF

            # Copied 'AND' Section
            # EOR Exclusive-OR Memory with Accumulator -----------------
            case 0x49:  # EOR immediate
                self.Cycles = 2
                self.A = self.A ^ self.Memory[self.PC + 1]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x45:  # EOR zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.A = self.A ^ self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x55:  # EOR zeropage,X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                self.A = self.A ^ self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x4D:  # EOR absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.A = self.A ^ self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x5D:  # EOR absolute,X
                self.Cycles = 4
                p = self._addressingAbsoluteX(self.PC + 1)
                self.A = self.A ^ self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x59:  # EOR absolute,Y
                self.Cycles = 4
                p = self._addressingAbsoluteY(self.PC + 1)
                self.A = self.A ^ self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x41:  # EOR indirect,X
                self.Cycles = 6
                p = self._addressingIndirectX(self.PC + 1)
                self.A = self.A ^ self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x51:  # EOR indirect,y
                self.Cycles = 5
                p = self._addressingIndirectY(self.PC + 1)
                self.A = self.A ^ self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            # Copied DEC section
            # INC Increment Memory by One -----------------

            case 0xE6:  # INC zeropage
                self.Cycles = 5
                p = self.Memory[self.PC + 1]
                self.Memory[p] = (self.Memory[p] + 1) & 0xFF
                self._updateNZ(self.Memory[p])
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xF6:  # INC zeropage,X
                self.Cycles = 6
                p = self._addressingZeropageX(self.PC + 1)
                self.Memory[p] = (self.Memory[p] + 1) & 0xFF
                self._updateNZ(self.Memory[p])
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xEE:  # INC absolute
                self.Cycles = 6
                p = self._readShort(self.PC + 1)
                self.Memory[p] = (self.Memory[p] + 1) & 0xFF
                self._updateNZ(self.Memory[p])
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xFE:  # INC absolute,X
                self.Cycles = 7
                p = (self._readShort(self.PC + 1) + self.X) & 0xFFFF
                self.Memory[p] = (self.Memory[p] + 1) & 0xFF
                self._updateNZ(self.Memory[p])
                self.PC = (self.PC + 3) & 0xFFFF

            # --------------------------------------------------

            case 0xE8:  # INX Increament X by one
                self.Cycles = 2
                self.X = (self.X + 1) & 0xFF
                self._updateNZ(self.X)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0xC8:  # INY Increament Y by one
                self.Cycles = 2
                self.Y = (self.Y + 1) & 0xFF
                self._updateNZ(self.Y)
                self.PC = (self.PC + 1) & 0xFFFF

            # JMP -------------------------------------------
            case 0x4C:  # JMP absolute
                self.Cycles = 3
                self.PC = self._readShort(self.PC + 1)
            case 0x6C:  # jmp indirect
                self.Cycles = 5
                # p address of value where to jmp
                # some hardware bug said by chat
                pL = self.Memory[self.PC + 1]
                pH = self.Memory[self.PC + 2]
                PCL = self.Memory[pL + pH * (1 << 8)]
                PCH = self.Memory[((pL + 1) & 0xFF) + pH * (1 << 8)]
                self.PC = PCL + PCH * (1 << 8)
            case (
                0x20
            ):  # JSR Jump to New Location Saving Return Address (jmp sub-routine)
                self.Cycles = 6
                PC = self.PC + 2
                self._push(PC >> 8)
                self._push(PC & 0xFF)
                self.PC = self._readShort(self.PC + 1)

            # LDA Load A with Memory
            case 0xA9:  # LDA immediate
                self.Cycles = 2
                self.A = self.Memory[self.PC + 1]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xA5:  # LDA zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.A = self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xB5:  # LDA zeropage,X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                self.A = self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xAD:  # LDA absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.A = self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xBD:  # LDA absolute,X
                self.Cycles = 4
                p = self._addressingAbsoluteX(self.PC + 1)
                self.A = self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xB9:  # LDA absolute,Y
                self.Cycles = 4
                p = self._addressingAbsoluteY(self.PC + 1)
                self.A = self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xA1:  # LDA indirect,X
                self.Cycles = 6
                p = self._addressingIndirectX(self.PC + 1)
                self.A = self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xB1:  # LDA indirect,Y
                self.Cycles = 5
                p = self._addressingIndirectY(self.PC + 1)
                self.A = self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            # Copied LDA
            # LDX Load X with Memory
            case 0xA2:  # LDX immediate
                self.Cycles = 2
                self.X = self.Memory[self.PC + 1]
                self._updateNZ(self.X)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xA6:  # LDX zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.X = self.Memory[p]
                self._updateNZ(self.X)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xB6:  # LDX zeropage,Y
                self.Cycles = 4
                p = self._addressingZeropageY(self.PC + 1)
                self.X = self.Memory[p]
                self._updateNZ(self.X)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xAE:  # LDX absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.X = self.Memory[p]
                self._updateNZ(self.X)
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xBE:  # LDX absolute,Y
                self.Cycles = 4
                p = self._addressingAbsoluteY(self.PC + 1)
                self.X = self.Memory[p]
                self._updateNZ(self.X)
                self.PC = (self.PC + 3) & 0xFFFF

            # Copied LDX
            # LDY Load Y with Memory
            case 0xA0:  # LDY immediate
                self.Cycles = 2
                self.Y = self.Memory[self.PC + 1]
                self._updateNZ(self.Y)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xA4:  # LDY zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.Y = self.Memory[p]
                self._updateNZ(self.Y)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xB4:  # LDY zeropage,X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                self.Y = self.Memory[p]
                self._updateNZ(self.Y)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xAC:  # LDY absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.Y = self.Memory[p]
                self._updateNZ(self.Y)
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xBC:  # LDY absolute,X
                self.Cycles = 4
                p = self._addressingAbsoluteX(self.PC + 1)
                self.Y = self.Memory[p]
                self._updateNZ(self.Y)
                self.PC = (self.PC + 3) & 0xFFFF

            # LSR Shift Right
            case 0x4A:  # LSR accumulator
                self.Cycles = 2
                self.C = self.A & 0x01
                self.A = (self.A >> 1) & 0xFF
                self._updateNZ(self.A)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x46:  # LSR zeropage
                self.Cycles = 5
                p = self.Memory[self.PC + 1]
                M = self.Memory[p]
                self.C = M & 0x01
                M = (M >> 1) & 0xFF
                self._updateNZ(M)
                self.Memory[p] = M
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x56:  # LSR zeropage,X
                self.Cycles = 6
                p = self._addressingZeropageX(self.PC + 1)
                M = self.Memory[p]
                self.C = M & 0x01
                M = (M >> 1) & 0xFF
                self._updateNZ(M)
                self.Memory[p] = M
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x4E:  # LSR absolute
                self.Cycles = 6
                p = self._readShort(self.PC + 1)
                M = self.Memory[p]
                self.C = M & 0x01
                M = (M >> 1) & 0xFF
                self._updateNZ(M)
                self.Memory[p] = M
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x5E:  # LSR absolute,X
                self.Cycles = 7
                p = (self._readShort(self.PC + 1) + self.X) & 0xFFFF
                M = self.Memory[p]
                self.C = M & 0x01
                M = (M >> 1) & 0xFF
                self._updateNZ(M)
                self.Memory[p] = M
                self.PC = (self.PC + 3) & 0xFFFF

            # --------------------------------------------------------
            case 0xEA:  # NOP
                self.Cycles = 2
                self.PC = (self.PC + 1) & 0xFFFF

            # Copied 'EOR' Section
            # ORA OR Memory with Accumulator -----------------
            case 0x09:  # ORA immediate
                self.Cycles = 2
                self.A = self.A | self.Memory[self.PC + 1]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x05:  # ORA zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.A = self.A | self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x15:  # ORA zeropage,X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                self.A = self.A | self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x0D:  # ORA absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.A = self.A | self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x1D:  # ORA absolute,X
                self.Cycles = 4
                p = self._addressingAbsoluteX(self.PC + 1)
                self.A = self.A | self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x19:  # ORA absolute,Y
                self.Cycles = 4
                p = self._addressingAbsoluteY(self.PC + 1)
                self.A = self.A | self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 3) & 0xFFFF

            case 0x01:  # ORA indirect,X
                self.Cycles = 6
                p = self._addressingIndirectX(self.PC + 1)
                self.A = self.A | self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x11:  # ORA indirect,y
                self.Cycles = 5
                p = self._addressingIndirectY(self.PC + 1)
                self.A = self.A | self.Memory[p]
                self._updateNZ(self.A)
                self.PC = (self.PC + 2) & 0xFFFF

            # Stack operations -----------------------------------
            case 0x48:  # PHA Push A on Stack
                self.Cycles = 3
                self._push(self.A)
                self.PC = (self.PC + 1) & 0xFFFF

            case 0x08:  # PHP Push Processor Status on Stack
                self.Cycles = 3
                SR = 0
                SR += self.N * (1 << 7)
                SR += self.V * (1 << 6)
                SR += 1 * (1 << 5)  # IDK chat said it's always 1 during break
                SR += 1 * (1 << 4)  # self.B = 1
                SR += self.D * (1 << 3)
                SR += self.I * (1 << 2)
                SR += self.Z * (1 << 1)
                SR += self.C * (1 << 0)
                self._push(SR)
                self.PC = (self.PC + 1) & 0xFFFF

            case 0x68:  # PLA Pull A from Stack
                self.Cycles = 4
                self.A = self._pull()
                self._updateNZ(self.A)
                self.PC = (self.PC + 1) & 0xFFFF

            case 0x28:  # PLP Pull Processor Status from Stack
                self.Cycles = 4
                SR = self._pull()
                self.C = (SR >> 0) & 0x1
                self.Z = (SR >> 1) & 0x1
                self.I = (SR >> 2) & 0x1
                self.D = (SR >> 3) & 0x1
                self.V = (SR >> 6) & 0x1
                self.N = (SR >> 7) & 0x1
                self.PC = (self.PC + 1) & 0xFFFF

            # ROL Rotate One Bit Left ---------------------------------
            case 0x2A:  # ROL accumulator
                self.Cycles = 2
                M = (self.A << 1) + self.C
                self.C = M >> 8
                self.A = M & 0xFF
                self._updateNZ(self.A)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x26:  # ROL zeropage
                self.Cycles = 5
                p = self.Memory[self.PC + 1]
                M = self.Memory[p]
                M = (M << 1) + self.C
                self.C = M >> 8
                self.Memory[p] = M & 0xFF
                self._updateNZ(M)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x36:  # ROL zeropage,X
                self.Cycles = 6
                p = self._addressingZeropageX(self.PC + 1)
                M = self.Memory[p]
                M = (M << 1) + self.C
                self.C = M >> 8
                self.Memory[p] = M & 0xFF
                self._updateNZ(M)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x2E:  # ROL absolute
                self.Cycles = 6
                p = self._readShort(self.PC + 1)
                M = self.Memory[p]
                M = (M << 1) + self.C
                self.C = M >> 8
                self.Memory[p] = M & 0xFF
                self._updateNZ(M)
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x3E:  # ROL absolute,X
                self.Cycles = 7
                p = (self._readShort(self.PC + 1) + self.X) & 0xFFFF
                M = self.Memory[p]
                M = (M << 1) + self.C
                self.C = M >> 8
                self.Memory[p] = M & 0xFF
                self._updateNZ(M)
                self.PC = (self.PC + 3) & 0xFFFF

            # Copied ROL
            # ROR Rotate One Bit Right ---------------------------------
            case 0x6A:  # ROR accumulator
                self.Cycles = 2
                M = (self.A >> 1) + (self.C << 7)
                self.C = self.A & 0x1
                self.A = M & 0xFF
                self._updateNZ(self.A)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x66:  # ROR zeropage
                self.Cycles = 5
                p = self.Memory[self.PC + 1]
                M = self.Memory[p]
                NM = (M >> 1) + (self.C << 7)
                self.C = M & 0x1
                self.Memory[p] = NM & 0xFF
                self._updateNZ(NM)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x76:  # ROR zeropage,X
                self.Cycles = 6
                p = self._addressingZeropageX(self.PC + 1)
                M = self.Memory[p]
                NM = (M >> 1) + (self.C << 7)
                self.C = M & 0x1
                self.Memory[p] = NM & 0xFF
                self._updateNZ(NM)
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x6E:  # ROR absolute
                self.Cycles = 6
                p = self._readShort(self.PC + 1)
                M = self.Memory[p]
                NM = (M >> 1) + (self.C << 7)
                self.C = M & 0x1
                self.Memory[p] = NM & 0xFF
                self._updateNZ(NM)
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x7E:  # ROR absolute,X
                self.Cycles = 7
                p = (self._readShort(self.PC + 1) + self.X) & 0xFFFF
                M = self.Memory[p]
                NM = (M >> 1) + (self.C << 7)
                self.C = M & 0x1
                self.Memory[p] = NM & 0xFF
                self._updateNZ(NM)
                self.PC = (self.PC + 3) & 0xFFFF

            # -----------------------------------------------------------

            case 0x40:  # RTI Return from Interrupt
                self.Cycles = 6
                SR = self._pull()
                self.C = (SR >> 0) & 0x1
                self.Z = (SR >> 1) & 0x1
                self.I = (SR >> 2) & 0x1
                self.D = (SR >> 3) & 0x1
                self.V = (SR >> 6) & 0x1
                self.N = (SR >> 7) & 0x1
                PCL = self._pull()
                PCH = self._pull()
                self.PC = PCL + (PCH << 8)

            case 0x60:  # RTS Return from Subroutine
                self.Cycles = 6
                PCL = self._pull()
                PCH = self._pull()
                PC = PCL + (PCH << 8)
                self.PC = (PC + 1) & 0xFFFF

            # SBC Subtract Memory from Accumulator with Borrow

            case 0xE9:  # SBC immediate
                self.Cycles = 2
                M = self.Memory[self.PC + 1]
                R = self.A - M - (1 - self.C)
                self._SBCFlags(self.A, M, R)
                self.A = R & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xE5:  # SBC zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                M = self.Memory[p]
                R = self.A - M - (1 - self.C)
                self._SBCFlags(self.A, M, R)
                self.A = R & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xF5:  # SBC zeropage,X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                M = self.Memory[p]
                R = self.A - M - (1 - self.C)
                self._SBCFlags(self.A, M, R)
                self.A = R & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xED:  # SBC absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                M = self.Memory[p]
                R = self.A - M - (1 - self.C)
                self._SBCFlags(self.A, M, R)
                self.A = R & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xFD:  # SBC absolute,X
                self.Cycles = 4
                p = self._addressingAbsoluteX(self.PC + 1)
                M = self.Memory[p]
                R = self.A - M - (1 - self.C)
                self._SBCFlags(self.A, M, R)
                self.A = R & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xF9:  # SBC absolute,Y
                self.Cycles = 4
                p = self._addressingAbsoluteY(self.PC + 1)
                M = self.Memory[p]
                R = self.A - M - (1 - self.C)
                self._SBCFlags(self.A, M, R)
                self.A = R & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0xE1:  # SBC indirect,X
                self.Cycles = 6
                p = self._addressingIndirectX(self.PC + 1)
                M = self.Memory[p]
                R = self.A - M - (1 - self.C)
                self._SBCFlags(self.A, M, R)
                self.A = R & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0xF1:  # SBC indirect,Y
                self.Cycles = 5
                p = self._addressingIndirectY(self.PC + 1)
                M = self.Memory[p]
                R = self.A - M - (1 - self.C)
                self._SBCFlags(self.A, M, R)
                self.A = R & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF

            # Set Flags ---------------------------------------

            case 0x38:  # Set Carry Flag
                self.Cycles = 2
                self.C = 1
                self.PC = (self.PC + 1) & 0xFFFF
            case 0xF8:  # Set Decimal Flag
                self.Cycles = 2
                self.D = 1
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x78:  # Set Interrupt Disable Flag
                self.Cycles = 2
                self.I = 1
                self.PC = (self.PC + 1) & 0xFFFF

            # STA Store Accumulator in Memory

            case 0x85:  # STA zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.Memory[p] = self.A & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x95:  # STA zeropage,X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                self.Memory[p] = self.A & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x8D:  # STA absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.Memory[p] = self.A & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x9D:  # STA absolute,X
                self.Cycles = 5
                p = (self._readShort(self.PC + 1) + self.X) & 0xFFFF
                self.Memory[p] = self.A & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x99:  # STA absolute,Y
                self.Cycles = 5
                p = (self._readShort(self.PC + 1) + self.Y) & 0xFFFF
                self.Memory[p] = self.A & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF
            case 0x81:  # STA indirect,X
                self.Cycles = 6
                p = self._addressingIndirectX(self.PC + 1)
                self.Memory[p] = self.A & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF
            case 0x91:  # STA indirect,Y
                self.Cycles = 6
                pp = self.Memory[self.PC + 1]
                p = (self._readShort(pp) + self.Y) & 0xFFFF
                self.Memory[p] = self.A & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF

            # STX Store X in Memory--------------------------------

            case 0x86:  # STX zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.Memory[p] = self.X & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x96:  # STX zeropage,Y
                self.Cycles = 4
                p = self._addressingZeropageY(self.PC + 1)
                self.Memory[p] = self.X & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x8E:  # STX absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.Memory[p] = self.X & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF

            # Copied STX

            # STX Store X in Memory--------------------------------

            case 0x84:  # STY zeropage
                self.Cycles = 3
                p = self.Memory[self.PC + 1]
                self.Memory[p] = self.Y & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x94:  # STY zeropage,X
                self.Cycles = 4
                p = self._addressingZeropageX(self.PC + 1)
                self.Memory[p] = self.Y & 0xFF
                self.PC = (self.PC + 2) & 0xFFFF

            case 0x8C:  # STY absolute
                self.Cycles = 4
                p = self._readShort(self.PC + 1)
                self.Memory[p] = self.Y & 0xFF
                self.PC = (self.PC + 3) & 0xFFFF

            # Transfer operations --------------------------------------

            case 0xAA:  # TAX Transfer A to X
                self.Cycles = 2
                self.X = self.A
                self._updateNZ(self.X)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0xA8:  # TAY Transfer A to Y
                self.Cycles = 2
                self.Y = self.A
                self._updateNZ(self.Y)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0xBA:  # TSX Transfer Stack Pointer to X
                self.Cycles = 2
                self.X = self.SP
                self._updateNZ(self.X)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x8A:  # TXA Transfer X to A
                self.Cycles = 2
                self.A = self.X
                self._updateNZ(self.A)
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x9A:  # TXS Transfer X to Stack Pointer
                self.Cycles = 2
                self.SP = self.X
                self.PC = (self.PC + 1) & 0xFFFF
            case 0x98:  # TYA Transfer Y to A
                self.Cycles = 2
                self.A = self.Y
                self._updateNZ(self.A)
                self.PC = (self.PC + 1) & 0xFFFF
            case _:
                self.Cycles = 2
                self.PC = (self.PC + 1) & 0xFFFF
