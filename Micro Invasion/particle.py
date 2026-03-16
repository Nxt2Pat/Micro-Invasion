"""
particle.py — Particle effects system for visual juice
Handles damage particles, death bursts, food sparkles, combo text, etc.
"""
import pygame
import random
import math
from settings import (
    COLOR_PARTICLE_HIT, COLOR_PARTICLE_DEATH,
    COLOR_PARTICLE_DIVIDE, COLOR_PARTICLE_FOOD,
    COLOR_UI_COMBO
)


class Particle:
    """A single particle with position, velocity, lifetime, and shrinking size."""

    def __init__(self, x, y, color, vel_x=0, vel_y=0, size=4, lifetime=30, shrink=True):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = vel_x + random.uniform(-0.5, 0.5)
        self.vel_y = vel_y + random.uniform(-0.5, 0.5)
        self.size = size
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.shrink = shrink
        self.alive = True

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        # Slight drag
        self.vel_x *= 0.96
        self.vel_y *= 0.96
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface, camera):
        if not self.alive:
            return
        # Calculate current size
        if self.shrink:
            t = self.lifetime / self.max_lifetime
            current_size = max(1, int(self.size * t))
        else:
            current_size = self.size

        screen_pos = camera.apply((self.x, self.y))
        sx, sy = int(screen_pos[0]), int(screen_pos[1])

        # Draw directly — simpler, no SRCALPHA allocation per particle
        if current_size > 0:
            # Fade color toward black as lifetime decreases
            t = self.lifetime / self.max_lifetime
            faded = tuple(int(c * t) for c in self.color[:3])
            pygame.draw.circle(surface, faded, (sx, sy), current_size)


class FloatingText:
    """Floating text that drifts up and fades out (for combo counters, damage numbers)."""

    def __init__(self, x, y, text, color=COLOR_UI_COMBO, size=24, lifetime=45):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
        self.vel_y = -1.5  # Float upward
        self.font = pygame.font.Font(None, size)
        # Scale animation
        self.scale = 1.5  # Start big, shrink to normal

    def update(self):
        self.y += self.vel_y
        self.vel_y *= 0.97
        self.lifetime -= 1
        self.scale = max(1.0, self.scale - 0.03)
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface, camera):
        if not self.alive:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        screen_pos = camera.apply((self.x, self.y))

        # Render text
        current_size = max(12, int(self.size * self.scale))
        font = pygame.font.Font(None, current_size)
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        rect = text_surf.get_rect(center=(int(screen_pos[0]), int(screen_pos[1])))
        surface.blit(text_surf, rect)


class ParticleManager:
    """Manages all active particles and floating texts."""

    def __init__(self):
        self.particles = []
        self.texts = []

    def update(self):
        # Update particles
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()
        # Update floating texts
        self.texts = [t for t in self.texts if t.alive]
        for t in self.texts:
            t.update()

    def draw(self, surface, camera):
        for p in self.particles:
            p.draw(surface, camera)
        for t in self.texts:
            t.draw(surface, camera)

    # ─── Preset burst effects ───────────────────────────────────────

    def emit_hit(self, x, y, count=8):
        """Red particles on taking damage."""
        for _ in range(count):
            color = random.choice(COLOR_PARTICLE_HIT)
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append(Particle(
                x, y, color,
                vel_x=math.cos(angle) * speed,
                vel_y=math.sin(angle) * speed,
                size=random.randint(3, 6),
                lifetime=random.randint(15, 30)
            ))

    def emit_death(self, x, y, color=None, count=25):
        """Burst of particles when a germ dies."""
        colors = color if isinstance(color, list) else COLOR_PARTICLE_DEATH
        for _ in range(count):
            c = random.choice(colors) if isinstance(colors, list) else colors
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 10)
            self.particles.append(Particle(
                x, y, c,
                vel_x=math.cos(angle) * speed,
                vel_y=math.sin(angle) * speed,
                size=random.randint(3, 8),
                lifetime=random.randint(20, 45)
            ))

    def emit_divide(self, x, y, count=20):
        """Ring of green particles when player replicates."""
        for i in range(count):
            color = random.choice(COLOR_PARTICLE_DIVIDE)
            angle = (math.pi * 2 / count) * i
            speed = random.uniform(2, 5)
            self.particles.append(Particle(
                x, y, color,
                vel_x=math.cos(angle) * speed,
                vel_y=math.sin(angle) * speed,
                size=random.randint(3, 6),
                lifetime=random.randint(25, 40)
            ))

    def emit_food(self, x, y, count=5):
        """Sparkle on food pickup."""
        for _ in range(count):
            color = random.choice(COLOR_PARTICLE_FOOD)
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 2)
            self.particles.append(Particle(
                x, y, color,
                vel_x=math.cos(angle) * speed,
                vel_y=math.sin(angle) * speed,
                size=random.randint(2, 4),
                lifetime=random.randint(15, 25)
            ))

    def emit_xp(self, x, y, count=4):
        """Purple sparkle when XP orb is collected."""
        for _ in range(count):
            color = (200, 160, 255)
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 2)
            self.particles.append(Particle(
                x, y, color,
                vel_x=math.cos(angle) * speed,
                vel_y=math.sin(angle) * speed,
                size=random.randint(2, 4),
                lifetime=random.randint(10, 20)
            ))

    def emit_powerup(self, x, y, color, count=20):
        """Burst when picking up a power-up."""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 8)
            self.particles.append(Particle(
                x, y, color,
                vel_x=math.cos(angle) * speed,
                vel_y=math.sin(angle) * speed,
                size=random.randint(3, 7),
                lifetime=random.randint(20, 40)
            ))

    def add_combo_text(self, x, y, combo):
        """Show floating combo multiplier text."""
        self.texts.append(FloatingText(
            x, y - 30, f"×{combo}!",
            color=COLOR_UI_COMBO, size=28 + combo * 2,
            lifetime=50
        ))

    def add_damage_text(self, x, y, damage):
        """Show floating damage number."""
        self.texts.append(FloatingText(
            x + random.randint(-10, 10),
            y - 20,
            f"-{int(damage)}",
            color=(255, 100, 80), size=20,
            lifetime=30
        ))
