import pygame
import pygame.locals
import math
import time
import os

from TextureObject import TextureObject
from ProjectileObject import *
from pygame import Vector2 as vec2

# global variables
Width, Height = 640, 480  # window size
MainLoopActive = 1  # if main loop is active
prevMark = time.time_ns() / 1000000
currMark = time.time_ns() / 1000000

# init
pygame.init()
pygame.display.set_caption("IDK Game")
Display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, vsync=1)
desktopWidth, desktopHeight = pygame.display.get_window_size()
(Width, Height) = (desktopWidth, desktopHeight)
pygame.mouse.set_visible(0)


# texture loading
# loads projectile texutures by type
i = 0
while 1:
    if not os.path.isfile(
        os.path.dirname(__file__) + "./assets/projectile/" + str(i) + ".bmp"
    ):
        break
    ProjectileTexture.append(
        TextureObject("./assets/projectile/" + str(i) + ".bmp", PreScale=3)
    )
    i += 1


# code prototyping
AmmoType = 0
cursorTexture = TextureObject("./assets/cursor.bmp", PreScale=2)
MainCharacterTexture = TextureObject("./assets/ilum.bmp", PreScale=2)
GunTexture = TextureObject("./assets/gun.bmp", PreScale=2)
MainCharPos = vec2(100, 100)
MainCharVel = 0.5  # pixel/ms

while MainLoopActive:
    # timing
    deltaTime = currMark - prevMark
    prevMark = currMark
    currMark = time.time_ns() / 1000000
    # events
    for Event in pygame.event.get():
        if Event.type == pygame.locals.QUIT:
            MainLoopActive = 0
        elif Event.type == pygame.locals.VIDEORESIZE:
            Width = Display.get_width()
            Height = Display.get_height()
        elif Event.type == pygame.KEYDOWN:
            if Event.key == pygame.K_ESCAPE:
                MainLoopActive = 0
            if Event.key == pygame.K_F11:
                if pygame.display.is_fullscreen():
                    Width = 640
                    Height = 480
                    pygame.display.set_mode((Width, Height), pygame.RESIZABLE, vsync=1)
                else:
                    pygame.display.set_mode(
                        (desktopWidth, desktopHeight), pygame.FULLSCREEN, vsync=1
                    )
                    Width, Height = desktopWidth, desktopHeight
            if Event.key == pygame.K_SPACE:
                ProjectileObject(
                    GunCenterPos,
                    vec2(mousePos - GunCenterPos).normalize(),
                    Type=AmmoType,
                    Velocity=1,
                )
            if Event.key == pygame.K_LSHIFT:
                AmmoType = 1 if AmmoType == 0 else 0
        elif Event.type == pygame.MOUSEBUTTONDOWN:
            ProjectileObject(
                GunCenterPos,
                vec2(mousePos - GunCenterPos).normalize(),
                Type=AmmoType,
                Velocity=1,
            )
    keysPressed = pygame.key.get_pressed()
    if keysPressed[pygame.K_a]:
        MainCharPos.x -= MainCharVel * deltaTime
    if keysPressed[pygame.K_d]:
        MainCharPos.x += MainCharVel * deltaTime
    if keysPressed[pygame.K_w]:
        MainCharPos.y -= MainCharVel * deltaTime
    if keysPressed[pygame.K_s]:
        MainCharPos.y += MainCharVel * deltaTime
    mousePos = vec2(pygame.mouse.get_pos())
    # update
    for projectile in ProjetileQueue:
        projectile.update(deltaTime)

    # gun pos/rot
    GunCenterPos = vec2(MainCharPos.x + 96, MainCharPos.y + 74)
    GunRotation = math.degrees(math.atan2(mousePos.y - GunCenterPos.y, mousePos.x - GunCenterPos.x))

    # draw
    Display.fill((50, 50, 50))

    MainCharacterTexture.draw(MainCharPos)
    for projectile in ProjetileQueue:
        projectile.draw()

    print(str(GunRotation))
    if 90 < GunRotation or GunRotation < -90:
        GunTexture.drawCentered(
            GunCenterPos,
            Rotation=GunRotation,
            FlipY=1,
        )
    else:
        GunTexture.drawCentered(GunCenterPos, Rotation=GunRotation)

    cursorTexture.drawCentered(mousePos)
    pygame.display.update()
