"""
food.py — Nutrient pickups and XP orbs
Food grants energy/health; XP orbs drop from enemies and contribute to evolution.
"""
import pygame
import random
import math
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT,
    FOOD_RADIUS, FOOD_ENERGY_AMOUNT, FOOD_HEALTH_AMOUNT,
    FOOD_HEALTH_CHANCE,
    COLOR_FOOD_ENERGY, COLOR_FOOD_HEALTH, COLOR_XP_ORB,
    XP_ORB_RADIUS, XP_ORB_MAGNET_RANGE, XP_ORB_SPEED
)


class Food(pygame.sprite.Sprite):
    """A nutrient pickup that grants energy or health."""

    def __init__(self, x=None, y=None, food_type=None):
        super().__init__()
        # Random position if not specified
        self.world_x = x if x is not None else random.uniform(50, WORLD_WIDTH - 50)
        self.world_y = y if y is not None else random.uniform(50, WORLD_HEIGHT - 50)

        # Determine type: energy or health
        if food_type is None:
            self.food_type = "health" if random.random() < FOOD_HEALTH_CHANCE else "energy"
        else:
            self.food_type = food_type

        self.radius = FOOD_RADIUS
        self.color = COLOR_FOOD_HEALTH if self.food_type == "health" else COLOR_FOOD_ENERGY
        self.amount = FOOD_HEALTH_AMOUNT if self.food_type == "health" else FOOD_ENERGY_AMOUNT

        # Animation
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.bob_offset = 0

        # Sprite setup
        self.image = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.world_x), int(self.world_y)))

    def update(self):
        # Gentle pulsing animation
        self.pulse_timer += 0.08
        self.bob_offset = math.sin(self.pulse_timer) * 2

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y + self.bob_offset))
        sx, sy = int(sx), int(sy)

        pulse = 0.7 + 0.3 * math.sin(self.pulse_timer)

        # Outer ring glow (direct draw, no SRCALPHA surface)
        glow_r = int(self.radius * 2 * pulse)
        dim_color = tuple(c // 4 for c in self.color[:3])
        pygame.draw.circle(surface, dim_color, (sx, sy), glow_r)

        # Core dot
        current_radius = max(2, int(self.radius * pulse))
        pygame.draw.circle(surface, self.color, (sx, sy), current_radius)

        # Inner bright spot
        inner_r = max(1, current_radius // 2)
        bright = tuple(min(255, c + 80) for c in self.color[:3])
        pygame.draw.circle(surface, bright, (sx - 1, sy - 1), inner_r)


class XPOrb(pygame.sprite.Sprite):
    """XP orb dropped by enemies — magnetically attracted to player."""

    def __init__(self, x, y, xp_amount=10):
        super().__init__()
        self.world_x = x
        self.world_y = y
        self.xp_amount = xp_amount
        self.radius = XP_ORB_RADIUS
        self.color = COLOR_XP_ORB

        # Physics
        self.vel_x = random.uniform(-3, 3)
        self.vel_y = random.uniform(-3, 3)
        self.friction = 0.92

        # Animation
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.alive = True

        # Sprite setup
        self.image = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.world_x), int(self.world_y)))

    def update(self, player_pos=None, magnet_range=None):
        # Apply initial burst velocity with friction
        self.vel_x *= self.friction
        self.vel_y *= self.friction

        # Magnetic attraction to player
        if player_pos:
            attract_range = magnet_range or XP_ORB_MAGNET_RANGE
            dx = player_pos[0] - self.world_x
            dy = player_pos[1] - self.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < attract_range and dist > 1:
                # Attraction strength increases as orb gets closer
                strength = (1 - dist / attract_range) * XP_ORB_SPEED
                self.vel_x += (dx / dist) * strength
                self.vel_y += (dy / dist) * strength

        self.world_x += self.vel_x
        self.world_y += self.vel_y

        # Update rect
        self.rect.center = (int(self.world_x), int(self.world_y))

        # Pulse animation
        self.pulse_timer += 0.1

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        pulse = 0.6 + 0.4 * math.sin(self.pulse_timer)

        # Outer glow ring (direct)
        glow_r = int(self.radius * 2.5 * pulse)
        dim_color = tuple(c // 5 for c in self.color[:3])
        pygame.draw.circle(surface, dim_color, (sx, sy), glow_r)

        # Core
        cr = max(2, int(self.radius * pulse))
        pygame.draw.circle(surface, self.color, (sx, sy), cr)
