"""
player.py — Player germ and Clone sprites
The player is a new germ invading human skin with an amoeba-like appearance.
"""
import pygame
import math
import random
from settings import (
    PLAYER_SPEED, PLAYER_MAX_HEALTH, PLAYER_MAX_ENERGY,
    PLAYER_RADIUS, PLAYER_IFRAMES,
    PLAYER_AURA_RADIUS, PLAYER_AURA_DAMAGE,
    COLOR_PLAYER, COLOR_PLAYER_GLOW, COLOR_PLAYER_CORE,
    COLOR_CLONE, COLOR_CLONE_GLOW,
    CLONE_SPEED, CLONE_HEALTH, CLONE_RADIUS,
    CLONE_ORBIT_DIST, CLONE_ORBIT_SPEED,
    CLONE_ATTACK_RANGE, CLONE_ATTACK_DAMAGE,
    REPLICATE_COST, MAX_CLONES, INVENTORY_SLOTS,
    WORLD_WIDTH, WORLD_HEIGHT
)


class Player(pygame.sprite.Sprite):
    """The player-controlled germ."""

    def __init__(self, x, y):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.radius = PLAYER_RADIUS
        self.vel_x = 0.0
        self.vel_y = 0.0

        # Stats
        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.max_energy = PLAYER_MAX_ENERGY
        self.energy = 0.0
        self.base_speed = PLAYER_SPEED

        # Speed modifier from power-ups and mutations
        self.speed_mult = 1.0
        self.damage_mult = 1.0

        # Invincibility frames
        self.iframes = 0
        self.flash_timer = 0

        # Toxin aura
        self.aura_radius = PLAYER_AURA_RADIUS
        self.aura_damage = PLAYER_AURA_DAMAGE
        self.aura_mult = 1.0  # From mutations

        # Visual: amoeba wobble
        self.wobble_timer = 0
        self.wobble_points = [random.uniform(-3, 3) for _ in range(12)]
        self.pulse_timer = 0

        # Shield visual
        self.has_shield = False
        self.shield_hits = 0

        # Score tracking
        self.score = 0
        self.enemies_killed = 0
        self.food_collected = 0
        self.hit_flash_timer = 0
        
        # Dash mechanic
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_speed_mult = 3.0

        # Inventory
        self.inventory = [None] * INVENTORY_SLOTS
        
        # Burst Skill state
        self.burst_cooldown = 0
        self.pulse_visual_timer = 0

        # Sprite rect for collision
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.world_x), int(self.world_y)))

    def handle_input(self, keys):
        """Read WASD / arrow keys and set velocity."""
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        # Normalize direction
        if dx != 0 or dy != 0:
            mag = math.sqrt(dx*dx + dy*dy)
            self.facing_x = dx / mag
            self.facing_y = dy / mag
            
            # Normalize diagonal movement for velocity
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071
        else:
            # Default facing if no input
            if not hasattr(self, 'facing_x'):
                self.facing_x, self.facing_y = 1.0, 0.0

        speed = self.base_speed * self.speed_mult
        
        # Apply dash boost if active
        if self.is_dashing:
            speed *= self.dash_speed_mult

        # Smooth velocity with inertia
        self.vel_x += (dx * speed - self.vel_x) * 0.2
        self.vel_y += (dy * speed - self.vel_y) * 0.2

    def update(self):
        # Apply velocity
        self.world_x += self.vel_x
        self.world_y += self.vel_y

        # Clamp to world bounds
        self.world_x = max(self.radius, min(self.world_x, WORLD_WIDTH - self.radius))
        self.world_y = max(self.radius, min(self.world_y, WORLD_HEIGHT - self.radius))

        # Update rect
        self.rect.center = (int(self.world_x), int(self.world_y))

        # Dash handling
        if self.is_dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.dash_cooldown = 45 # Frames cooldown
        elif self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Invincibility frames
        if self.iframes > 0:
            self.iframes -= 1
            self.flash_timer += 1
            
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        if self.burst_cooldown > 0:
            self.burst_cooldown -= 1
            
        if self.pulse_visual_timer > 0:
            self.pulse_visual_timer -= 1

        # Animation
        self.wobble_timer += 0.05
        self.pulse_timer += 0.04
        for i in range(len(self.wobble_points)):
            self.wobble_points[i] += random.uniform(-0.3, 0.3)
            self.wobble_points[i] = max(-4, min(4, self.wobble_points[i]))

    def take_damage(self, amount):
        """Take damage with i-frame protection. Returns actual damage dealt."""
        if self.iframes > 0 or self.is_dashing:  # Immune while dashing
            return 0

        # Shield check
        if self.has_shield and self.shield_hits > 0:
            self.shield_hits -= 1
            if self.shield_hits <= 0:
                self.has_shield = False
            return 0

        self.health -= amount
        self.iframes = PLAYER_IFRAMES
        self.flash_timer = 0
        self.hit_flash_timer = 3  # Flash white on hit

        if self.health <= 0:
            self.health = 0
        return amount

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def add_energy(self, amount):
        self.energy = min(self.max_energy, self.energy + amount)

    def can_replicate(self, discount=1.0):
        cost = REPLICATE_COST * discount
        return self.energy >= cost

    def spend_energy(self, discount=1.0):
        cost = REPLICATE_COST * discount
        self.energy -= cost

    def dash(self):
        """Trigger a quick dash if cooldown is ready."""
        if self.dash_cooldown <= 0 and not self.is_dashing:
            self.is_dashing = True
            self.dash_timer = 8  # Frames of dash duration
            # Ensure we have a facing direction even if standing still initially
            if not hasattr(self, 'facing_x'):
                self.facing_x, self.facing_y = 1.0, 0.0
            return True
        return False

    @property
    def alive(self):
        return self.health > 0

    @property
    def pos(self):
        return (self.world_x, self.world_y)

    def draw(self, surface, camera):
        # Skip drawing every other frame during i-frames (flash)
        if self.iframes > 0 and self.flash_timer % 6 < 3:
            return

        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        # --- Toxin aura (ring outline, no filled SRCALPHA) ---
        aura_r = int(self.aura_radius * self.aura_mult)
        aura_brightness = 25 + int(15 * math.sin(self.pulse_timer * 2))
        pygame.draw.circle(surface, (aura_brightness, aura_brightness + 40, aura_brightness + 20),
                         (sx, sy), aura_r, 1)

        # --- Shield bubble ---
        if self.has_shield:
            shield_r = self.radius + 8
            shield_pulse = int(3 * math.sin(self.pulse_timer * 3))
            pygame.draw.circle(surface, (80, 160, 255), (sx, sy), shield_r + shield_pulse, 2)
            pygame.draw.circle(surface, (50, 100, 180), (sx, sy), shield_r + shield_pulse + 2, 1)

        # --- Outer glow (dimmed color circle) ---
        glow_r = int(self.radius * 1.6)
        dim_player = tuple(c // 4 for c in COLOR_PLAYER[:3])
        pygame.draw.circle(surface, dim_player, (sx, sy), glow_r)

        # --- Amoeba body (wobbling polygon) ---
        num_points = len(self.wobble_points)
        points = []
        pulse = 0.9 + 0.1 * math.sin(self.pulse_timer)
        for i in range(num_points):
            angle = (math.pi * 2 / num_points) * i + self.wobble_timer
            wobble = self.wobble_points[i]
            r = (self.radius + wobble) * pulse
            px = sx + math.cos(angle) * r
            py = sy + math.sin(angle) * r
            points.append((px, py))

        if len(points) >= 3:
            if self.hit_flash_timer > 0:
                pygame.draw.polygon(surface, (255, 255, 255), points)
            else:
                pygame.draw.polygon(surface, COLOR_PLAYER, points)
                pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in COLOR_PLAYER[:3]),
                                  points, 2)

        # --- Nucleus ---
        nucleus_r = max(3, int(self.radius * 0.4 * pulse))
        pygame.draw.circle(surface, COLOR_PLAYER_CORE, (sx, sy), nucleus_r)

    def draw_rage_aura(self, surface, camera):
        """Extra visual when Rage power-up is active."""
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)
        rage_r = int(self.radius * 1.8)
        pygame.draw.circle(surface, (80, 15, 15), (sx, sy), rage_r)
        pygame.draw.circle(surface, (180, 40, 40), (sx, sy), rage_r, 2)

    def add_to_inventory(self, item_type):
        """Add item to first empty slot. Returns True if successful."""
        for i in range(len(self.inventory)):
            if self.inventory[i] is None:
                self.inventory[i] = item_type
                return True
        return False

    def use_item(self, index):
        """Return the item type if slot is used, then clear it."""
        if 0 <= index < len(self.inventory) and self.inventory[index]:
            item = self.inventory[index]
            self.inventory[index] = None
            return item
        return None

    def trigger_burst(self, cooldown_frames):
        """Handle cooldown and visual for the burst attack."""
        if self.burst_cooldown <= 0:
            self.burst_cooldown = cooldown_frames
            self.pulse_visual_timer = 15 # Visual duration
            return True
        return False


