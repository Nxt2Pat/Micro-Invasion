"""
item.py — Active items for the inventory system
Adrenaline Shot, Bio-Grenade, Repair Nanobots, Sensor Flare
"""
import pygame
import math
import random
from settings import ITEM_TYPES, POWERUP_RADIUS

class Item(pygame.sprite.Sprite):
    """A collectible item that can be picked up and stored in the inventory."""

    def __init__(self, x, y, item_type=None):
        super().__init__()
        # Random type if not specified
        if item_type is None:
            item_type = random.choice(list(ITEM_TYPES.keys()))

        self.item_type = item_type
        self.info = ITEM_TYPES[item_type]
        self.world_x = float(x)
        self.world_y = float(y)
        self.radius = POWERUP_RADIUS
        self.color = self.info["color"]

        # Animation
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.rotation = 0
        self.bob_y = 0
        self.lifetime = 1200  # Despawn after 50 seconds (1200 frames @ 24 FPS)

        # Sprite
        self.image = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

        # Pre-render icon (avoid per-frame font allocation)
        self._icon_font = pygame.font.SysFont("Arial", 16, bold=True)
        self._icon_surf = self._icon_font.render(self.info["icon"], True, (255, 255, 255))

    def update(self):
        self.pulse_timer += 0.05
        self.rotation += 3
        self.bob_y = math.sin(self.pulse_timer) * 6
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y + self.bob_y))
        sx, sy = int(sx), int(sy)

        pulse = 0.8 + 0.2 * math.sin(self.pulse_timer * 2)

        # Outer glow ring
        glow_r = int(self.radius * (1.6 + 0.3 * math.sin(self.pulse_timer)))
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 60), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

        # Core circle
        pygame.draw.circle(surface, self.color, (sx, sy), int(self.radius * pulse))
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), int(self.radius * pulse * 0.4))

        # Icon/Symbol (cached)
        icon_rect = self._icon_surf.get_rect(center=(sx, sy))
        surface.blit(self._icon_surf, icon_rect)
