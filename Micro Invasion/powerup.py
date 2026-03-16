"""
powerup.py — Temporary power-up drops
Speed Boost, Rage Mode, Regeneration, Shield Bubble, Magnet
"""
import pygame
import random
import math
from settings import (
    POWERUP_RADIUS,
    POWERUP_SPEED_DURATION, POWERUP_SPEED_MULT,
    POWERUP_RAGE_DURATION, POWERUP_RAGE_MULT,
    POWERUP_REGEN_DURATION, POWERUP_REGEN_RATE,
    POWERUP_SHIELD_HITS,
    POWERUP_MAGNET_DURATION, POWERUP_MAGNET_RANGE,
    COLOR_POWERUP_SPEED, COLOR_POWERUP_RAGE,
    COLOR_POWERUP_REGEN, COLOR_POWERUP_SHIELD, COLOR_POWERUP_MAGNET
)

# Power-up type definitions
POWERUP_TYPES = {
    "speed": {
        "name": "Speed Boost",
        "color": COLOR_POWERUP_SPEED,
        "icon": "»",
        "duration": POWERUP_SPEED_DURATION,
    },
    "rage": {
        "name": "Rage Mode",
        "color": COLOR_POWERUP_RAGE,
        "icon": "!",
        "duration": POWERUP_RAGE_DURATION,
    },
    "regen": {
        "name": "Regeneration",
        "color": COLOR_POWERUP_REGEN,
        "icon": "+",
        "duration": POWERUP_REGEN_DURATION,
    },
    "shield": {
        "name": "Shield Bubble",
        "color": COLOR_POWERUP_SHIELD,
        "icon": "O",
        "duration": 999,  # Until hits depleted
    },
    "magnet": {
        "name": "Magnet",
        "color": COLOR_POWERUP_MAGNET,
        "icon": "@",
        "duration": POWERUP_MAGNET_DURATION,
    },
    "glitch": {
        "name": "V.O.I.D. Glitch",
        "color": (255, 0, 255),
        "icon": "?",
        "duration": 12.0,
    },
}


class PowerUp(pygame.sprite.Sprite):
    """A collectible power-up item that appears on the map."""

    def __init__(self, x, y, powerup_type=None):
        super().__init__()
        # Random type if not specified
        if powerup_type is None:
            powerup_type = random.choice(list(POWERUP_TYPES.keys()))

        self.powerup_type = powerup_type
        self.info = POWERUP_TYPES[powerup_type]
        self.world_x = x
        self.world_y = y
        self.radius = POWERUP_RADIUS
        self.color = self.info["color"]

        # Animation
        self.pulse_timer = 0
        self.rotation = 0
        self.bob_y = 0
        self.lifetime = 600  # Despawn after 10 seconds (600 frames)

        # Sprite
        self.image = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self):
        self.pulse_timer += 0.06
        self.rotation += 2
        self.bob_y = math.sin(self.pulse_timer) * 4
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y + self.bob_y))
        sx, sy = int(sx), int(sy)

        pulse = 0.7 + 0.3 * math.sin(self.pulse_timer * 2)

        # Halo ring (no SRCALPHA)
        halo_r = int(self.radius * 2 * pulse)
        dim_color = tuple(c // 4 for c in self.color[:3])
        pygame.draw.circle(surface, dim_color, (sx, sy), halo_r)
        pygame.draw.circle(surface, self.color, (sx, sy), halo_r, 1)

        # Core shape (hexagon-ish)
        core_r = int(self.radius * pulse)
        points = []
        for i in range(6):
            angle = math.radians(self.rotation + i * 60)
            px = sx + math.cos(angle) * core_r
            py = sy + math.sin(angle) * core_r
            points.append((px, py))
        if len(points) >= 3:
            pygame.draw.polygon(surface, self.color, points)
            # Bright inner
            inner_points = []
            for i in range(6):
                angle = math.radians(self.rotation + i * 60)
                px = sx + math.cos(angle) * (core_r * 0.5)
                py = sy + math.sin(angle) * (core_r * 0.5)
                inner_points.append((px, py))
            bright = tuple(min(255, c + 60) for c in self.color[:3])
            pygame.draw.polygon(surface, bright, inner_points)

        # Blinking effect when about to despawn
        if self.lifetime < 120 and self.lifetime % 10 < 5:
            return  # Blink effect


class ActivePowerUp:
    """Tracks an active power-up buff on the player."""

    def __init__(self, powerup_type):
        self.powerup_type = powerup_type
        self.info = POWERUP_TYPES[powerup_type]
        self.color = self.info["color"]
        self.name = self.info["name"]
        self.max_duration = self.info["duration"]
        self.time_left = self.max_duration

        # Shield-specific
        self.shield_hits = POWERUP_SHIELD_HITS if powerup_type == "shield" else 0

    def update(self, dt):
        """Update timer. Returns False when expired."""
        if self.powerup_type == "shield":
            return self.shield_hits > 0
        self.time_left -= dt
        return self.time_left > 0

    def absorb_hit(self):
        """For shield: absorb a hit. Returns True if shield still active."""
        if self.powerup_type == "shield":
            self.shield_hits -= 1
            return self.shield_hits > 0
        return True

    @property
    def progress(self):
        """Remaining duration as 0-1 fraction."""
        if self.powerup_type == "shield":
            return self.shield_hits / POWERUP_SHIELD_HITS
        return max(0, self.time_left / self.max_duration)

    def get_speed_mult(self):
        if self.powerup_type == "glitch": return 2.0
        return POWERUP_SPEED_MULT if self.powerup_type == "speed" else 1.0

    def get_damage_mult(self):
        if self.powerup_type == "glitch": return 3.0
        return POWERUP_RAGE_MULT if self.powerup_type == "rage" else 1.0

    def get_regen_rate(self):
        return POWERUP_REGEN_RATE if self.powerup_type == "regen" else 0.0

    def get_magnet_range(self):
        if self.powerup_type == "glitch": return 800
        return POWERUP_MAGNET_RANGE if self.powerup_type == "magnet" else 0
