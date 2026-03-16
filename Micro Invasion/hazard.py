"""
hazard.py — Environmental hazards: Soap (instant kill) and Water (push force)
"""
import pygame
import math
import random
from settings import (
    SOAP_RADIUS_MIN, SOAP_RADIUS_MAX, SOAP_EXPAND_SPEED, SOAP_LIFETIME,
    WATER_WIDTH, WATER_LENGTH, WATER_PUSH_FORCE, WATER_LIFETIME,
    COLOR_SOAP, COLOR_WATER,
    ALCOHOL_ZONE_RADIUS, ALCOHOL_ZONE_LIFETIME,
    ALCOHOL_WAVE_SPEED, ALCOHOL_WAVE_HEALTH, ALCOHOL_WAVE_DAMAGE,
    ALCOHOL_WAVE_RADIUS, ALCOHOL_WAVE_COUNT,
    COLOR_ALCOHOL_ZONE, COLOR_ALCOHOL_WAVE, COLOR_ALCOHOL_GLOW,
    WORLD_WIDTH, WORLD_HEIGHT
)


class Soap(pygame.sprite.Sprite):
    """An expanding soap bubble zone — instantly kills any germ on contact."""

    def __init__(self, x, y):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.radius = SOAP_RADIUS_MIN
        self.max_radius = SOAP_RADIUS_MAX + random.randint(-20, 20)
        self.expand_speed = SOAP_EXPAND_SPEED
        self.lifetime = SOAP_LIFETIME
        self.max_lifetime = SOAP_LIFETIME
        self.alive = True

        # Visual
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.bubble_spots = []
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0.2, 0.7)
            size = random.uniform(3, 8)
            self.bubble_spots.append((angle, dist, size))

        self.image = pygame.Surface((int(self.max_radius * 2), int(self.max_radius * 2)),
                                   pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self):
        # Expand
        if self.radius < self.max_radius:
            self.radius += self.expand_speed

        self.lifetime -= 1
        self.pulse_timer += 0.05

        if self.lifetime <= 0:
            self.alive = False
            self.kill()

    def draw(self, surface, camera):
        if not self.alive:
            return

        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        r = int(self.radius)
        if r < 2:
            return

        # Fade out in last 30% of lifetime
        fade = min(1.0, self.lifetime / (self.max_lifetime * 0.3))
        base_alpha = int(80 * fade)

        # Main bubble
        bubble_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(bubble_surf, (240, 240, 255, base_alpha), (r, r), r)
        # Outline shimmer
        shimmer_alpha = int((40 + 20 * math.sin(self.pulse_timer * 3)) * fade)
        pygame.draw.circle(bubble_surf, (255, 255, 255, shimmer_alpha), (r, r), r, 2)
        # Inner ring
        inner_r = max(2, int(r * 0.6))
        pygame.draw.circle(bubble_surf, (250, 250, 255, int(30 * fade)), (r, r), inner_r, 1)

        surface.blit(bubble_surf, (sx - r, sy - r))

        # Small bubble spots
        for angle, dist, size in self.bubble_spots:
            bx = sx + math.cos(angle + self.pulse_timer * 0.5) * (r * dist)
            by = sy + math.sin(angle + self.pulse_timer * 0.5) * (r * dist)
            s = int(size * fade)
            if s > 0:
                spot_surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
                pygame.draw.circle(spot_surf, (255, 255, 255, int(50 * fade)), (s, s), s)
                surface.blit(spot_surf, (int(bx) - s, int(by) - s))

        # Warning icon "☠" in center
        if fade > 0.5:
            font = pygame.font.Font(None, max(16, int(20 * (r / self.max_radius))))
            icon = font.render("☠", True, (255, 255, 255))
            icon.set_alpha(int(120 * fade))
            icon_rect = icon.get_rect(center=(sx, sy))
            surface.blit(icon, icon_rect)


