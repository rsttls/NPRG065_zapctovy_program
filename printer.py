class printer:
    def __init__(Self, Memory: list):
        Self.Memory = Memory

    def update(Self):
        if Self.Memory[0xFE] == 1:
            print(chr(Self.Memory[0xFF]), end="", flush=1)
            Self.Memory[0xFE] = 0
