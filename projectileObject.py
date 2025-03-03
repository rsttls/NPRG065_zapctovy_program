from DrawableObject import DrawableObject
import math
from pygame import Vector2 as vec2


ProjetileQueue = []
ProjectileTexture = []

class ProjectileObject(DrawableObject):
    def _DrawableObjectInit(Self):
        Self.Texture = ProjectileTexture[Self.Type]
        Self.Scale = 1
        Self.Rotation = math.degrees(math.atan2(Self.Direction.y, Self.Direction.x))
        Self.Pivot = Self.Texture.Pivot
        Self.FlipX = 0
        Self.FlipY = 0

    def __init__(Self, Pos: vec2, Direction: vec2, Type=0, Velocity=1):
        global ProjetileQueue
        Self.Pos = Pos
        Self.Direction = Direction
        Self.Type = Type
        Self.Velocity = Velocity
        Self.Lifespan = 0
        Self._DrawableObjectInit()
        ProjetileQueue.append(Self)

    def update(Self, DeltaTime):
        Self.Pos = Self.Pos + DeltaTime * Self.Direction * Self.Velocity
        Self.Lifespan += DeltaTime
        if Self.Lifespan > 5000:
            ProjetileQueue.remove(Self)

    def draw(Self):
        Self.drawCentered()
