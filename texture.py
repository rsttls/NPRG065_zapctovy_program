import pygame
import os
from pygame import Vector2 as vec2


class texture:
    def __init__(self, relativePath,  pivot = None):
        self.Image = pygame.image.load(
            os.path.dirname(__file__) + relativePath
        ).convert_alpha()
        if pivot == None:
            self.pivot = vec2(self.Image.get_rect().size)/2
        else:
            self.pivot = pivot


    def draw(self, x, y, scale=1, rotation=0, pivot=None, flipX=0, flipY=0):
        TransformedImage = self.Image
        if flipX != 0 or flipY != 0:
            TransformedImage = pygame.transform.flip(TransformedImage, flipX, flipY)
        if scale != 1:
            TransformedImage = pygame.transform.scale_by(TransformedImage, scale)

        if rotation != 0:
            PreRotationRect = TransformedImage.get_rect()
            if pivot == None:
                pivot = self.pivot*scale
                if pivot == None:
                    pivot = (PreRotationRect.w // 2, PreRotationRect.h // 2)
            TransformedImage = pygame.transform.rotate(TransformedImage, -rotation)
            NewRect = TransformedImage.get_rect()
            v = vec2(pivot) - vec2(PreRotationRect.center)
            rv = v.rotate(rotation)
            NewRect.center = PreRotationRect.center
            NewRect.center +=  v - rv
        else:
            NewRect = TransformedImage.get_rect()
        NewRect.x += x
        NewRect.y += y
        pygame.display.get_surface().blit(TransformedImage, NewRect)