class Water(pygame.sprite.Sprite):
    """A directional water flow zone — pushes germs in the flow direction."""

    def __init__(self, x, y, direction=None):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)

        # Flow direction (normalized)
        if direction is None:
            angle = random.uniform(0, math.pi * 2)
            self.dir_x = math.cos(angle)
            self.dir_y = math.sin(angle)
        else:
            self.dir_x = direction[0]
            self.dir_y = direction[1]

        self.width = WATER_WIDTH
        self.length = WATER_LENGTH + random.randint(-50, 50)
        self.push_force = WATER_PUSH_FORCE
        self.lifetime = WATER_LIFETIME
        self.max_lifetime = WATER_LIFETIME
        self.alive = True

        # Calculate the rectangle corners for collision
        self.angle = math.atan2(self.dir_y, self.dir_x)
        self._update_corners()

        # Flow particles
        self.flow_particles = []
        for _ in range(15):
            self.flow_particles.append({
                "offset": random.uniform(0, 1),
                "lateral": random.uniform(-0.4, 0.4),
                "speed": random.uniform(0.005, 0.015),
                "size": random.randint(2, 4),
            })

        self.pulse_timer = 0

        self.image = pygame.Surface((int(self.length), int(self.width)), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def _update_corners(self):
        """Calculate rotated rectangle corners for collision test."""
        perp_x = -self.dir_y
        perp_y = self.dir_x
        half_w = self.width / 2
        half_l = self.length / 2

        self.corners = [
            (self.world_x - self.dir_x * half_l + perp_x * half_w,
             self.world_y - self.dir_y * half_l + perp_y * half_w),
            (self.world_x + self.dir_x * half_l + perp_x * half_w,
             self.world_y + self.dir_y * half_l + perp_y * half_w),
            (self.world_x + self.dir_x * half_l - perp_x * half_w,
             self.world_y + self.dir_y * half_l - perp_y * half_w),
            (self.world_x - self.dir_x * half_l - perp_x * half_w,
             self.world_y - self.dir_y * half_l - perp_y * half_w),
        ]

    def is_point_inside(self, px, py):
        """Check if a point is inside the water flow zone (simple AABB after transform)."""
        # Transform point into local space
        dx = px - self.world_x
        dy = py - self.world_y
        # Project onto flow direction and perpendicular
        along = dx * self.dir_x + dy * self.dir_y
        perp = dx * (-self.dir_y) + dy * self.dir_x
        return abs(along) < self.length / 2 and abs(perp) < self.width / 2

    def get_push_vector(self):
        """Get the push force vector."""
        return (self.dir_x * self.push_force, self.dir_y * self.push_force)

    def update(self):
        self.lifetime -= 1
        self.pulse_timer += 0.03

        # Flow particles move
        for fp in self.flow_particles:
            fp["offset"] += fp["speed"]
            if fp["offset"] > 1:
                fp["offset"] = 0
                fp["lateral"] = random.uniform(-0.4, 0.4)

        if self.lifetime <= 0:
            self.alive = False
            self.kill()

    def draw(self, surface, camera):
        if not self.alive:
            return

        fade = min(1.0, self.lifetime / (self.max_lifetime * 0.2))
        base_alpha = int(60 * fade)

        # Draw the rotated stream
        # Convert corners to screen space
        screen_corners = [camera.apply(c) for c in self.corners]

        # Stream body
        stream_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        try:
            pygame.draw.polygon(stream_surf, (80, 140, 220, base_alpha), screen_corners)
            pygame.draw.polygon(stream_surf, (100, 170, 240, base_alpha + 20), screen_corners, 2)
        except (ValueError, TypeError):
            pass
        surface.blit(stream_surf, (0, 0))

        # Flow particles inside the stream
        perp_x = -self.dir_y
        perp_y = self.dir_x
        half_l = self.length / 2

        for fp in self.flow_particles:
            # Position along stream
            along = -half_l + fp["offset"] * self.length
            px = self.world_x + self.dir_x * along + perp_x * (fp["lateral"] * self.width)
            py = self.world_y + self.dir_y * along + perp_y * (fp["lateral"] * self.width)

            spx, spy = camera.apply((px, py))
            spx, spy = int(spx), int(spy)

            dot_alpha = int(80 * fade * (0.5 + 0.5 * math.sin(self.pulse_timer * 5 + fp["offset"] * 10)))
            dot_surf = pygame.Surface((fp["size"] * 2, fp["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (150, 200, 255, dot_alpha),
                             (fp["size"], fp["size"]), fp["size"])
            surface.blit(dot_surf, (spx - fp["size"], spy - fp["size"]))

        # Direction arrow in center
        cx, cy = camera.apply((self.world_x, self.world_y))
        cx, cy = int(cx), int(cy)
        arrow_len = 15
        ax = cx + self.dir_x * arrow_len
        ay = cy + self.dir_y * arrow_len
        arrow_alpha = int(100 * fade)
        pygame.draw.line(surface, (180, 220, 255), (cx, cy), (int(ax), int(ay)), 2)


class AlcoholZone(pygame.sprite.Sprite):
    """A hazardous alcohol zone — spawns aggressive AlcoholWave entities
    that hunt and kill ALL germs (enemies AND the player)."""

    def __init__(self, x, y):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.radius = ALCOHOL_ZONE_RADIUS
        self.lifetime = ALCOHOL_ZONE_LIFETIME
        self.max_lifetime = ALCOHOL_ZONE_LIFETIME
        self.alive_flag = True

        # Visual
        self.pulse_timer = 0
        self.warning_font = pygame.font.Font(None, 28)

        # Track spawned waves
        self.waves_spawned = False

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def get_wave_spawn_positions(self):
        """Return positions where AlcoholWave entities should spawn."""
        positions = []
        for i in range(ALCOHOL_WAVE_COUNT):
            angle = (math.pi * 2 / ALCOHOL_WAVE_COUNT) * i + random.uniform(-0.3, 0.3)
            dist = random.uniform(30, self.radius * 0.6)
            wx = self.world_x + math.cos(angle) * dist
            wy = self.world_y + math.sin(angle) * dist
            positions.append((wx, wy))
        self.waves_spawned = True
        return positions

    def update(self):
        self.lifetime -= 1
        self.pulse_timer += 0.06

        if self.lifetime <= 0:
            self.alive_flag = False
            self.kill()

    def draw(self, surface, camera):
        if not self.alive_flag:
            return

        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)
        r = int(self.radius)

        fade = min(1.0, self.lifetime / (self.max_lifetime * 0.2))
        pulse = 0.9 + 0.1 * math.sin(self.pulse_timer * 3)

        # Zone glow ring (pulsing)
        zone_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        zone_alpha = int(50 * fade * pulse)
        pygame.draw.circle(zone_surf, (200, 180, 255, zone_alpha), (r, r), r)
        # Outer ring
        ring_alpha = int(100 * fade)
        pygame.draw.circle(zone_surf, (180, 140, 255, ring_alpha), (r, r), r, 3)
        # Inner warning ring
        inner_r = int(r * 0.6 * pulse)
        pygame.draw.circle(zone_surf, (220, 160, 255, int(40 * fade)), (r, r), inner_r, 2)
        surface.blit(zone_surf, (sx - r, sy - r))

        # Floating alcohol droplets in zone
        for i in range(8):
            angle = (math.pi * 2 / 8) * i + self.pulse_timer
            dist = r * 0.4 + r * 0.3 * math.sin(self.pulse_timer * 2 + i)
            dx = sx + math.cos(angle) * dist
            dy = sy + math.sin(angle) * dist
            dot_r = int(3 + 2 * math.sin(self.pulse_timer * 4 + i * 0.5))
            dot_alpha = int(80 * fade)
            dot_surf = pygame.Surface((dot_r * 2, dot_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (220, 180, 255, dot_alpha), (dot_r, dot_r), dot_r)
            surface.blit(dot_surf, (int(dx) - dot_r, int(dy) - dot_r))

        # Warning icon
        if fade > 0.3:
            icon = self.warning_font.render("🧪 ALCOHOL", True, (220, 180, 255))
            icon.set_alpha(int(180 * fade))
            icon_rect = icon.get_rect(center=(sx, sy - r - 15))
            surface.blit(icon, icon_rect)


class AlcoholWave(pygame.sprite.Sprite):
    """A powerful alcohol entity that aggressively hunts ALL germs.
    Kills everything it touches — player, clones, and enemies alike."""

    def __init__(self, x, y):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.radius = ALCOHOL_WAVE_RADIUS
        self.speed = ALCOHOL_WAVE_SPEED
        self.health = ALCOHOL_WAVE_HEALTH
        self.max_health = ALCOHOL_WAVE_HEALTH
        self.damage = ALCOHOL_WAVE_DAMAGE
        self.color = COLOR_ALCOHOL_WAVE

        # AI
        self.target_x = x
        self.target_y = y
        self.retarget_timer = 0

        # Visual
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.trail = []  # Trail positions for visual effect
        self.wobble_points = [random.uniform(-3, 3) for _ in range(10)]

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def find_nearest_target(self, targets):
        """Find the closest living target from a list of (x, y) positions."""
        best_dist = 9999
        best_pos = None
        for t in targets:
            tx = getattr(t, 'world_x', None)
            ty = getattr(t, 'world_y', None)
            if tx is None or ty is None:
                continue
            # Skip dead targets
            if hasattr(t, 'alive'):
                alive = t.alive() if callable(t.alive) else t.alive
                if not alive:
                    continue
            if hasattr(t, 'health') and t.health <= 0:
                continue
            dx = tx - self.world_x
            dy = ty - self.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < best_dist:
                best_dist = dist
                best_pos = (tx, ty)
        return best_pos

    def update(self, all_targets=None):
        """Chase the nearest target."""
        self.pulse_timer += 0.08

        # Retarget periodically
        self.retarget_timer -= 1
        if self.retarget_timer <= 0 and all_targets:
            self.retarget_timer = 12  # Re-evaluate every 12 frames
            pos = self.find_nearest_target(all_targets)
            if pos:
                self.target_x, self.target_y = pos

        # Move toward target
        dx = self.target_x - self.world_x
        dy = self.target_y - self.world_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 2:
            self.world_x += (dx / dist) * self.speed
            self.world_y += (dy / dist) * self.speed

        # Clamp to world
        self.world_x = max(self.radius, min(self.world_x, WORLD_WIDTH - self.radius))
        self.world_y = max(self.radius, min(self.world_y, WORLD_HEIGHT - self.radius))

        # Trail effect
        self.trail.append((self.world_x, self.world_y))
        if len(self.trail) > 12:
            self.trail.pop(0)

        # Wobble animation
        for i in range(len(self.wobble_points)):
            self.wobble_points[i] += random.uniform(-0.4, 0.4)
            self.wobble_points[i] = max(-5, min(5, self.wobble_points[i]))

        self.rect.center = (int(self.world_x), int(self.world_y))

    def take_damage(self, amount):
        """Alcohol is very resistant but can be damaged."""
        self.health -= amount * 0.3  # Takes only 30% damage
        if self.health <= 0:
            self.health = 0
            self.kill()
            return True
        return False

    def alive(self):
        return self.health > 0

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        pulse = 0.85 + 0.15 * math.sin(self.pulse_timer * 3)

        # Trail (fading purple)
        for i, (tx, ty) in enumerate(self.trail):
            tsx, tsy = camera.apply((tx, ty))
            t_alpha = int(40 * (i / len(self.trail)))
            t_r = max(1, int(self.radius * 0.4 * (i / len(self.trail))))
            trail_surf = pygame.Surface((t_r * 2, t_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (180, 140, 255, t_alpha), (t_r, t_r), t_r)
            surface.blit(trail_surf, (int(tsx) - t_r, int(tsy) - t_r))

        # Outer glow
        glow_r = int(self.radius * 2)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (220, 180, 255, 40), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

        # Body (wobbling polygon for organic feel)
        num_points = len(self.wobble_points)
        points = []
        for i in range(num_points):
            angle = (math.pi * 2 / num_points) * i + self.pulse_timer * 0.5
            wobble = self.wobble_points[i]
            r = (self.radius + wobble) * pulse
            px = sx + math.cos(angle) * r
            py = sy + math.sin(angle) * r
            points.append((px, py))

        if len(points) >= 3:
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, (220, 200, 255), points, 2)

        # Core (bright white-purple center)
        core_r = max(3, int(self.radius * 0.35 * pulse))
        pygame.draw.circle(surface, (240, 220, 255), (sx, sy), core_r)

        # Danger icon
        font = pygame.font.Font(None, 16)
        icon = font.render("☠", True, (255, 255, 255))
        icon_rect = icon.get_rect(center=(sx, sy - self.radius - 8))
        surface.blit(icon, icon_rect)
