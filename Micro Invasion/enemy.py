"""
enemy.py — Enemy germs, White Blood Cells, and Boss
"""
import pygame
import math
import random
from settings import (
    ENEMY_SPEED, ENEMY_HEALTH, ENEMY_RADIUS, ENEMY_DAMAGE,
    ENEMY_DETECTION, ENEMY_WANDER_TIME, ENEMY_XP_DROP,
    WBC_SPEED, WBC_HEALTH, WBC_RADIUS, WBC_DAMAGE, WBC_XP_DROP,
    BOSS_HEALTH, BOSS_RADIUS, BOSS_SPEED, BOSS_DAMAGE, BOSS_XP_DROP,
    HEAVY_SPEED, HEAVY_HEALTH, HEAVY_RADIUS, HEAVY_DAMAGE, HEAVY_XP_DROP,
    CHARGER_SPEED, CHARGER_DASH_SPEED, CHARGER_HEALTH, CHARGER_RADIUS, CHARGER_DAMAGE, CHARGER_XP_DROP,
    SPITTER_SPEED, SPITTER_HEALTH, SPITTER_RADIUS, SPITTER_DAMAGE, SPITTER_XP_DROP, SPITTER_RANGE,
    EXPLODER_SPEED, EXPLODER_HEALTH, EXPLODER_RADIUS, EXPLODER_DAMAGE, EXPLODER_XP_DROP, EXPLODER_DETECTION, EXPLODER_FUSE_TIME, EXPLODER_AOE_RADIUS,
    ELITE_WBC_SPEED, ELITE_WBC_HEALTH, ELITE_WBC_RADIUS, ELITE_WBC_DAMAGE, ELITE_WBC_XP_DROP, ELITE_WBC_DASH_SPEED, ELITE_WBC_DASH_COOLDOWN,
    HEAVY_SLOW_RADIUS, HEAVY_SLOW_FACTOR, HEAVY_PULL_FORCE,
    COLOR_ENEMY_1, COLOR_ENEMY_2, COLOR_ENEMY_3,
    COLOR_WBC, COLOR_WBC_GLOW,
    COLOR_BOSS, COLOR_BOSS_GLOW,
    WORLD_WIDTH, WORLD_HEIGHT
)

ENEMY_COLORS = [COLOR_ENEMY_1, COLOR_ENEMY_2, COLOR_ENEMY_3]