class Clone(pygame.sprite.Sprite):
    """A clone germ that orbits and fights alongside the player."""

    def __init__(self, player, orbit_index=0):
        super().__init__()
        self.player = player
        self.orbit_index = orbit_index
        self.orbit_angle = (math.pi * 2 / MAX_CLONES) * orbit_index
        self.orbit_dist = CLONE_ORBIT_DIST
        self.radius = CLONE_RADIUS
        self.health = CLONE_HEALTH
        self.max_health = CLONE_HEALTH
        self.speed = CLONE_SPEED
        self.attack_range = CLONE_ATTACK_RANGE
        self.attack_damage = CLONE_ATTACK_DAMAGE

        # Position
        self.world_x = player.world_x
        self.world_y = player.world_y

        # Target position (orbit around player)
        self.target_x = self.world_x
        self.target_y = self.world_y

        # Attacking state
        self.attack_target = None
        self.attack_cooldown = 0

        # Visual
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.wobble_points = [random.uniform(-2, 2) for _ in range(8)]
        self.hit_flash_timer = 0

        # Sprite
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def update(self, enemies=None):
        # Update orbit angle
        self.orbit_angle += CLONE_ORBIT_SPEED

        # Target position (ideal orbit around player)
        self.target_x = self.player.world_x + math.cos(self.orbit_angle) * self.orbit_dist
        self.target_y = self.player.world_y + math.sin(self.orbit_angle) * self.orbit_dist

        # Decaying cooldowns
        self.attack_cooldown = max(0, self.attack_cooldown - 1)

        # AI Behavior: Hunt vs Orbit
        found_hunt_target = False
        if enemies:
            # Clones now have a larger independent hunting range
            HUNT_RANGE = 250
            closest = None
            closest_dist = HUNT_RANGE
            for enemy in enemies:
                dx = enemy.world_x - self.world_x
                dy = enemy.world_y - self.world_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < closest_dist:
                    closest = enemy
                    closest_dist = dist

            if closest:
                found_hunt_target = True
                self.attack_target = closest
                # Move toward enemy to attack
                dx = closest.world_x - self.world_x
                dy = closest.world_y - self.world_y
                dist = max(1, math.sqrt(dx * dx + dy * dy))
                
                # Hunting speed
                self.world_x += (dx / dist) * self.speed * 1.2
                self.world_y += (dy / dist) * self.speed * 1.2

                # Deal damage on contact
                if dist < self.radius + closest.radius and self.attack_cooldown <= 0:
                    closest.take_damage(self.attack_damage * self.player.damage_mult)
                    self.attack_cooldown = 12 # Strike faster than before
            else:
                self.attack_target = None

        if not found_hunt_target:
            # Return to orbit position / Stay in orbit if no enemies to hunt
            dx = self.target_x - self.world_x
            dy = self.target_y - self.world_y
            dist = max(1, math.sqrt(dx * dx + dy * dy))
            
            # Smoothly transition back to player
            move_speed = min(self.speed, dist * 0.15)
            self.world_x += (dx / dist) * move_speed
            self.world_y += (dy / dist) * move_speed

        # Clamp to world
        self.world_x = max(self.radius, min(self.world_x, WORLD_WIDTH - self.radius))
        self.world_y = max(self.radius, min(self.world_y, WORLD_HEIGHT - self.radius))

        self.rect.center = (int(self.world_x), int(self.world_y))
        self.pulse_timer += 0.06
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
        # Wobble
        for i in range(len(self.wobble_points)):
            self.wobble_points[i] += random.uniform(-0.2, 0.2)
            self.wobble_points[i] = max(-3, min(3, self.wobble_points[i]))

    def take_damage(self, amount):
        self.health -= amount
        self.hit_flash_timer = 3
        if self.health <= 0:
            self.kill()
            return True
        return False

    @property
    def alive(self):
        return self.health > 0

    @property
    def pos(self):
        return (self.world_x, self.world_y)

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        # Dim glow circle
        glow_r = int(self.radius * 1.5)
        dim_clone = tuple(c // 5 for c in COLOR_CLONE[:3])
        pygame.draw.circle(surface, dim_clone, (sx, sy), glow_r)

        # Body (smaller amoeba)
        num_points = len(self.wobble_points)
        points = []
        pulse = 0.9 + 0.1 * math.sin(self.pulse_timer)
        for i in range(num_points):
            angle = (math.pi * 2 / num_points) * i
            wobble = self.wobble_points[i]
            r = (self.radius + wobble) * pulse
            px = sx + math.cos(angle) * r
            py = sy + math.sin(angle) * r
            points.append((px, py))

        if len(points) >= 3:
            if self.hit_flash_timer > 0:
                pygame.draw.polygon(surface, (255, 255, 255), points)
            else:
                pygame.draw.polygon(surface, COLOR_CLONE, points)
                pygame.draw.polygon(surface, tuple(max(0, c - 20) for c in COLOR_CLONE[:3]),
                                  points, 1)

        # Nucleus
        nucleus_r = max(2, int(self.radius * 0.35 * pulse))
        bright = tuple(min(255, c + 60) for c in COLOR_CLONE[:3])
        pygame.draw.circle(surface, bright, (sx, sy), nucleus_r)

        # Health bar (always visible above clone)
        bar_w = self.radius * 2
        bar_h = 3
        bar_x = sx - bar_w // 2
        bar_y = sy - self.radius - 8
        pygame.draw.rect(surface, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * (self.health / self.max_health))
        hp_pct = self.health / self.max_health
        if hp_pct > 0.5:
            bar_color = (100, 220, 140)  # Green
        elif hp_pct > 0.25:
            bar_color = (220, 180, 60)   # Yellow
        else:
            bar_color = (220, 60, 60)    # Red
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h))


