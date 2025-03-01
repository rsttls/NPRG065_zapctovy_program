import pygame
import pygame.locals
import math
import time

from texture import texture
from projectileObject import *

# global variables
Width, Height = 640, 480  # window size
CameraX, CameraY = 0, 0  # camera position
MainLoopActive = 1  # if main loop is active

# init
pygame.init()
pygame.display.set_caption("IDK Game")
prevMark = time.time_ns() / 1000000
currMark = time.time_ns() / 1000000

Display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, vsync=1)
desktopWidth, desktopHeight = pygame.display.get_window_size()
pygame.mouse.set_visible(0)
cursorTexture = texture("./assets/cursor.bmp")
MainCharacterTexture = texture("./assets/ilum.bmp")
GunTexture = texture("./assets/gun.bmp")
BulletTexture = texture("./assets/bullet.bmp")
MainCharX = 0
MainCharY = 0
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
        elif Event.type == pygame.MOUSEBUTTONDOWN:
            projectileObject(
                GunPos,
                pygame.Vector2(mouseX - (GunPos[0] + 64), mouseY - (GunPos[1] + 64))
                / 1000,
            )
    keysPressed = pygame.key.get_pressed()
    if keysPressed[pygame.K_a]:
        MainCharX -= MainCharVel * deltaTime
    if keysPressed[pygame.K_d]:
        MainCharX += MainCharVel * deltaTime
    if keysPressed[pygame.K_w]:
        MainCharY -= MainCharVel * deltaTime
    if keysPressed[pygame.K_s]:
        MainCharY += MainCharVel * deltaTime
    (mouseX, mouseY) = pygame.mouse.get_pos()
    # update
    for projectile in projetileQueue:
        projectile.update(deltaTime)

    # gun pos/rot
    GunPos = (MainCharX + 20, MainCharY + 10)
    GunRotation = math.atan2(mouseY - (GunPos[1] + 64), mouseX - (GunPos[0] + 64))

    # draw
    Display.fill((50, 50, 50))

    for projectile in projetileQueue:
        BulletTexture.draw(projectile.Position[0] + 32, projectile.Position[1] + 32)

    MainCharacterTexture.draw(MainCharX, MainCharY, 2)
    if 1.5708 < GunRotation or GunRotation < -1.5708:
        GunTexture.draw(GunPos[0], GunPos[1], 2, math.degrees(GunRotation), flipY=1)
    else:
        GunTexture.draw(GunPos[0], GunPos[1], 2, math.degrees(GunRotation))

    cursorTexture.draw(mouseX - 32, mouseY - 32, 2)
    pygame.display.update()
