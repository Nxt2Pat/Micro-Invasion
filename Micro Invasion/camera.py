"""
camera.py — Smooth-follow camera with screen shake support
"""
import pygame
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT


class Camera:
    """Follows the player with smooth lerp and optional screen shake."""

    def __init__(self):
        self.offset = pygame.math.Vector2(0, 0)
        self.target = pygame.math.Vector2(0, 0)
        self.smoothing = 0.08  # Lower = smoother / slower follow

        # Screen shake
        self.shake_amount = 0
        self.shake_decay = 0.85
        self.shake_offset = pygame.math.Vector2(0, 0)

    def update(self, target_pos):
        """Smoothly move camera toward the target (player position)."""
        # Target: center the player on screen
        self.target.x = target_pos[0] - SCREEN_WIDTH // 2
        self.target.y = target_pos[1] - SCREEN_HEIGHT // 2

        # Lerp toward target
        self.offset.x += (self.target.x - self.offset.x) * self.smoothing
        self.offset.y += (self.target.y - self.offset.y) * self.smoothing

        # Clamp to world bounds
        self.offset.x = max(0, min(self.offset.x, WORLD_WIDTH - SCREEN_WIDTH))
        self.offset.y = max(0, min(self.offset.y, WORLD_HEIGHT - SCREEN_HEIGHT))

        # Update screen shake
        if self.shake_amount > 0.5:
            self.shake_offset.x = random.uniform(-self.shake_amount, self.shake_amount)
            self.shake_offset.y = random.uniform(-self.shake_amount, self.shake_amount)
            self.shake_amount *= self.shake_decay
        else:
            self.shake_amount = 0
            self.shake_offset.x = 0
            self.shake_offset.y = 0

    def apply(self, world_pos):
        """Convert world coordinates to screen coordinates."""
        return (
            world_pos[0] - self.offset.x + self.shake_offset.x,
            world_pos[1] - self.offset.y + self.shake_offset.y
        )

    def apply_rect(self, rect):
        """Apply camera offset to a pygame.Rect, return new Rect."""
        return pygame.Rect(
            rect.x - self.offset.x + self.shake_offset.x,
            rect.y - self.offset.y + self.shake_offset.y,
            rect.width,
            rect.height
        )

    def shake(self, intensity=10):
        """Trigger a screen shake effect."""
        self.shake_amount = max(self.shake_amount, intensity)

    def world_to_screen(self, pos):
        """Alias for apply — world pos to screen pos."""
        return self.apply(pos)

    def screen_to_world(self, screen_pos):
        """Convert screen coordinates back to world coordinates."""
        return (
            screen_pos[0] + self.offset.x,
            screen_pos[1] + self.offset.y
        )