class AcidProjectile(pygame.sprite.Sprite):
    """Acid spit projectile fired by the player."""

    def __init__(self, x, y, direction_x, direction_y, piercing=False):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.speed = 6.0
        self.damage = 15
        self.radius = 5
        self.lifetime = 120  # frames
        self.piercing = piercing

        # Normalize direction
        mag = max(0.01, math.sqrt(direction_x ** 2 + direction_y ** 2))
        self.vel_x = (direction_x / mag) * self.speed
        self.vel_y = (direction_y / mag) * self.speed

        self.pulse_timer = 0

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self):
        self.world_x += self.vel_x
        self.world_y += self.vel_y
        self.rect.center = (int(self.world_x), int(self.world_y))
        self.lifetime -= 1
        self.pulse_timer += 0.15

        # Kill if out of world or expired
        if (self.lifetime <= 0 or
            self.world_x < 0 or self.world_x > WORLD_WIDTH or
            self.world_y < 0 or self.world_y > WORLD_HEIGHT):
            self.kill()

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        # Dim glow
        glow_r = int(self.radius * 2)
        pygame.draw.circle(surface, (45, 65, 15), (sx, sy), glow_r)

        # Core
        pulse = 0.8 + 0.2 * math.sin(self.pulse_timer)
        r = max(2, int(self.radius * pulse))
        pygame.draw.circle(surface, (180, 255, 60), (sx, sy), r)
        pygame.draw.circle(surface, (220, 255, 120), (sx, sy), max(1, r // 2))

class EnemyProjectile(pygame.sprite.Sprite):
    """Projectile fired by enemies (e.g., Spitter) that hurts the player."""

    def __init__(self, x, y, direction_x, direction_y, damage=1.0):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.speed = 4.5
        self.damage = damage
        self.radius = 4
        self.lifetime = 150  # frames

        # Normalize direction
        mag = max(0.01, math.sqrt(direction_x ** 2 + direction_y ** 2))
        self.vel_x = (direction_x / mag) * self.speed
        self.vel_y = (direction_y / mag) * self.speed

        self.pulse_timer = 0
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self):
        self.world_x += self.vel_x
        self.world_y += self.vel_y
        self.rect.center = (int(self.world_x), int(self.world_y))
        self.lifetime -= 1
        self.pulse_timer += 0.15

        if (self.lifetime <= 0 or
            self.world_x < 0 or self.world_x > WORLD_WIDTH or
            self.world_y < 0 or self.world_y > WORLD_HEIGHT):
            self.kill()

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        # Glow
        glow_r = int(self.radius * 2)
        pygame.draw.circle(surface, (60, 20, 100), (sx, sy), glow_r)

        # Core (Toxic Purple)
        pulse = 0.8 + 0.2 * math.sin(self.pulse_timer)
        r = max(2, int(self.radius * pulse))
        pygame.draw.circle(surface, (160, 50, 220), (sx, sy), r)
        pygame.draw.circle(surface, (200, 150, 255), (sx, sy), max(1, r // 2))
