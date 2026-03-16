"""
game.py — Main game state manager
Handles MENU, PLAYING, EVOLUTION_PICK, and GAME_OVER states.
Manages all sprite groups, collision detection, spawning, and difficulty scaling.
"""
import pygame
import math
import random
import time as _time

import settings as _settings_module
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    WORLD_WIDTH, WORLD_HEIGHT,
    PLAYER_AURA_RADIUS, PLAYER_AURA_DAMAGE,
    ENEMY_SPAWN_RATE_BASE, ENEMY_SPAWN_RATE_MIN, ENEMY_SPAWN_SCALE,
    WBC_SPAWN_START, WBC_SPAWN_RATE,
    SOAP_SPAWN_START, WATER_SPAWN_START,
    BOSS_SPAWN_INTERVAL,
    FOOD_SPAWN_RATE, FOOD_MAX_COUNT,
    POWERUP_DROP_CHANCE, POWERUP_BOSS_DROPS,
    COMBO_WINDOW, COMBO_MAX,
    MAX_CLONES,
    ENEMY_XP_DROP, WBC_XP_DROP,
    PLAYER_MAX_HEALTH,
    SFX_VOLUME, MUSIC_VOLUME, SETTING_SCREEN_SHAKE, SETTING_CRT_FX, SETTING_GLITCH_FX,
    LIGHT_RADIUS_PLAYER, LIGHT_DARKNESS_ALPHA, LIGHT_MIN_RADIUS,
    HEAVY_SLOW_RADIUS, HEAVY_SLOW_FACTOR, HEAVY_PULL_FORCE,
    EXPLODER_AOE_RADIUS, EXPLODER_DAMAGE,
    NERVE_STUN_DURATION, COLOR_NERVE_GLOW,
    ITEM_SPAWN_RATE,
    ALCOHOL_SPAWN_START, ALCOHOL_SPAWN_RATE,
    BURST_BASE_RADIUS, BURST_BASE_DAMAGE, BURST_COOLDOWN,
)

from camera import Camera
from player import Player, Clone, AcidProjectile, EnemyProjectile
from enemy import EnemyGerm, WhiteBloodCell, BossGerm, BossProjectile, HeavyEnemy, ChargerEnemy, SpitterEnemy, ExploderGerm, EliteWBC
from food import Food, XPOrb
from hazard import Soap, Water, AlcoholZone, AlcoholWave
from powerup import PowerUp, ActivePowerUp
from evolution import EvolutionSystem
from particle import ParticleManager
from world import World, TissueObstacle
from hud import HUD
from item import Item
import sound


