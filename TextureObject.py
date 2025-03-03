import pygame
import os
from pygame import Vector2 as Vec2


class TextureObject:
    def __init__(Self, RelativePath, Pivot=None, PreScale=1):
        Self.Image = pygame.image.load(
            os.path.dirname(__file__) + RelativePath
        ).convert_alpha()

        if PreScale != 1:
            Self.Image = pygame.transform.scale_by(Self.Image, PreScale)
        if Pivot == None:
            Self.Pivot = Vec2(Self.Image.get_rect().size) / 2
        else:
            Self.Pivot = Pivot
        Rect = Self.Image.get_rect()
        Self.W = Rect.w
        Self.H = Rect.h
        Self.Center = Vec2(Rect.center)

    def draw(Self, Pos:Vec2, Scale=1, Rotation=0, Pivot=None, FlipX=0, FlipY=0):
        TransformedImage = Self.Image
        if FlipX != 0 or FlipY != 0:
            TransformedImage = pygame.transform.flip(TransformedImage, FlipX, FlipY)
        if Scale != 1:
            TransformedImage = pygame.transform.scale_by(TransformedImage, Scale)

        # vector magic
        # mozna tu bude problem s zrcadlenim a pivotem
        if Rotation != 0:
            PreRotationRect = TransformedImage.get_rect()
            if Pivot == None:
                Pivot = Self.Pivot * Scale
                if Pivot == None:
                    Pivot = (PreRotationRect.w // 2, PreRotationRect.h // 2)
            TransformedImage = pygame.transform.rotate(TransformedImage, -Rotation)
            NewRect = TransformedImage.get_rect()
            V = Vec2(Pivot) - Vec2(PreRotationRect.center)
            RV = V.rotate(Rotation)
            NewRect.center = PreRotationRect.center
            NewRect.center += V - RV
        else:
            NewRect = TransformedImage.get_rect()
        NewRect.x += Pos.x
        NewRect.y += Pos.y
        pygame.display.get_surface().blit(TransformedImage, NewRect)

    # draw texture at x,y as it's center
    def drawCentered(Self, Pos, Scale=1, Rotation=0, Pivot=None, FlipX=0, FlipY=0):
        Self.draw(
            Pos - Self.Center, Scale, Rotation, Pivot, FlipX, FlipY
        )
