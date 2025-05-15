import pygame
import pygame.locals


class monitor:
    def __init__(self, Memory: list, Scale: int = 1):
        """
        Initialize the monitor with a reference to the memory and a scale factor.
        Displays values in memory 0x200 - 0x5FF with a 8-bit RGB value (RRRGGGBB).
        Args:
            Memory (list): The shared memory array to read from.
            Scale (int): Scale factor for enlarging the display window.
        """
        self.Memory = Memory
        self.Scale = Scale
        self.WindowOpen = 1
        pygame.init()
        pygame.display.set_caption("6502")
        self.Width = 320 * Scale
        self.Height = 320 * Scale
        self.Display = pygame.display.set_mode((self.Width, self.Height), vsync=1)

    def _8bitTo24bitColor(self, Color: int):
        """
        Convert an 8-bit color value to a 24-bit RGB tuple.

        The 8-bit color format:
        - Top 3 bits: red (0-7)
        - Middle 3 bits: green (0-7)
        - Bottom 2 bits: blue (0-3)

        Args:
            Color (int): An 8-bit packed color value.

        Returns:
            tuple: A (R, G, B) tuple scaled to 8-bit color channels (0-255).
        """
        r = (Color >> 5) & 0x7
        g = (Color >> 2) & 0x7
        b = Color & 0x3
        # r / 7 normalize -> scale to 8 bit
        r = round((r / 7) * 255)
        g = round((g / 7) * 255)
        b = round((b / 3) * 255)
        return (r, g, b)

    # read memory 0x200 - 0x5FF
    def update(self):
        """
        Update the monitor display.

        Reads from memory range 0x0200 to 0x05FF (32x32 grid), converts the
        color values, and draws them as rectangles on the screen.
        """
        for x in range(32):
            for y in range(32):
                M = self.Memory[0x200 + (y * 32) + x]
                C = self._8bitTo24bitColor(M)
                pygame.draw.rect(
                    self.Display,
                    C,
                    (
                        10 * x * self.Scale,
                        10 * y * self.Scale,
                        32 * self.Scale,
                        32 * self.Scale,
                    ),
                )
        pygame.display.update()
