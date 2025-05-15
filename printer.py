class printer:
    """
    A simple memory-mapped printer emulator.

    This device reads from memory location 0xFF when triggered by 0xFE,
    simulating character output (e.g., console print).
    """

    def __init__(self, Memory: list):
        """
        Initialize the printer with a reference to the shared memory.

        Args:
            Memory (list): A list representing system memory.
        """
        self.Memory = Memory

    def update(self):
        """
        Check the memory-mapped output trigger and print a character.

        If Memory[0xFE] is set to 1, the printer reads Memory[0xFF],
        interprets it as an ASCII character, prints it to the console,
        and resets the trigger flag to 0.
        """
        if self.Memory[0xFE] == 1:
            print(chr(self.Memory[0xFF]), end="", flush=True)
            self.Memory[0xFE] = 0