class EnemyGerm(pygame.sprite.Sprite):
    """A rival germ that wanders and attacks the player on sight."""

    def __init__(self, x, y):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.radius = ENEMY_RADIUS + random.randint(-2, 3)
        self.speed = ENEMY_SPEED + random.uniform(-0.3, 0.3)
        self.health = ENEMY_HEALTH + random.randint(-5, 5)
        self.max_health = self.health
        self.damage = ENEMY_DAMAGE
        self.xp_drop = ENEMY_XP_DROP

        # AI state
        self.state = "wander"  # wander / chase
        self.wander_timer = random.randint(30, ENEMY_WANDER_TIME)
        self.wander_dir_x = random.uniform(-1, 1)
        self.wander_dir_y = random.uniform(-1, 1)
        self.detection_range = ENEMY_DETECTION

        # Visual
        self.color = random.choice(ENEMY_COLORS)
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.wobble_points = [random.uniform(-2, 2) for _ in range(8)]
        self.hit_flash_timer = 0

        # Slow effect (from toxic aura)
        self.slow_timer = 0
        self.slow_mult = 1.0

        # Sprite
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self, player_pos=None):
        speed = self.speed * self.slow_mult

        # Slow effect decay
        if self.slow_timer > 0:
            self.slow_timer -= 1
        else:
            self.slow_mult = 1.0

        # Check if player is in detection range
        if player_pos:
            dx = player_pos[0] - self.world_x
            dy = player_pos[1] - self.world_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < self.detection_range:
                self.state = "chase"
                if dist > 1:
                    self.world_x += (dx / dist) * speed
                    self.world_y += (dy / dist) * speed
            else:
                self.state = "wander"

        if self.state == "wander":
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.wander_dir_x = random.uniform(-1, 1)
                self.wander_dir_y = random.uniform(-1, 1)
                self.wander_timer = random.randint(60, ENEMY_WANDER_TIME)

            self.world_x += self.wander_dir_x * speed * 0.5
            self.world_y += self.wander_dir_y * speed * 0.5

        # Clamp to world
        self.world_x = max(self.radius, min(self.world_x, WORLD_WIDTH - self.radius))
        self.world_y = max(self.radius, min(self.world_y, WORLD_HEIGHT - self.radius))

        self.rect.center = (int(self.world_x), int(self.world_y))

        # Animation
        self.pulse_timer += 0.05
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
        for i in range(len(self.wobble_points)):
            self.wobble_points[i] += random.uniform(-0.2, 0.2)
            self.wobble_points[i] = max(-3, min(3, self.wobble_points[i]))

    def take_damage(self, amount):
        self.health -= amount
        self.hit_flash_timer = 3  # Flash white for 3 frames
        if self.health <= 0:
            self.kill()
            return True
        return False

    def apply_slow(self, duration=60, factor=0.5):
        self.slow_timer = duration
        self.slow_mult = factor

    @property
    def pos(self):
        return (self.world_x, self.world_y)

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        # Dim glow circle
        glow_r = int(self.radius * 1.4)
        dim_color = tuple(c // 5 for c in self.color[:3])
        pygame.draw.circle(surface, dim_color, (sx, sy), glow_r)

        # Body
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
                pygame.draw.polygon(surface, self.color, points)
                darker = tuple(max(0, c - 40) for c in self.color[:3])
                pygame.draw.polygon(surface, darker, points, 2)

        # Nucleus
        nucleus_r = max(2, int(self.radius * 0.3 * pulse))
        darker_core = tuple(max(0, c - 60) for c in self.color[:3])
        pygame.draw.circle(surface, darker_core, (sx, sy), nucleus_r)

        # Health bar
        if self.health < self.max_health:
            bar_w = self.radius * 2
            bar_h = 3
            bar_x = sx - bar_w // 2
            bar_y = sy - self.radius - 8
            pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, bar_h))
            fill = int(bar_w * (self.health / self.max_health))
            pygame.draw.rect(surface, (220, 60, 60), (bar_x, bar_y, fill, bar_h))


