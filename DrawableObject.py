from TextureObject import TextureObject
from pygame import Vector2 as Vec2


class DrawableObject:
    def __init__(
        Self,
        Texture: TextureObject,
        Pos: Vec2 = (0, 0),
        Scale=1,
        Rotation=0,
        Pivot=None,
        FlipX=0,
        FlipY=0,
    ):
        Self.Texture = Texture
        Self.Pos = Pos
        Self.Scale = Scale
        Self.Rotation = Rotation
        if Pivot == None:
            Self.Pivot = Self.Texture.Pivot
        else:
            Self.Pivot = Pivot
        Self.FlipX = FlipX
        Self.FlipY = FlipY

    def draw(Self):
        Self.Texture.draw(
            Self.Pos, Self.Scale, Self.Rotation, Self.Pivot, Self.FlipX, Self.FlipY
        )

    def drawCentered(Self):
        Self.Texture.drawCentered(
            Self.Pos, Self.Scale, Self.Rotation, Self.Pivot, Self.FlipX, Self.FlipY
        )