class Game:
    """Central game controller managing all states and logic."""

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "MENU"  # MENU, PLAYING, EVOLUTION_PICK, GAME_OVER

        # Core systems
        self.camera = Camera()
        self.particles = ParticleManager()
        self.evolution = EvolutionSystem()
        self.hud = HUD()
        self.world = None

        # Sprite groups
        self.enemies = pygame.sprite.Group()
        self.foods = pygame.sprite.Group()
        self.xp_orbs = pygame.sprite.Group()
        self.hazards = pygame.sprite.Group()
        self.clones = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()       # Player acid spit
        self.boss_projectiles = pygame.sprite.Group()   # Boss scatter
        self.enemy_projectiles = pygame.sprite.Group()  # For Spitter enemies
        self.alcohol_waves = pygame.sprite.Group()       # Alcohol Wave entities
        self.alcohol_zones = pygame.sprite.Group()        # Alcohol Zone overlays
        self.obstacles = pygame.sprite.Group()           # Static map obstacles

        # Player
        self.player = None

        # Game state
        self.game_time = 0.0
        self.score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.clones_made = 0
        self.hit_stop_frames = 0

        # Active power-ups on player
        self.active_powerups = []
        self.items = pygame.sprite.Group() # New for items
        self.item_spawn_timer = 0.0
        self.burst_visuals = [] # To store (x, y, r, timer)

        # Boss tracking
        self.current_boss = None
        self.boss_tier = 1
        self.last_boss_time = 0

        # Spawn timers (seconds)
        self.enemy_spawn_timer = 0.0
        self.enemy_spawn_rate = ENEMY_SPAWN_RATE_BASE
        self.food_spawn_timer = 0.0
        self.wbc_spawn_timer = 0.0
        self.soap_spawn_timer = 0.0
        self.water_spawn_timer = 0.0

        # Acid spit timer
        self.acid_spit_timer = 0.0
        self.acid_spit_rate = 1.0  # seconds between shots

        # Difficulty scaling timer
        self.difficulty_timer = 0.0

        # Glitch / FX state
        self.glitch_timer = 0
        self.boss_intro_timer = 0
        self.boss_intro_name = ""
        
        # Settings Menu state
        self.settings_index = 0
        self.settings_data = [
            # [key, label, type, value]
            ["sfx_vol", "SFX Volume", "float", SFX_VOLUME],
            ["music_vol", "Music Volume", "float", MUSIC_VOLUME],
            ["shake", "Screen Shake", "bool", SETTING_SCREEN_SHAKE],
            ["scanlines", "Retro Scanlines", "bool", SETTING_CRT_FX],
            ["glitch", "Glitch Effects", "bool", SETTING_GLITCH_FX],
        ]

    def reset(self):
        """Reset all game state for a new game."""
        self.state = "PLAYING"
        self.game_time = 0.0
        self.score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.clones_made = 0
        self.hit_stop_frames = 0

        # Clear groups
        self.enemies.empty()
        self.foods.empty()
        self.xp_orbs.empty()
        self.hazards.empty()
        self.clones.empty()
        self.powerups.empty()
        self.projectiles.empty()
        self.boss_projectiles.empty()
        self.enemy_projectiles.empty()
        self.items.empty()
        self.burst_visuals = []
        self.item_spawn_timer = 0.0
        self.alcohol_waves.empty()
        self.alcohol_zones.empty()
        self.alcohol_spawn_timer = 0.0
        self.obstacles.empty()

        # Reset systems
        self.camera = Camera()
        self.particles = ParticleManager()
        # Pacing & Events
        self.pacing_state = "NORMAL"  # NORMAL, AMBUSH, DORMANT, BLOOM
        self.pacing_timer = 0.0
        self.event_cooldown = 45.0    # Time until next possible event
        self.elite_hunt_target = None
        self.evolution = EvolutionSystem()
        self.active_powerups = []

        # Create world
        self.world = World()

        # ── Spawn Static Obstacles ──
        for _ in range(30):
            # Try to spawn far from the center (avoid blocking player spawn)
            ox, oy = self._random_spawn_pos(300)
            radius = random.uniform(30, 80)
            self.obstacles.add(TissueObstacle(ox, oy, radius))

        # Create player at center
        self.player = Player(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)

        # Reset spawn timers
        self.enemy_spawn_timer = 0.0
        self.enemy_spawn_rate = ENEMY_SPAWN_RATE_BASE
        self.food_spawn_timer = 0.0
        self.wbc_spawn_timer = 0.0
        self.soap_spawn_timer = 0.0
        self.water_spawn_timer = 0.0
        self.acid_spit_timer = 0.0
        self.difficulty_timer = 0.0

        # Boss
        self.current_boss = None
        self.boss_tier = 1
        self.last_boss_time = 0

        # Spawn initial food
        for _ in range(20):
            self.foods.add(Food())

        # Spawn a few enemies
        for _ in range(5):
            x, y = self._random_spawn_pos(200)
            self.enemies.add(EnemyGerm(x, y))

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            dt = min(dt, 0.05)  # Cap delta time

            # ── Events ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

                if event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)

            # ── Update ──
            if self.state == "MENU":
                pass  # Menu is static, just drawn
            elif self.state == "PLAYING":
                self._update_playing(dt)
            elif self.state == "EVOLUTION_PICK":
                self.evolution.update_animation()
            elif self.state == "SETTINGS":
                pass
            elif self.state == "BOSS_INTRO":
                self.boss_intro_timer -= 1
                if self.boss_intro_timer <= 0:
                    self.state = "PLAYING"
            elif self.state == "GAME_OVER":
                pass

            # ── Draw ──
            self._draw()

            pygame.display.flip()

    def _handle_keydown(self, key):
        """Handle key press events."""
        if key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            return

        if self.state == "MENU":
            if key == pygame.K_RETURN:
                self.reset()
            elif key == pygame.K_s:
                self.state = "SETTINGS"

        elif self.state == "PLAYING":
            if key == pygame.K_ESCAPE:
                self.state = "SETTINGS"
            elif key == pygame.K_SPACE:
                self._try_replicate()
            elif key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                if hasattr(self, 'player') and self.player.alive:
                    if self.player.dash():
                        if sound.audio: sound.audio.play("shoot")
            elif key == pygame.K_j: # Manual burst hotkey
                self._trigger_burst_skill()
            elif key == pygame.K_1:
                self._use_inventory_item(0)
            elif key == pygame.K_2:
                self._use_inventory_item(1)
            elif key == pygame.K_3:
                self._use_inventory_item(2)

        elif self.state == "EVOLUTION_PICK":
            if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                index = key - pygame.K_1  # 0, 1, or 2
                selected = self.evolution.select_mutation(index)
                if selected is not None:
                    self.state = "PLAYING"
                    # Apply mutation effects
                    self._apply_mutations()
                    self.particles.emit_divide(self.player.world_x, self.player.world_y)
                    self.camera.shake(8)

        elif self.state == "SETTINGS":
            if key == pygame.K_ESCAPE:
                if self.player and self.player.alive:
                    self.state = "PLAYING"
                else:
                    self.state = "MENU"
            elif key == pygame.K_UP:
                self.settings_index = (self.settings_index - 1) % len(self.settings_data)
            elif key == pygame.K_DOWN:
                self.settings_index = (self.settings_index + 1) % len(self.settings_data)
            elif key in (pygame.K_LEFT, pygame.K_RIGHT):
                self._adjust_setting(key)
            elif key == pygame.K_RETURN:
                # Toggle bools on Enter too
                if self.settings_data[self.settings_index][2] == "bool":
                    self.settings_data[self.settings_index][3] = not self.settings_data[self.settings_index][3]
                    self._apply_settings()

        elif self.state == "GAME_OVER":
            if key == pygame.K_r:
                self.reset()
            elif key == pygame.K_ESCAPE:
                self.state = "MENU"

    def _try_replicate(self):
        """Attempt germ replication."""
        discount = self.evolution.get_replication_discount()
        if self.player.can_replicate(discount) and len(self.clones) < MAX_CLONES:
            self.player.spend_energy(discount)
            clone = Clone(self.player, len(self.clones))
            if self.evolution.clones_spawn_full_hp():
                clone.health = clone.max_health
            self.clones.add(clone)
            self.clones_made += 1
            self.particles.emit_divide(self.player.world_x, self.player.world_y)
            self.camera.shake(6)

    def _update_playing(self, dt):
        """Update all game logic during PLAYING state."""
        # ── Hit Stop (Freeze Frame) ──
        if self.hit_stop_frames > 0:
            self.hit_stop_frames -= 1
            # Only update particles/camera during hit stop for visual juice
            self.particles.update()
            return

        self.game_time += dt

        # ── Player input & update ──
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update()

        # ── Camera ──
        self.camera.update(self.player.pos)

        # ── World ──
        self.world.update(self.player.pos)

        # ── Power-up effects on player ──
        self._update_powerups(dt)

        # ── Burst Skill Animation ──
        for b in list(self.burst_visuals):
            b[3] -= dt
            if b[3] <= 0:
                self.burst_visuals.remove(b)

        # ── Combo decay ──
        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

        # ── Spawning ──
        self._update_spawning(dt)
        self._update_item_spawning(dt)

        # ── Acid spit (auto-fire if mutation active) ──
        self._update_acid_spit(dt)
        
        # Resolve player obstacle collision immediately after update
        self._resolve_obstacle_collision(self.player)
        
        # ── Mouse Input for Burst ──
        if pygame.mouse.get_pressed()[0]: # Left click
            self._trigger_burst_skill()

        # ── Update entities ──
        for food in self.foods:
            food.update()

        for orb in list(self.xp_orbs):
            magnet_range = self._get_magnet_range()
            orb.update(self.player.pos, magnet_range)

        # Prepare a list of all potential targets for WBCs (Player, Clones, NPC Enemies)
        all_targets = [self.player] + list(self.clones) + list(self.enemies)

        for enemy in self.enemies:
            if isinstance(enemy, BossGerm):
                enemy.update(self.player.pos)
                self._update_boss_attacks(enemy)
            elif isinstance(enemy, WhiteBloodCell) or isinstance(enemy, EliteWBC):
                enemy.update(all_targets)
            else:
                enemy.update(self.player.pos)
            
            # Resolve enemy obstacle collision
            self._resolve_obstacle_collision(enemy)
            
            # Check if spitter wants to shoot
            if getattr(enemy, 'should_shoot', False):
                dx = self.player.world_x - enemy.world_x
                dy = self.player.world_y - enemy.world_y
                proj = EnemyProjectile(enemy.world_x, enemy.world_y, dx, dy, enemy.damage)
                self.enemy_projectiles.add(proj)
                if sound.audio: sound.audio.play("shoot")

        for item in self.items:
            item.update()

        # Alcohol Waves chase all targets
        all_alcohol_targets = [self.player] + list(self.clones) + list(self.enemies)
        for wave in self.alcohol_waves:
            wave.update(all_alcohol_targets)
            self._resolve_obstacle_collision(wave)

        for zone in self.alcohol_zones:
            zone.update()
            # Spawn waves once per zone
            if not zone.waves_spawned:
                for wx, wy in zone.get_wave_spawn_positions():
                    self.alcohol_waves.add(AlcoholWave(wx, wy))
                self.camera.shake(15)
                self.glitch_timer = 15
                if sound.audio: sound.audio.play("boss_spawn")

        for clone in self.clones:
            clone.update(self.enemies)
            self._resolve_obstacle_collision(clone)

        for hazard in self.hazards:
            hazard.update()

        for pu in self.powerups:
            pu.update()

        for proj in self.projectiles:
            proj.update()

        for bp in self.boss_projectiles:
            bp.update()

        for ep in self.enemy_projectiles:
            ep.update()

        # ── Toxin aura ──
        self._update_aura()

        # ── Collisions ──
        self._check_collisions()

        # ── World interactions ──
        if self.player.alive:
            for nerve in self.world.nerves:
                if nerve.active:
                    dx = nerve.world_x - self.player.world_x
                    dy = nerve.world_y - self.player.world_y
                    if math.sqrt(dx*dx + dy*dy) < nerve.radius + self.player.radius:
                        if nerve.trigger():
                            self._trigger_nerve_stun(nerve)

        # ── Particles ──
        self.particles.update()

        # ── Difficulty scaling ──
        self._update_difficulty(dt)

        # ── Check player death ──
        if not self.player.alive:
            self.state = "GAME_OVER"

    def _update_powerups(self, dt):
        """Update active power-up timers and apply effects."""
        # Reset player multipliers
        self.player.speed_mult = self.evolution.get_speed_bonus()
        self.player.damage_mult = 1.0
        regen_rate = 0
        energy_regen = 0.5 # Base energy slowly regens

        # --- BIOME EFFECTS ---
        current_biome = self.world.get_biome_at(self.player.world_x, self.player.world_y)
        if current_biome == "cyst":
            energy_regen += 2.0 # Cysts recharge energy!
            if self.game_time % 30 == 0:
                self.particles.emit_powerup(self.player.world_x, self.player.world_y, (255, 100, 200))
        
        # Crystal zones slow down ALL enemies within them
        for enemy in self.enemies:
            e_biome = self.world.get_biome_at(enemy.world_x, enemy.world_y)
            if e_biome == "crystal":
                enemy.apply_slow(10, 0.6) # Constant slow in crystals
        
        # --- ENEMY AURA EFFECTS (HEAVY ENEMY) ---
        # Heavy Enemy aura effects
        for enemy in self.enemies:
            if isinstance(enemy, HeavyEnemy):
                dx = enemy.world_x - self.player.world_x
                dy = enemy.world_y - self.player.world_y
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < HEAVY_SLOW_RADIUS:
                    # Slow player
                    self.player.speed_mult *= HEAVY_SLOW_FACTOR
                    
                    # Gravity pull (gentle displacement)
                    if dist > 10:
                        pull_x = (dx / dist) * HEAVY_PULL_FORCE
                        pull_y = (dy / dist) * HEAVY_PULL_FORCE
                        self.player.world_x += pull_x
                        self.player.world_y += pull_y
                        
                    # Periodic sudden jerk pull
                    if (self.game_time * 10) % 15 < 1.0: # Roughly every 1.5s
                        self.player.world_x += (dx / dist) * 3.0
                        self.player.world_y += (dy / dist) * 3.0
                        if random.random() < 0.1: self.camera.shake(2)
        # ---------------------

        new_active = []
        for pu in self.active_powerups:
            if pu.update(dt):
                new_active.append(pu)
                self.player.speed_mult *= pu.get_speed_mult()
                self.player.damage_mult *= pu.get_damage_mult()
                regen_rate += pu.get_regen_rate()
            # else: expired, don't keep

        self.active_powerups = new_active

        # Apply regen
        if regen_rate > 0:
            self.player.heal(regen_rate * dt)

    def _get_magnet_range(self):
        """Get the effective magnet range considering power-ups."""
        base = 100
        for pu in self.active_powerups:
            extra = pu.get_magnet_range()
            if extra > 0:
                base = max(base, extra)
        return base

    def _update_spawning(self, dt):
        """Handle all entity spawning with a Pacing Manager Wave System."""
        self.pacing_timer -= dt
        if self.event_cooldown > 0:
            self.event_cooldown -= dt

        # --- PACING STATE MACHINE ---
        if self.pacing_state == "NORMAL":
            if self.event_cooldown <= 0 and random.random() < 0.005:  # Random event trigger
                roll = random.random()
                if roll < 0.4:  # 40% chance for Ambush
                    self.pacing_state = "AMBUSH"
                    self.pacing_timer = 10.0  # 10 seconds of chaos
                    self.glitch_timer = 20
                    self.camera.shake(20)
                    if sound.audio: sound.audio.play("boss_spawn") # Re-use for alert
                elif roll < 0.7:  # 30% chance for Bloom
                    self.pacing_state = "BLOOM"
                    self.pacing_timer = 15.0
                else: # 30% chance for Elite Hunt (handled in update)
                    self._trigger_elite_hunt()
                    self.event_cooldown = 60.0 # Long CD for hunts

        elif self.pacing_timer <= 0:
            # Transition back to Normal (or Dormant after intensity)
            if self.pacing_state == "AMBUSH":
                self.pacing_state = "DORMANT"
                self.pacing_timer = 15.0 # 15 seconds of peace
            else:
                self.pacing_state = "NORMAL"
                self.event_cooldown = 30.0 + random.uniform(0, 30)

        # ── Spawning Logic based on State ──
        
        # 1. Food Spawning
        f_rate = FOOD_SPAWN_RATE
        if self.pacing_state == "BLOOM":
            f_rate *= 0.1 # Spawn food 10x faster!
        elif self.pacing_state == "DORMANT":
            f_rate *= 2.0 # Half speed
            
        self.food_spawn_timer += dt
        if self.food_spawn_timer >= f_rate and len(self.foods) < FOOD_MAX_COUNT * (2 if self.pacing_state == "BLOOM" else 1):
            self.food_spawn_timer = 0
            self.foods.add(Food())
            if self.pacing_state == "BLOOM" and random.random() < 0.3:
                # Add extra XP orbs during bloom
                x, y = self._random_spawn_pos(200)
                from food import XPOrb
                self.xp_orbs.add(XPOrb(x, y, 20))

        # 2. Enemy Spawning
        if self.pacing_state == "BLOOM":
            return # No enemies spawn during bloom!

        e_rate = self.enemy_spawn_rate
        if self.pacing_state == "DORMANT":
            e_rate *= 5.0 # Very slow
        elif self.pacing_state == "AMBUSH":
            e_rate *= 0.3 # 3x faster spawning

        self.enemy_spawn_timer += dt
        if self.enemy_spawn_timer >= e_rate:
            self.enemy_spawn_timer = 0
            x, y = self._random_spawn_pos(300)
            
            if self.pacing_state == "AMBUSH":
                # Ambushes are mostly Chargers and Exploders
                if random.random() < 0.7:
                    self.enemies.add(ChargerEnemy(x, y))
                else:
                    self.enemies.add(ExploderGerm(x, y))
            else:
                # Normal biome spawning
                biome = self.world.get_biome_at(x, y)
                if biome == "wound":
                    self.enemies.add(HeavyEnemy(x, y))
                elif biome == "vein":
                    self.enemies.add(ChargerEnemy(x, y))
                elif biome == "follicle":
                    self.enemies.add(SpitterEnemy(x, y))
                elif biome == "cyst":
                    if random.random() < 0.6:
                        self.enemies.add(ExploderGerm(x, y))
                    else:
                        self.enemies.add(SpitterEnemy(x, y))
                else:
                    self.enemies.add(EnemyGerm(x, y))

        # ── Boss ──
        if (self.game_time >= BOSS_SPAWN_INTERVAL and
            self.current_boss is None and
            self.game_time - self.last_boss_time >= BOSS_SPAWN_INTERVAL):
            self._spawn_boss()
            if sound.audio: sound.audio.play("boss_spawn")

        # ── Alcohol Zone Event ──
        if self.game_time >= ALCOHOL_SPAWN_START:
            self.alcohol_spawn_timer += dt
            if self.alcohol_spawn_timer >= ALCOHOL_SPAWN_RATE:
                self.alcohol_spawn_timer = 0
                x, y = self._random_spawn_pos(400)
                self.alcohol_zones.add(AlcoholZone(x, y))

    def _spawn_boss(self):
        """Spawn a boss germ and trigger a DORMANT phase afterward."""
        x, y = self._random_spawn_pos(500)
        boss = BossGerm(x, y, self.boss_tier)
        self.enemies.add(boss)
        self.current_boss = boss
        
        # Cinematic Splash!
        self.state = "BOSS_INTRO"
        self.boss_intro_timer = 100 
        self.boss_intro_name = boss.name
        self.last_boss_time = self.game_time
        self.camera.shake(15)

    def _trigger_elite_hunt(self):
        """Start an Elite WBC hunt event."""
        # Find a spawn position off-screen
        x, y = self._random_spawn_pos(500)
        elite = EliteWBC(x, y)
        self.enemies.add(elite)
        self.elite_hunt_target = elite
        self.glitch_timer = 10
        if sound.audio: sound.audio.play("boss_spawn")

    def _update_boss_attacks(self, boss):
        """Handle boss scatter projectiles and minion spawning."""
        if boss.should_scatter_projectile():
            # Scatter 8 projectiles in a circle
            for i in range(8):
                angle = (math.pi * 2 / 8) * i + random.uniform(-0.2, 0.2)
                proj = BossProjectile(boss.world_x, boss.world_y, angle)
                self.boss_projectiles.add(proj)
            self.camera.shake(5)

        if boss.should_spawn_minion():
            offset_x = random.uniform(-60, 60)
            offset_y = random.uniform(-60, 60)
            minion = EnemyGerm(boss.world_x + offset_x, boss.world_y + offset_y)
            minion.health *= 0.6
            minion.max_health = minion.health
            self.enemies.add(minion)

    def _update_acid_spit(self, dt):
        """Auto-fire acid projectiles if mutation is active."""
        if not self.evolution.can_acid_spit():
            return

        level = self.evolution.get_mutation_level("acid_spit")
        rate_mult = [1.0, 1.0, 0.6, 0.4][level]  # Faster at higher levels
        self.acid_spit_timer += dt

        if self.acid_spit_timer >= self.acid_spit_rate * rate_mult:
            self.acid_spit_timer = 0

            # Find nearest enemy to aim at
            closest_enemy = None
            closest_dist = 400  # Max range
            for enemy in self.enemies:
                dx = enemy.world_x - self.player.world_x
                dy = enemy.world_y - self.player.world_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < closest_dist:
                    closest_enemy = enemy
                    closest_dist = dist

            if closest_enemy:
                dx = closest_enemy.world_x - self.player.world_x
                dy = closest_enemy.world_y - self.player.world_y
                proj = AcidProjectile(
                    self.player.world_x, self.player.world_y,
                    dx, dy,
                    piercing=self.evolution.acid_spit_pierces()
                )
                proj.damage *= self.player.damage_mult
                self.projectiles.add(proj)
                if sound.audio: sound.audio.play("shoot")

    def _update_aura(self):
        """Apply toxin aura damage to nearby enemies."""
        aura_r = PLAYER_AURA_RADIUS * self.evolution.get_aura_bonus()
        aura_dmg = PLAYER_AURA_DAMAGE * self.player.damage_mult
        slows = self.evolution.aura_slows()

        for enemy in list(self.enemies) + list(self.alcohol_waves):
            dx = enemy.world_x - self.player.world_x
            dy = enemy.world_y - self.player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < aura_r:
                enemy.take_damage(aura_dmg)
                if slows and hasattr(enemy, 'apply_slow'):
                    enemy.apply_slow(30, 0.5)

    def _check_collisions(self):
        """Handle all collision interactions."""
        if not self.player:
            return

        player = self.player

        # ── Player ↔ Food ──
        for food in list(self.foods):
            dx = food.world_x - player.world_x
            dy = food.world_y - player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < player.radius + food.radius:
                if food.food_type == "health":
                    player.heal(food.amount)
                else:
                    player.add_energy(food.amount)
                player.food_collected += 1
                self.score += 5
                self.particles.emit_food(food.world_x, food.world_y)
                food.kill()
                if sound.audio: sound.audio.play("eat")

        # ── Player ↔ XP Orbs ──
        for orb in list(self.xp_orbs):
            magnet_range = self._get_magnet_range()
            orb.update((self.player.world_x, self.player.world_y), magnet_range)
            dx = orb.world_x - player.world_x
            dy = orb.world_y - player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < player.radius + orb.radius + 5:
                if self.evolution.add_xp(orb.xp_amount):
                    # Level up! Enter evolution pick state
                    self.state = "EVOLUTION_PICK"
                    if sound.audio: sound.audio.play("level_up")
                self.particles.emit_xp(orb.world_x, orb.world_y)
                orb.kill()
                if sound.audio: sound.audio.play("xp")

        # ── Player ↔ Enemies (contact damage) ──
        for enemy in list(self.enemies):
            dx = enemy.world_x - player.world_x
            dy = enemy.world_y - player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < player.radius + enemy.radius:
                damage = enemy.damage
                actual = player.take_damage(damage)
                if actual > 0:
                    self.particles.emit_hit(player.world_x, player.world_y)
                    self.camera.shake(8)
                    self.hit_stop_frames = 4  # Heavy hit pause on taking damage
                    if sound.audio: sound.audio.play("hit")
                    # Damage reflection
                    if self.evolution.reflects_damage():
                        enemy.take_damage(damage * 0.2)
                    
                    # Cool Extra: Trigger Glitch/Juice on heavy hit
                    if damage > 10:
                        self.glitch_timer = 12

            # Exploder Germ logic
            if isinstance(enemy, ExploderGerm) and enemy.exploded:
                # AOE damage to player and clones
                # AOE damage to player and clones
                dist_p = math.sqrt((enemy.world_x - player.world_x)**2 + (enemy.world_y - player.world_y)**2)
                if dist_p < EXPLODER_AOE_RADIUS:
                    player.take_damage(EXPLODER_DAMAGE)
                    self.camera.shake(15)
                    self.glitch_timer = 15
                
                for clone in self.clones:
                    dist_c = math.sqrt((enemy.world_x - clone.world_x)**2 + (enemy.world_y - clone.world_y)**2)
                    if dist_c < EXPLODER_AOE_RADIUS:
                        clone.take_damage(EXPLODER_DAMAGE)
                
                # Visual explosion
                self.particles.emit_divide(enemy.world_x, enemy.world_y) # Reuse divide for now
                if sound.audio: sound.audio.play("hit") # Could use better sound
                enemy.kill()

            # White Blood Cell Infighting logic
            if isinstance(enemy, WhiteBloodCell) or isinstance(enemy, EliteWBC):
                # WBC vs NPC Germs
                for other in self.enemies:
                    if other == enemy or isinstance(other, WhiteBloodCell) or isinstance(other, EliteWBC):
                        continue
                    dist = math.sqrt((enemy.world_x - other.world_x)**2 + (enemy.world_y - other.world_y)**2)
                    if dist < enemy.radius + other.radius:
                        if other.take_damage(enemy.damage * 0.1): # NPCs take less damage from WBCs to keep chaos alive
                            self.particles.emit_hit(other.world_x, other.world_y)
                
                # WBC vs Player Clones
                for clone in self.clones:
                    dist = math.sqrt((enemy.world_x - clone.world_x)**2 + (enemy.world_y - clone.world_y)**2)
                    if dist < enemy.radius + clone.radius:
                        clone.take_damage(enemy.damage * 0.5)
                        self.particles.emit_hit(clone.world_x, clone.world_y)

        # ── Player ↔ Power-ups ──
        for pu in list(self.powerups):
            dx = pu.world_x - player.world_x
            dy = pu.world_y - player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < player.radius + pu.radius:
                self._activate_powerup(pu.powerup_type)
                self.particles.emit_powerup(pu.world_x, pu.world_y, pu.color)
                self.camera.shake(3)
                pu.kill()

        # ── Player ↔ Items ──
        for item in list(self.items):
            dx = item.world_x - player.world_x
            dy = item.world_y - player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < player.radius + item.radius:
                if player.add_to_inventory(item.item_type):
                    self.particles.emit_powerup(item.world_x, item.world_y, item.color)
                    if sound.audio: sound.audio.play("powerup")
                    item.kill()

        # ── Player ↔ Boss Projectiles ──
        for bp in list(self.boss_projectiles):
            dx = bp.world_x - player.world_x
            dy = bp.world_y - player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < player.radius + bp.radius:
                actual = player.take_damage(bp.damage)
                if actual > 0:
                    self.particles.emit_hit(player.world_x, player.world_y)
                    self.camera.shake(6)
                bp.kill()

        # ── Player ↔ Enemy Projectiles (Spitter) ──
        for ep in list(self.enemy_projectiles):
            dx = ep.world_x - player.world_x
            dy = ep.world_y - player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < player.radius + ep.radius:
                actual = player.take_damage(ep.damage)
                if actual > 0:
                    self.particles.emit_hit(player.world_x, player.world_y)
                    self.camera.shake(4)
                ep.kill()

        # ── Projectiles ↔ Obstacles ──
        # Destroy projectiles that hit obstacles
        for proj in list(self.projectiles):
            for obs in self.obstacles:
                dx = proj.world_x - obs.world_x
                dy = proj.world_y - obs.world_y
                if math.sqrt(dx*dx + dy*dy) < proj.radius + obs.radius:
                    proj.kill()
                    self.particles.emit_hit(proj.world_x, proj.world_y, 2)
                    break
                    
        for ep in list(self.enemy_projectiles):
            for obs in self.obstacles:
                dx = ep.world_x - obs.world_x
                dy = ep.world_y - obs.world_y
                if math.sqrt(dx*dx + dy*dy) < ep.radius + obs.radius:
                    ep.kill()
                    self.particles.emit_hit(ep.world_x, ep.world_y, 2)
                    break

        for bp in list(self.boss_projectiles):
            for obs in self.obstacles:
                dx = bp.world_x - obs.world_x
                dy = bp.world_y - obs.world_y
                if math.sqrt(dx*dx + dy*dy) < bp.radius + obs.radius:
                    bp.kill()
                    self.particles.emit_hit(bp.world_x, bp.world_y, 2)
                    break

        # ── Player Projectiles ↔ Enemies / Alcohol ──
        for proj in list(self.projectiles):
            for enemy in list(self.enemies) + list(self.alcohol_waves):
                dx = proj.world_x - enemy.world_x
                dy = proj.world_y - enemy.world_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < proj.radius + enemy.radius:
                    killed = enemy.take_damage(proj.damage)
                    self.particles.emit_hit(enemy.world_x, enemy.world_y, 4)
                    if sound.audio: sound.audio.play("hit")

                    # Lifesteal
                    lifesteal = self.evolution.get_lifesteal()
                    if lifesteal > 0:
                        player.heal(proj.damage * lifesteal)

                    if killed and enemy in self.enemies:
                        self._on_enemy_killed(enemy)

                    if not proj.piercing:
                        proj.kill()
                        break

        # ── Clones ↔ Enemies (already handled in clone.update) ──
        # Check for enemy deaths from clone damage
        for enemy in list(self.enemies):
            if not enemy.alive():
                self._on_enemy_killed(enemy)
                enemy.kill()

        # ── Hazards ↔ Player ──
        for hazard in self.hazards:
            if isinstance(hazard, Soap):
                dx = hazard.world_x - player.world_x
                dy = hazard.world_y - player.world_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < hazard.radius + player.radius:
                    # Soap = instant kill (unless shield)
                    has_shield = False
                    for pu in self.active_powerups:
                        if pu.powerup_type == "shield" and pu.shield_hits > 0:
                            pu.absorb_hit()
                            has_shield = True
                            self.camera.shake(10)
                            break
                    if not has_shield:
                        player.health = 0
                        self.particles.emit_death(player.world_x, player.world_y,
                                                  count=25)
                        self.camera.shake(20)

            elif isinstance(hazard, Water):
                if hazard.is_point_inside(player.world_x, player.world_y):
                    push = hazard.get_push_vector()
                    player.world_x += push[0]
                    player.world_y += push[1]

        # ── Hazards ↔ Enemies (soap kills them too) ──
        for hazard in list(self.hazards):
            if isinstance(hazard, Soap):
                for enemy in list(self.enemies):
                    dx = hazard.world_x - enemy.world_x
                    dy = hazard.world_y - enemy.world_y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < hazard.radius + enemy.radius:
                        self.particles.emit_death(enemy.world_x, enemy.world_y, count=10)
                        enemy.kill()
                        if enemy == self.current_boss:
                            self.current_boss = None

            elif isinstance(hazard, Water):
                for enemy in list(self.enemies):
                    if hazard.is_point_inside(enemy.world_x, enemy.world_y):
                        push = hazard.get_push_vector()
                        enemy.world_x += push[0]
                        enemy.world_y += push[1]

        # ── Hazards ↔ Clones ──
        for hazard in list(self.hazards):
            if isinstance(hazard, Soap):
                for clone in list(self.clones):
                    dx = hazard.world_x - clone.world_x
                    dy = hazard.world_y - clone.world_y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < hazard.radius + clone.radius:
                        self.particles.emit_death(clone.world_x, clone.world_y, count=8)
                        clone.kill()

        # ── Alcohol Waves ↔ ALL targets ──
        for wave in list(self.alcohol_waves):
            # vs Player
            dx = wave.world_x - player.world_x
            dy = wave.world_y - player.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < player.radius + wave.radius:
                actual = player.take_damage(wave.damage)
                if actual > 0:
                    self.particles.emit_hit(player.world_x, player.world_y)
                    self.camera.shake(15)
                    self.glitch_timer = 10

            # vs Enemies
            for enemy in list(self.enemies):
                dx = wave.world_x - enemy.world_x
                dy = wave.world_y - enemy.world_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < enemy.radius + wave.radius:
                    killed = enemy.take_damage(wave.damage)
                    self.particles.emit_hit(enemy.world_x, enemy.world_y)
                    if killed:
                        self._on_enemy_killed(enemy)
                        enemy.kill()

            # vs Clones
            for clone in list(self.clones):
                dx = wave.world_x - clone.world_x
                dy = wave.world_y - clone.world_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < clone.radius + wave.radius:
                    clone.take_damage(wave.damage)
                    self.particles.emit_hit(clone.world_x, clone.world_y)

    def _resolve_obstacle_collision(self, entity):
        """Push an entity out of solid obstacles."""
        for obs in self.obstacles:
            dx = entity.world_x - obs.world_x
            dy = entity.world_y - obs.world_y
            dist = math.sqrt(dx * dx + dy * dy)
            min_dist = getattr(entity, 'radius', 10) + obs.radius
            if dist < min_dist and dist > 0:
                push_dist = min_dist - dist
                entity.world_x += (dx / dist) * push_dist
                entity.world_y += (dy / dist) * push_dist

    def _on_enemy_killed(self, enemy):
        """Handle enemy death: score, combo, drops."""
        xp = getattr(enemy, 'xp_drop', ENEMY_XP_DROP)

        # Score with combo
        self.combo += 1
        self.combo = min(self.combo, COMBO_MAX)
        self.combo_timer = COMBO_WINDOW
        points = 10 * self.combo
        self.score += points
        if self.player:
            self.player.enemies_killed += 1

        # Combo text
        if self.combo > 1:
            self.particles.add_combo_text(enemy.world_x, enemy.world_y, self.combo)

        # Death particles and Splatter
        death_color = getattr(enemy, 'color', (200, 60, 60))
        if isinstance(death_color, list):
            death_color = [death_color]
        d_color = random.choice(death_color) if isinstance(death_color, list) else death_color
        self.particles.emit_death(enemy.world_x, enemy.world_y, death_color)
        self.world.add_splatter(enemy.world_x, enemy.world_y, d_color)

        # Hit stop for juice
        self.hit_stop_frames = 2
        self.camera.shake(5)
        if sound.audio: sound.audio.play("death")

        # Drop XP orb
        orb = XPOrb(enemy.world_x, enemy.world_y, xp)
        self.xp_orbs.add(orb)

        # Drop food
        food = Food(enemy.world_x + random.uniform(-15, 15),
                    enemy.world_y + random.uniform(-15, 15))
        self.foods.add(food)

        # Power-up drop chance
        is_boss = isinstance(enemy, BossGerm)
        if is_boss:
            # Boss guaranteed power-up drops
            for _ in range(POWERUP_BOSS_DROPS):
                pu = PowerUp(
                    enemy.world_x + random.uniform(-30, 30),
                    enemy.world_y + random.uniform(-30, 30)
                )
                self.powerups.add(pu)

        if enemy == self.current_boss:
            # Boss-specific rewards
            pu = PowerUp(enemy.world_x, enemy.world_y, "glitch")
            self.powerups.add(pu)
            if random.random() < 0.5:
                self.pacing_state = "BLOOM"
                self.pacing_timer = 20.0
            else:
                self.pacing_state = "DORMANT"
                self.pacing_timer = 20.0
            self.current_boss = None
            self.boss_tier += 1
            self.event_cooldown = 40.0
            self.camera.shake(30)
            self.hit_stop_frames = 15
        elif random.random() < POWERUP_DROP_CHANCE:
            # Small chance for random glitch drop, otherwise regular
            type_roll = "glitch" if random.random() < 0.05 else None
            pu = PowerUp(enemy.world_x, enemy.world_y, type_roll)
            self.powerups.add(pu)

        # Lifesteal (Enzyme Drain)
        # We only heal from damage, or flat amount on kill? 
        # Standardize: projectiles heal on damage, kills give a small bonus.
        lifesteal = self.evolution.get_lifesteal()
        if lifesteal > 0 and self.player:
            # Heal fraction of enemy's total health as a "kill bonus"
            heal_amt = enemy.max_health * lifesteal * 0.5
            self.player.heal(heal_amt)
            if self.evolution.heals_clones():
                for clone in self.clones:
                    clone.health = min(clone.max_health, clone.health + heal_amt * 0.5)

    def _activate_powerup(self, powerup_type):
        """Activate a power-up on the player."""
        active = ActivePowerUp(powerup_type)
        self.active_powerups.append(active)

        # Special handling for shield
        if powerup_type == "shield":
            self.player.has_shield = True
            self.player.shield_hits = active.shield_hits
        
        # Special handling for glitch
        if powerup_type == "glitch":
            self.glitch_timer = 60 # Initial burst
            if sound.audio: sound.audio.play("boss_spawn")

    def _update_difficulty(self, dt):
        """Scale difficulty over time."""
        self.difficulty_timer += dt
        if self.difficulty_timer >= 30:
            self.difficulty_timer = 0
            self.enemy_spawn_rate = max(
                ENEMY_SPAWN_RATE_MIN,
                self.enemy_spawn_rate * ENEMY_SPAWN_SCALE
            )

    def _apply_mutations(self):
        """Reapply all mutation effects after a new one is picked."""
        # Max HP bonus
        hp_bonus = self.evolution.get_max_hp_bonus()
        if self.player:
            self.player.max_health = PLAYER_MAX_HEALTH + hp_bonus
            if self.player.health > self.player.max_health:
                self.player.health = self.player.max_health

        # Aura bonus
        if self.player:
            self.player.aura_mult = self.evolution.get_aura_bonus()

    def _random_spawn_pos(self, min_dist_from_player=200):
        """Generate a random spawn position far from the player."""
        for _ in range(20):
            x = random.uniform(50, WORLD_WIDTH - 50)
            y = random.uniform(50, WORLD_HEIGHT - 50)
            if self.player is None:
                return x, y
            dx = x - self.player.world_x
            dy = y - self.player.world_y
            if math.sqrt(dx * dx + dy * dy) >= min_dist_from_player:
                return x, y
        # Fallback: just pick a random edge
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            return random.uniform(50, WORLD_WIDTH - 50), 50
        elif edge == "bottom":
            return random.uniform(50, WORLD_WIDTH - 50), WORLD_HEIGHT - 50
        elif edge == "left":
            return 50, random.uniform(50, WORLD_HEIGHT - 50)
        else:
            return WORLD_WIDTH - 50, random.uniform(50, WORLD_HEIGHT - 50)

    def _adjust_setting(self, key):
        """Handle left/right adjustment of settings."""
        idx = self.settings_index
        setting = self.settings_data[idx]
        key_name, label, val_type, value = setting
        
        if val_type == "bool":
            self.settings_data[idx][3] = not value
        elif val_type == "float":
            step = 0.05
            if key == pygame.K_LEFT:
                self.settings_data[idx][3] = max(0.0, value - step)
            else:
                self.settings_data[idx][3] = min(1.0, value + step)
        
        self._apply_settings()

    def _apply_settings(self):
        """Update game systems with new setting values."""
        import settings as _settings_module
        for key_name, label, val_type, value in self.settings_data:
            if key_name == "sfx_vol":
                # Assuming SFX_VOLUME is a module-level variable in settings or similar
                _settings_module.SFX_VOLUME = value
                if sound.audio:
                    sound.audio.master_vol = value
            elif key_name == "music_vol":
                _settings_module.MUSIC_VOLUME = value
            elif key_name == "shake":
                _settings_module.SETTING_SCREEN_SHAKE = value
            elif key_name == "scanlines":
                _settings_module.SETTING_CRT_FX = value
            elif key_name == "glitch":
                _settings_module.SETTING_GLITCH_FX = value

    def _trigger_nerve_stun(self, nerve):
        """Trigger a screen-wide stun and visual effect."""
        
        # Visual juice
        self.camera.shake(20)
        self.hit_stop_frames = 10
        self.particles.emit_divide(nerve.world_x, nerve.world_y) # Reuse divide for now
        
        # Stun all enemies on screen
        for enemy in self.enemies:
            # Check if on screen (roughly)
            sx, sy = self.camera.apply((enemy.world_x, enemy.world_y))
            if 0 < sx < SCREEN_WIDTH and 0 < sy < SCREEN_HEIGHT:
                if hasattr(enemy, 'apply_slow'):
                    enemy.apply_slow(NERVE_STUN_DURATION, 0.0)
                elif hasattr(enemy, 'stun_timer'):
                    # Fallback if stun not implemented in enemy base
                    enemy.stun_timer = NERVE_STUN_DURATION

        if sound.audio: sound.audio.play("shoot") # Reuse sound for now

    def _draw(self):
        """Draw everything based on current state."""
        if self.state == "MENU":
            self.hud.draw_menu(self.screen)

        elif self.state in ("PLAYING", "EVOLUTION_PICK"):
            # World background
            self.world.draw(self.screen, self.camera)

            # Food
            for food in self.foods:
                food.draw(self.screen, self.camera)

            # XP Orbs
            for orb in self.xp_orbs:
                orb.draw(self.screen, self.camera)

            # Power-up items on ground
            for pu in self.powerups:
                pu.draw(self.screen, self.camera)

            # Hazards
            for hazard in self.hazards:
                hazard.draw(self.screen, self.camera)

            # Enemies
            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera)

            # Clones
            for clone in self.clones:
                clone.draw(self.screen, self.camera)

            # Player
            if self.player.alive:
                # Rage aura visual
                for pu in self.active_powerups:
                    if pu.powerup_type == "rage":
                        self.player.draw_rage_aura(self.screen, self.camera)
                        break
                self.player.draw(self.screen, self.camera)

            # ── Elite Hunt Warning ──
            if self.elite_hunt_target and self.elite_hunt_target.alive():
                e = self.elite_hunt_target
                sx, sy = self.camera.apply((e.world_x, e.world_y))
                # Only show if off-screen
                if sx < 0 or sx > SCREEN_WIDTH or sy < 0 or sy > SCREEN_HEIGHT:
                    # Calculate edge position
                    edge_x = max(20, min(SCREEN_WIDTH - 20, sx))
                    edge_y = max(20, min(SCREEN_HEIGHT - 20, sy))
                    # Pulsing red indicator
                    alpha = int(127 + 127 * math.sin(self.game_time * 10))
                    color = (255, 0, 0, alpha)
                    warn_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
                    pygame.draw.circle(warn_surf, color, (20, 20), 15, 3)
                    pygame.draw.polygon(warn_surf, color, [(20, 5), (35, 30), (5, 30)]) # Warning triangle
                    self.screen.blit(warn_surf, (edge_x - 20, edge_y - 20))

            # Projectiles
            for proj in self.projectiles:
                proj.draw(self.screen, self.camera)
            for bp in self.boss_projectiles:
                bp.draw(self.screen, self.camera)
                
            for ep in self.enemy_projectiles:
                ep.draw(self.screen, self.camera)
                
            # Items
            for item in self.items:
                item.draw(self.screen, self.camera)

            # Obstacles
            for obs in self.obstacles:
                obs.draw(self.screen, self.camera)

            # Alcohol Zones (background glow)
            for zone in self.alcohol_zones:
                zone.draw(self.screen, self.camera)

            # Alcohol Waves (entities)
            for wave in self.alcohol_waves:
                wave.draw(self.screen, self.camera)

            # Burst Visuals
            for b_x, b_y, radius, timer in self.burst_visuals:
                # timer starts at 0.5
                progress = 1.0 - (timer / 0.5)
                # Expanding ring
                sx, sy = self.camera.apply((b_x, b_y))
                r = int(radius * progress)
                alpha = int(200 * (1.0 - progress))
                # Draw ring
                if r > 0:
                    temp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(temp_surf, (255, 150, 50, alpha), (radius, radius), r, 4)
                    # Outer faint glow
                    pygame.draw.circle(temp_surf, (255, 100, 30, alpha // 2), (radius, radius), r + 5, 2)
                    self.screen.blit(temp_surf, (sx - radius, sy - radius))

            # Particles
            self.particles.draw(self.screen, self.camera)

            # ── HORROR LIGHTING OVERLAY ──
            
            # Create a black surface with alpha (Deep crimson/brown bio-darkness)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((12, 4, 4, LIGHT_DARKNESS_ALPHA))
            
            # Punch a hole for the player's light
            if self.player.alive:
                sx, sy = self.camera.apply(self.player.pos)
                sx, sy = int(sx), int(sy)
                
                # Dynamic lighting: Shrink radius based on player health
                hp_ratio = self.player.health / self.player.max_health
                base_r = LIGHT_MIN_RADIUS + (LIGHT_RADIUS_PLAYER - LIGHT_MIN_RADIUS) * hp_ratio
                
                # Organic light pulsing / flickering
                pulse = math.sin(self.game_time * 4.0) * 15 + math.sin(self.game_time * 1.5) * 10
                flicker = random.uniform(-3, 3)
                light_r = int(base_r + pulse + flicker)
                
                # We use BLEND_RGBA_SUB to cut a hole. Subtracting alpha works best.
                # light_surf will hold the amount of alpha we want to REMOVE from the overlay
                light_surf = pygame.Surface((light_r * 2, light_r * 2), pygame.SRCALPHA)
                light_surf.fill((0, 0, 0, 0)) # Start with 0 subtraction
                
                # Draw concentric circles defining how much darkness to subtract
                steps = 30
                for i in range(steps):
                    r = light_r - int((light_r / steps) * i)
                    ratio = i / steps
                    # At center (ratio=1.0), subtract 255 (full brightness)
                    # At edge (ratio=0), subtract 0 (full darkness)
                    alpha_sub = int(255 * (ratio**2.0))  # Smooth ease-in curve
                    pygame.draw.circle(light_surf, (0, 0, 0, alpha_sub), (light_r, light_r), r)

                # Add a subtle greenish/cyan hue to the player's light (drawn normally ON the overlay later, or blit as ADD)
                hue_surf = pygame.Surface((light_r * 2, light_r * 2), pygame.SRCALPHA)
                for i in range(8):
                    r = int(light_r * 0.25) - int((light_r * 0.25 / 8) * i)
                    hue_alpha = int(12 * (i / 8))
                    pygame.draw.circle(hue_surf, (80, 255, 140, hue_alpha), (light_r, light_r), r)

                # Clones emit faint light (adds to subtraction pool)
                for clone in self.clones:
                    cx, cy = self.camera.apply(clone.pos)
                    r_clone = int(clone.radius * 3)
                    
                    rel_x = int(cx - (sx - light_r))
                    rel_y = int(cy - (sy - light_r))
                    
                    if 0 <= rel_x <= light_r * 2 and 0 <= rel_y <= light_r * 2:
                        pygame.draw.circle(light_surf, (0, 0, 0, 180), (rel_x, rel_y), r_clone)
                
                # SUBTRACT the light_surf alpha from the overlay
                overlay.blit(light_surf, (sx - light_r, sy - light_r), special_flags=pygame.BLEND_RGBA_SUB)
                
                # ADD the color tint on top
                overlay.blit(hue_surf, (sx - light_r, sy - light_r), special_flags=pygame.BLEND_RGBA_ADD)

                # If boss is spawned, it has a menacing red glow
                if self.current_boss and self.current_boss.alive():
                    bsx, bsy = self.camera.apply((self.current_boss.world_x, self.current_boss.world_y))
                    
                    # Boss light throb
                    boss_pulse = math.sin(self.game_time * 5.0) * 20
                    boss_r = int(self.current_boss.radius * 3.5 + boss_pulse)
                    
                    boss_light = pygame.Surface((boss_r * 2, boss_r * 2), pygame.SRCALPHA)
                    boss_light.fill((0, 0, 0, 0))
                    # Cut out hole by subtracting alpha
                    steps = 20
                    for i in range(steps):
                        r = boss_r - int((boss_r / steps) * i)
                        ratio = i / steps
                        alpha_sub = int(200 * (ratio**2.0))
                        pygame.draw.circle(boss_light, (0, 0, 0, alpha_sub), (boss_r, boss_r), r)
                        
                    overlay.blit(boss_light, (int(bsx) - boss_r, int(bsy) - boss_r), special_flags=pygame.BLEND_RGBA_SUB)
                    
                    # Add an intense red core tint over the cut hole
                    tint = pygame.Surface((boss_r * 2, boss_r * 2), pygame.SRCALPHA)
                    for i in range(8):
                        r = int(boss_r * 0.6) - int((boss_r * 0.6 / 8) * i)
                        tint_alpha = int(40 * (i / 8))
                        pygame.draw.circle(tint, (180, 10, 10, tint_alpha), (boss_r, boss_r), r)
                    overlay.blit(tint, (int(bsx) - boss_r, int(bsy) - boss_r), special_flags=pygame.BLEND_RGBA_ADD)

            # Heartbeat sound when player health is very low
            import time
            if self.player.health > 0 and self.player.health <= 30:
                if self.state == "PLAYING" and getattr(self, '_last_heartbeat', 0) < time.time() - 1.0:
                    if sound.audio: sound.audio.play("heartbeat")
                    self._last_heartbeat = time.time()

            self.screen.blit(overlay, (0, 0))

            # HUD
            boss_ref = None
            if self.current_boss and self.current_boss in self.enemies:
                boss_ref = self.current_boss

            self.hud.draw_playing(self.screen, self)

            # Evolution card overlay
            if self.state == "EVOLUTION_PICK":
                self.evolution.draw_cards(self.screen)

            # Boss Splash Intro
            if self.state == "BOSS_INTRO":
                self.hud.draw_boss_intro(self.screen, self.boss_intro_name, self.boss_intro_timer)

            # ── COOL EXTRA: GLITCH EFFECT ──
            has_glitch_pu = any(pu.powerup_type == "glitch" for pu in self.active_powerups)
            if (self.glitch_timer > 0 or has_glitch_pu) and _settings_module.SETTING_GLITCH_FX:
                if self.glitch_timer > 0: self.glitch_timer -= 1
                
                # Intensify if it's the powerup
                strength = 1.0 if not has_glitch_pu else 2.5
                if random.random() < 0.15 * strength:
                    glitch_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    # Shift pixels or draw random colored rectangles for "digital artifacts"
                    if self.glitch_timer % 3 == 0:
                        for _ in range(5):
                            rh = random.randint(2, 20)
                            ry = random.randint(0, SCREEN_HEIGHT - rh)
                            rx = random.randint(-20, 20)
                            # Blit a strip of the screen with an offset
                            strip = self.screen.subsurface((0, ry, SCREEN_WIDTH, rh)).copy()
                            self.screen.blit(strip, (rx, ry))
                        # Flash a subtle red tint
                        glitch_surf.fill((150, 20, 20, 40))
                        self.screen.blit(glitch_surf, (0, 0))

            # --- AMBUSH FLASH ---
            if self.pacing_state == "AMBUSH" and int(self.game_time * 8) % 2 == 0:
                flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash.fill((255, 0, 0, 60))
                self.screen.blit(flash, (0, 0))

        elif self.state == "SETTINGS":
            # Draw game background if possible
            if self.world and self.player:
                self.world.draw(self.screen, self.camera)
            self.hud.draw_settings(self.screen, self.settings_index, self.settings_data)

        elif self.state == "GAME_OVER":
            # Keep the last game frame visible under the overlay
            self.world.draw(self.screen, self.camera)
            for obs in self.obstacles:
                obs.draw(self.screen, self.camera)
            for food in self.foods:
                food.draw(self.screen, self.camera)
            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera)
            self.particles.draw(self.screen, self.camera)

            self.hud.draw_game_over(
                self.screen, self.score, self.game_time,
                self.player.enemies_killed, self.clones_made,
                self.evolution.current_level
            )

    # ═══════════════════════════════════════════════════════════════════
    #  INVENTORY & SKILLS
    # ═══════════════════════════════════════════════════════════════════

    def _update_item_spawning(self, dt):
        """Spawn inventory items periodically."""
        self.item_spawn_timer += dt
        if self.item_spawn_timer >= ITEM_SPAWN_RATE:
            self.item_spawn_timer = 0
            # Spawn at random edge of screen or random location near player
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(400, 700)
            sx = self.player.world_x + math.cos(angle) * dist
            sy = self.player.world_y + math.sin(angle) * dist
            self.items.add(Item(sx, sy))

    def _trigger_burst_skill(self):
        """Manually trigger the Cytotoxic Burst skill."""
        if not self.evolution.get_mutation_level("cytotoxic_burst"):
            return
            
        # Compute burst parameters from mutation level
        level = self.evolution.get_mutation_level("cytotoxic_burst")
        radius = BURST_BASE_RADIUS + (level - 1) * 40
        damage = BURST_BASE_DAMAGE + (level - 1) * 15
        
        # Check cooldown in player
        if self.player.trigger_burst(int(BURST_COOLDOWN * FPS)):
            # Visual
            self.burst_visuals.append([self.player.world_x, self.player.world_y, radius, 0.5]) # x, y, r, timer
            self.camera.shake(8)
            if sound.audio: sound.audio.play("explode") # Updated to use explode sound
            
            # Collision check
            for enemy in list(self.enemies) + list(self.alcohol_waves):
                dx = enemy.world_x - self.player.world_x
                dy = enemy.world_y - self.player.world_y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < radius + enemy.radius:
                    enemy.take_damage(damage * self.player.damage_mult)
                    self.particles.emit_hit(enemy.world_x, enemy.world_y)
                    # Knockback at level 3
                    if level >= 3:
                        enemy.world_x += (dx/dist) * 50 if dist > 0 else 0
                        enemy.world_y += (dy/dist) * 50 if dist > 0 else 0

    def _use_inventory_item(self, slot_index):
        """Apply the effect of an item from inventory."""
        item_type = self.player.use_item(slot_index)
        if not item_type:
            return
            
        if sound.audio: sound.audio.play("powerup")
        
        if item_type == "adrenaline":
            # Temporary massive buff
            self._activate_powerup("speed")
            self._activate_powerup("rage")
            self.particles.emit_powerup(self.player.world_x, self.player.world_y, (255, 50, 50))
        elif item_type == "grenade":
            # Huge explosion
            self.camera.shake(20)
            self.glitch_timer = 20
            # Damage all enemies on screen basically
            for enemy in list(self.enemies) + list(self.alcohol_waves):
                dx = enemy.world_x - self.player.world_x
                dy = enemy.world_y - self.player.world_y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 400: # Grenade range
                    enemy.take_damage(100)
                    self.particles.emit_hit(enemy.world_x, enemy.world_y)
        elif item_type == "nanobots":
            self._activate_powerup("regen")
        elif item_type == "flare":
            # Visual flare effect (optional flare logic)
            self.particles.emit_powerup(self.player.world_x, self.player.world_y, (255, 200, 50))
            # revealing handled in radar drawing if we want, currently just juice
