import pygame
import pygame.locals
from texture import texture
import time



# global variables
Width, Height = 640, 480  # window size
CameraX, CameraY = 0, 0  # camera position
MainLoopActive = 1  # if main loop is active


# init
pygame.init()
pygame.display.set_caption("IDK Game")

Display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, vsync=1)
desktopWidth, desktopHeight = pygame.display.get_window_size()

MainCharacterTexture = texture("./assets/ilum.bmp")
MainCharX = 100
MainCharY = 100
MainCharRot = 0

while MainLoopActive:
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
                        (desktopWidth, desktopHeight),
                        pygame.FULLSCREEN,
                        vsync=1,
                    )
                    Width, Height = desktopWidth, desktopHeight

    keysPressed = pygame.key.get_pressed()
    if keysPressed[pygame.K_a]:
        MainCharX -= 1
    if keysPressed[pygame.K_d]:
        MainCharX += 1
    if keysPressed[pygame.K_w]:
        MainCharY -= 1
    if keysPressed[pygame.K_s]:
        MainCharY += 1
    if keysPressed[pygame.K_q]:
        MainCharRot -= 1
    if keysPressed[pygame.K_e]:
        MainCharRot += 1
    # update

    # draw
    Display.fill((50, 50, 50))

    MainCharacterTexture.draw(
        MainCharX, MainCharY, scale=2, rotation=MainCharRot, flipX=1
    )

    pygame.display.update()
