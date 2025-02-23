import pygame
import os

class texture:
    def __init__(self, relativePath):
        self.Image = pygame.image.load(
            os.path.dirname(__file__) + relativePath
        ).convert_alpha()

    def draw(self, x, y, scale=1, rotation=0, flipX=0, flipY=0):

        TransformedImage = self.Image
        if scale != 1:
            TransformedImage = pygame.transform.scale_by(TransformedImage, scale)
        if rotation != 0:
            TransformedImage = pygame.transform.rotate(TransformedImage, rotation)
        if flipX != 0 or flipY != 0:
            TransformedImage = pygame.transform.flip(TransformedImage, flipX, flipY)
        Rect = TransformedImage.get_rect()
        Rect.x = x
        Rect.y = y
        pygame.display.get_surface().blit(TransformedImage, Rect)

