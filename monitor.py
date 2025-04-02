import pygame
import pygame.locals


class monitor:
    def __init__(Self, Memory: list, Scale: int = 1):
        Self.Memory = Memory
        Self.Scale = Scale
        Self.WindowOpen = 1
        pygame.init()
        pygame.display.set_caption("6502")
        Self.Width = 320 * Scale
        Self.Height = 320 * Scale
        Self.Display = pygame.display.set_mode((Self.Width, Self.Height), vsync=1)

    def _8bitTo24bitColor(Self, Color: int):
        r = (Color >> 5) & 0x7
        g = (Color >> 2) & 0x7
        b = Color & 0x3
        # r / 7 normalize -> scale to 8 bit
        r = round((r / 7) * 255)
        g = round((g / 7) * 255)
        b = round((b / 3) * 255)
        return (r, g, b)

    # read memory 0x200 - 0x5FF
    def update(Self):
        for x in range(32):
            for y in range(32):
                M = Self.Memory[0x200 + (y * 32) + x]
                C = Self._8bitTo24bitColor(M)
                pygame.draw.rect(
                    Self.Display,
                    C,
                    (
                        10 * x * Self.Scale,
                        10 * y * Self.Scale,
                        32 * Self.Scale,
                        32 * Self.Scale,
                    ),
                )
        pygame.display.update()