class WhiteBloodCell(pygame.sprite.Sprite):
    """Immune system defender — chases and destroys all germs."""

    def __init__(self, x, y):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.radius = WBC_RADIUS
        self.speed = WBC_SPEED
        self.health = WBC_HEALTH
        self.max_health = WBC_HEALTH
        self.damage = WBC_DAMAGE
        self.xp_drop = WBC_XP_DROP

        # Visual
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.tentacle_angles = [random.uniform(0, math.pi * 2) for _ in range(5)]
        self.tentacle_lengths = [random.uniform(8, 15) for _ in range(5)]
        self.hit_flash_timer = 0

        # Slow effect
        self.slow_timer = 0
        self.slow_mult = 1.0

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self, targets=None):
        speed = self.speed * self.slow_mult

        if self.slow_timer > 0:
            self.slow_timer -= 1
        else:
            self.slow_mult = 1.0

        # AI: Pick the closest target (Player, Clones, or NPC Germs)
        current_target_pos = None
        if targets:
            closest_dist = 99999
            for t in targets:
                # 't' can be Player, Clone, or EnemyGerm (excluding other WBCs)
                if t == self or isinstance(t, WhiteBloodCell) or isinstance(t, EliteWBC):
                    continue
                
                dx = t.world_x - self.world_x
                dy = t.world_y - self.world_y
                dist = dx*dx + dy*dy
                if dist < closest_dist:
                    closest_dist = dist
                    current_target_pos = (t.world_x, t.world_y)

        # Always chase target
        if current_target_pos:
            dx = current_target_pos[0] - self.world_x
            dy = current_target_pos[1] - self.world_y
            dist = max(1, math.sqrt(dx * dx + dy * dy))
            self.world_x += (dx / dist) * speed
            self.world_y += (dy / dist) * speed

        # Clamp
        self.world_x = max(self.radius, min(self.world_x, WORLD_WIDTH - self.radius))
        self.world_y = max(self.radius, min(self.world_y, WORLD_HEIGHT - self.radius))
        self.rect.center = (int(self.world_x), int(self.world_y))

        # Animation
        self.pulse_timer += 0.04
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
        for i in range(len(self.tentacle_angles)):
            self.tentacle_angles[i] += random.uniform(-0.05, 0.05)
            self.tentacle_lengths[i] += random.uniform(-0.3, 0.3)
            self.tentacle_lengths[i] = max(6, min(18, self.tentacle_lengths[i]))

    def take_damage(self, amount):
        self.health -= amount
        self.hit_flash_timer = 3
        if self.health <= 0:
            self.kill()
            return True
        return False

    def apply_slow(self, duration=60, factor=0.5):
        self.slow_timer = duration
        self.slow_mult = factor

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        # Dim glow circle
        glow_r = int(self.radius * 1.8)
        dim_wbc = tuple(c // 6 for c in COLOR_WBC[:3])
        pygame.draw.circle(surface, dim_wbc, (sx, sy), glow_r)

        # Tentacles / pseudopods
        for i in range(len(self.tentacle_angles)):
            angle = self.tentacle_angles[i]
            length = self.tentacle_lengths[i] + self.radius
            ex = sx + math.cos(angle) * length
            ey = sy + math.sin(angle) * length
            pygame.draw.line(surface, COLOR_WBC, (sx, sy), (int(ex), int(ey)), 3)
            pygame.draw.circle(surface, (220, 230, 245), (int(ex), int(ey)), 3)

        # Main body
        pulse = 0.95 + 0.05 * math.sin(self.pulse_timer)
        body_r = int(self.radius * pulse)
        
        if self.hit_flash_timer > 0:
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy), body_r)
        else:
            pygame.draw.circle(surface, COLOR_WBC, (sx, sy), body_r)
            pygame.draw.circle(surface, (180, 190, 210), (sx, sy), body_r, 2)
            # Nucleus (kidney-shaped — draw two offset circles)
            n_r = max(3, body_r // 3)
            n_color = (160, 170, 200)
            pygame.draw.circle(surface, n_color, (sx - 3, sy), n_r)
            pygame.draw.circle(surface, n_color, (sx + 3, sy), n_r)

        # Health bar
        if self.health < self.max_health:
            bar_w = self.radius * 2
            bar_h = 3
            bar_x = sx - bar_w // 2
            bar_y = sy - self.radius - 10
            pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h))
            fill = int(bar_w * (self.health / self.max_health))
            pygame.draw.rect(surface, COLOR_WBC, (bar_x, bar_y, fill, bar_h))


