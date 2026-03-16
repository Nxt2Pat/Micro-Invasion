"""
main.py — Entry point for Micro Invasion
A retro-nostalgia germ survival game built with Pygame.
"""
import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from game import Game


def main():
    """Initialize Pygame and launch the game."""
    pygame.init()
    pygame.mixer.init()

    # Create the game window with SCALED so internal resolution stays 480p
    # but the window is large and resizable on modern displays.
    flags = pygame.SCALED | pygame.RESIZABLE
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption(TITLE)

    # Initialize procedural sounds
    import sound
    sound.audio = sound.SoundManager()
    sound.audio.master_vol = 0.5
    sound.audio.play("drone", loops=-1)  # Endless creepy drone

    # Hide the default cursor for a more immersive feel
    # pygame.mouse.set_visible(False)

    # Create and run the game
    game = Game(screen)
    game.run()

    # Clean shutdown
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
