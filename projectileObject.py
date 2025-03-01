from collisionObject import *

projetileQueue = []

class projectileObject(collisionObejct):
    def __init__(self, Position, Direction, HasCollision = 1):
        global projetileQueue
        global collisionQueue
        self.Position = Position
        self.Direction = Direction
        self.Lifespan = 0
        projetileQueue.append(self)
        if HasCollision:
            collisionQueue.append(self)

    def update(self, deltaTime):
        self.Position = self.Position + deltaTime * self.Direction
        self.Lifespan += deltaTime
        if self.Lifespan > 5000:
            projetileQueue.remove(self)
            collisionQueue.remove(self)