class BossGerm(pygame.sprite.Sprite):
    """Massive boss germ with multiple attack phases."""

    def __init__(self, x, y, boss_tier=1):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.tier = boss_tier
        self.radius = BOSS_RADIUS + (boss_tier - 1) * 10
        self.speed = BOSS_SPEED
        self.health = BOSS_HEALTH * boss_tier
        self.max_health = self.health
        self.damage = BOSS_DAMAGE * boss_tier
        self.xp_drop = BOSS_XP_DROP * boss_tier
        
        # Boss Identification for Intro
        boss_names = ["CYTOTOXIC ALPHA", "CORE BREAKER", "NECROSIS PRIME", "CELL HUNTER", "MALIGNANT X"]
        self.name = boss_names[(boss_tier - 1) % len(boss_names)]
        if boss_tier > 5:
            self.name += f" V{boss_tier}"

        # Attack phases
        self.phase = "chase"  # chase / charge / scatter / spawn
        self.phase_timer = 0
        self.phase_duration = 180  # frames per phase
        self.charge_speed = self.speed * 3
        self.charge_target = None

        # Scatter projectile state
        self.scatter_timer = 0
        self.scatter_count = 0

        # Minion spawning
        self.minions_spawned = 0
        self.max_minions = 3 + boss_tier

        # Visual
        self.pulse_timer = 0
        self.tentacle_data = []
        for _ in range(8):
            self.tentacle_data.append({
                "angle": random.uniform(0, math.pi * 2),
                "length": random.uniform(15, 30),
                "speed": random.uniform(0.02, 0.05),
                "phase": random.uniform(0, math.pi * 2),
            })

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

        # Slow effect
        self.slow_timer = 0
        self.slow_mult = 1.0
        self.hit_flash_timer = 0

    def update(self, player_pos=None):
        speed = self.speed * self.slow_mult

        if self.slow_timer > 0:
            self.slow_timer -= 1
        else:
            self.slow_mult = 1.0

        self.phase_timer += 1
        self.pulse_timer += 0.03

        # Cycle through phases
        if self.phase_timer >= self.phase_duration:
            self.phase_timer = 0
            self.minions_spawned = 0
            self.scatter_count = 0
            phases = ["chase", "charge", "scatter", "spawn"]
            current_idx = phases.index(self.phase) if self.phase in phases else 0
            self.phase = phases[(current_idx + 1) % len(phases)]

            if self.phase == "charge" and player_pos:
                self.charge_target = (player_pos[0], player_pos[1])

        # Phase behavior
        if self.phase == "chase" and player_pos:
            dx = player_pos[0] - self.world_x
            dy = player_pos[1] - self.world_y
            dist = max(1, math.sqrt(dx * dx + dy * dy))
            self.world_x += (dx / dist) * speed
            self.world_y += (dy / dist) * speed

        elif self.phase == "charge" and self.charge_target:
            dx = self.charge_target[0] - self.world_x
            dy = self.charge_target[1] - self.world_y
            dist = max(1, math.sqrt(dx * dx + dy * dy))
            if dist > 10:
                self.world_x += (dx / dist) * self.charge_speed * self.slow_mult
                self.world_y += (dy / dist) * self.charge_speed * self.slow_mult

        elif self.phase == "scatter":
            # Slowly move, scatter timer handled in game.py
            if player_pos:
                dx = player_pos[0] - self.world_x
                dy = player_pos[1] - self.world_y
                dist = max(1, math.sqrt(dx * dx + dy * dy))
                self.world_x += (dx / dist) * speed * 0.3
                self.world_y += (dy / dist) * speed * 0.3

        elif self.phase == "spawn":
            # Stay still, spawning handled in game.py
            pass

        # Clamp
        self.world_x = max(self.radius, min(self.world_x, WORLD_WIDTH - self.radius))
        self.world_y = max(self.radius, min(self.world_y, WORLD_HEIGHT - self.radius))
        self.rect.center = (int(self.world_x), int(self.world_y))

        # Tentacle animation
        for t in self.tentacle_data:
            t["angle"] += t["speed"]
            t["length"] += random.uniform(-0.5, 0.5)
            t["length"] = max(10, min(35, t["length"]))
            
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

    def take_damage(self, amount):
        self.health -= amount
        self.hit_flash_timer = 4  # Longer flash for boss
        if self.health <= 0:
            self.kill()
            return True
        return False

    def apply_slow(self, duration=60, factor=0.5):
        self.slow_timer = duration
        self.slow_mult = factor

    def should_scatter_projectile(self):
        """Returns True when it's time to emit a scatter projectile."""
        if self.phase == "scatter":
            self.scatter_timer += 1
            if self.scatter_timer >= 15:  # Every 15 frames
                self.scatter_timer = 0
                self.scatter_count += 1
                return self.scatter_count <= 8
        return False

    def should_spawn_minion(self):
        """Returns True when a minion should be spawned."""
        if self.phase == "spawn" and self.minions_spawned < self.max_minions:
            if self.phase_timer % 40 == 0:
                self.minions_spawned += 1
                return True
        return False

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        # Dim menacing glow
        glow_r = int(self.radius * 2)
        dim_boss = tuple(c // 5 for c in COLOR_BOSS[:3])
        pygame.draw.circle(surface, dim_boss, (sx, sy), glow_r)

        # Tentacles
        for t in self.tentacle_data:
            angle = t["angle"]
            length = t["length"] + self.radius
            wave = math.sin(self.pulse_timer * 3 + t["phase"]) * 5
            ex = sx + math.cos(angle) * (length + wave)
            ey = sy + math.sin(angle) * (length + wave)
            # Thick tentacle
            pygame.draw.line(surface, COLOR_BOSS, (sx, sy), (int(ex), int(ey)), 4)
            pygame.draw.circle(surface, (220, 60, 60), (int(ex), int(ey)), 4)

        # Main body
        pulse = 0.95 + 0.05 * math.sin(self.pulse_timer)
        body_r = int(self.radius * pulse)
        
        if self.hit_flash_timer > 0:
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy), body_r)
        else:
            pygame.draw.circle(surface, COLOR_BOSS, (sx, sy), body_r)
            # Inner rings
            pygame.draw.circle(surface, (200, 50, 50), (sx, sy), int(body_r * 0.8), 2)
            pygame.draw.circle(surface, (220, 70, 70), (sx, sy), int(body_r * 0.5), 2)
            # Nucleus
            n_r = max(5, body_r // 3)
            pygame.draw.circle(surface, (100, 20, 20), (sx, sy), n_r)
            pygame.draw.circle(surface, (140, 30, 30), (sx - 2, sy - 2), max(2, n_r // 2))

        # Phase indicator ring
        if self.phase == "charge":
            pygame.draw.circle(surface, (255, 200, 60), (sx, sy), body_r + 5, 2)
        elif self.phase == "scatter":
            pygame.draw.circle(surface, (255, 100, 255), (sx, sy), body_r + 5, 2)
        elif self.phase == "spawn":
            pygame.draw.circle(surface, (100, 255, 100), (sx, sy), body_r + 5, 2)


class BossProjectile(pygame.sprite.Sprite):
    """Projectile scattered by the boss during scatter phase."""

    def __init__(self, x, y, angle):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.speed = 3.0
        self.damage = 10
        self.radius = 6
        self.lifetime = 180

        self.vel_x = math.cos(angle) * self.speed
        self.vel_y = math.sin(angle) * self.speed
        self.pulse_timer = 0

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self):
        self.world_x += self.vel_x
        self.world_y += self.vel_y
        self.rect.center = (int(self.world_x), int(self.world_y))
        self.lifetime -= 1
        self.pulse_timer += 0.1

        if self.lifetime <= 0:
            self.kill()

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)

        # Dim glow
        glow_r = int(self.radius * 1.6)
        pygame.draw.circle(surface, (65, 20, 20), (sx, sy), glow_r)

        pulse = 0.8 + 0.2 * math.sin(self.pulse_timer)
        r = max(2, int(self.radius * pulse))
        pygame.draw.circle(surface, (255, 100, 80), (sx, sy), r)
        pygame.draw.circle(surface, (255, 180, 150), (sx, sy), max(1, r // 2))

class HeavyEnemy(EnemyGerm):
    """A tanky enemy found in wounds. Slower but has high health and damage."""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = HEAVY_RADIUS
        self.health = HEAVY_HEALTH
        self.max_health = self.health
        self.speed = HEAVY_SPEED
        self.damage = HEAVY_DAMAGE
        self.xp_drop = HEAVY_XP_DROP
        self.color = (140, 40, 40) # Even darker, menacing red
        
        # Ability timers
        self.pull_pulse = 0
        
    def draw(self, surface, camera):
        # Draw gravity aura
        sx, sy = camera.apply((self.world_x, self.world_y))
        
        # Pulsing dark rings
        self.pull_pulse += 0.1
        for i in range(3):
            r_off = (self.pull_pulse + i * 1.5) % 4.5
            aura_r = int(self.radius * (1.2 + r_off * 0.4))
            alpha = int(max(0, 100 - (r_off * 20)))
            # Draw a circle with alpha - using a temporary surface since draw.circle doesn't поддерж alpha directly on target unless target is transparent
            # Actually, just draw thin rings
            pygame.draw.circle(surface, (60, 20, 20), (int(sx), int(sy)), aura_r, 1)

        super().draw(surface, camera)
        # Menacing core overlay
        pygame.draw.circle(surface, (80, 10, 10), (int(sx), int(sy)), int(self.radius * 0.5), 2)

class ChargerEnemy(EnemyGerm):
    """A fast, squishy enemy found in veins. Dashes when close to player."""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = CHARGER_RADIUS
        self.health = CHARGER_HEALTH
        self.max_health = self.health
        self.base_speed = CHARGER_SPEED
        self.dash_speed = CHARGER_DASH_SPEED
        self.speed = self.base_speed
        self.damage = CHARGER_DAMAGE
        self.xp_drop = CHARGER_XP_DROP
        self.color = (60, 100, 200) # Blue
        self.dash_cooldown = 0

    def update(self, player_pos=None):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        # Override speed logic for dashing
        if player_pos and self.dash_cooldown == 0:
            dx = player_pos[0] - self.world_x
            dy = player_pos[1] - self.world_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 150:
                self.speed = self.dash_speed
                self.dash_cooldown = 120 # 5 seconds
            elif self.speed > self.base_speed:
                self.speed *= 0.95 # Slow down after dash
                if self.speed < self.base_speed: self.speed = self.base_speed
        
        super().update(player_pos)

class SpitterEnemy(EnemyGerm):
    """A ranged enemy found in follicles. Shoots projectiles from distance."""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = SPITTER_RADIUS
        self.health = SPITTER_HEALTH
        self.max_health = self.health
        self.speed = SPITTER_SPEED
        self.damage = SPITTER_DAMAGE
        self.xp_drop = SPITTER_XP_DROP
        self.color = (150, 200, 60) # Greenish
        self.shoot_timer = random.randint(0, 60)
        self.should_shoot = False

    def update(self, player_pos=None):
        super().update(player_pos)
        self.should_shoot = False
        
        if self.state == "chase" and player_pos:
            self.shoot_timer += 1
            if self.shoot_timer >= 60:
                self.shoot_timer = 0
                self.should_shoot = True

    def draw(self, surface, camera):
        super().draw(surface, camera)
        # Add a visual cue for firing
        if self.shoot_timer > 45:
            sx, sy = camera.apply((self.world_x, self.world_y))
            pygame.draw.circle(surface, (255, 255, 200), (int(sx), int(sy)), self.radius + 2, 1)


class ExploderGerm(EnemyGerm):
    """A suicidal enemy that rushes the player and explodes."""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = EXPLODER_RADIUS
        self.health = EXPLODER_HEALTH
        self.max_health = self.health
        self.speed = EXPLODER_SPEED
        self.damage = EXPLODER_DAMAGE
        self.xp_drop = EXPLODER_XP_DROP
        self.color = (255, 100, 50) # Orange-red
        
        self.fusing = False
        self.fuse_timer = 0
        self.exploded = False

    def update(self, player_pos=None):
        if self.exploded: 
            return
        
        if self.fusing:
            self.fuse_timer += 1
            if self.fuse_timer >= EXPLODER_FUSE_TIME:
                self.exploded = True
            return # Stop moving while fusing
            
        super().update(player_pos)
        
        if player_pos and self.state == "chase":
            dx = player_pos[0] - self.world_x
            dy = player_pos[1] - self.world_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 60:
                self.fusing = True

    def draw(self, surface, camera):
        if self.exploded: return
        
        # Flashing effect when fusing
        color = self.color
        if self.fusing:
            if (self.fuse_timer // 3) % 2 == 0:
                color = (255, 255, 255)
            else:
                color = (255, 0, 0)
                
        # Override draw to use fuse specific color
        original_color = self.color
        self.color = color
        super().draw(surface, camera)
        self.color = original_color

class EliteWBC(WhiteBloodCell):
    """A powerful WBC that can dash towards the player."""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = ELITE_WBC_RADIUS
        self.health = ELITE_WBC_HEALTH
        self.max_health = self.health
        self.speed = ELITE_WBC_SPEED
        self.damage = ELITE_WBC_DAMAGE
        self.xp_drop = ELITE_WBC_XP_DROP
        
        self.base_speed = ELITE_WBC_SPEED
        self.dash_speed = ELITE_WBC_DASH_SPEED
        self.dash_cooldown = random.randint(0, 60)
        self.is_dashing = False
        self.dash_timer = 0

    def update(self, targets=None):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
            
        if self.is_dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.speed = self.base_speed
        elif targets and self.dash_cooldown <= 0:
            # Pick closest target similar to WBC
            closest_dist = 99999
            current_target = None
            for t in targets:
                if t == self or isinstance(t, WhiteBloodCell) or isinstance(t, EliteWBC):
                    continue
                dx = t.world_x - self.world_x
                dy = t.world_y - self.world_y
                dist = dx*dx + dy*dy
                if dist < closest_dist:
                    closest_dist = dist
                    current_target = t

            if current_target and closest_dist < 250*250:
                self.is_dashing = True
                self.dash_timer = 15
                self.speed = self.dash_speed
                self.dash_cooldown = ELITE_WBC_DASH_COOLDOWN
                
        super().update(targets)

    def draw(self, surface, camera):
        super().draw(surface, camera)
        if self.is_dashing:
            # Afterimage/Speed lines
            sx, sy = camera.apply((self.world_x, self.world_y))
            pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), self.radius + 4, 1)

