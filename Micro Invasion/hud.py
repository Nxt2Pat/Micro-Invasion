"""
hud.py — Retro-Nostalgia HUD
Authentic retro feel through pixel-art style bars, warm colors, and clean design.
No forced CRT post-processing — the nostalgia comes from the design itself.
"""
import pygame
import math
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WORLD_WIDTH, WORLD_HEIGHT,
    COLOR_UI_BG, COLOR_UI_TEXT, COLOR_UI_TEXT_DIM, COLOR_UI_WHITE,
    COLOR_UI_HEALTH, COLOR_UI_HEALTH_BG,
    COLOR_UI_ENERGY, COLOR_UI_ENERGY_BG,
    COLOR_UI_XP, COLOR_UI_XP_BG,
    COLOR_UI_COMBO, COLOR_UI_TITLE,
    PLAYER_MAX_HEALTH, PLAYER_MAX_ENERGY,
    ITEM_TYPES, FPS
)


class HUD:
    """Retro-style heads-up display — nostalgia through design, not filters."""

    def __init__(self):
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.font_tiny = None
        self.font_title = None
        self._initialized = False

    def _init(self):
        """Lazy initialization of fonts."""
        if self._initialized:
            return
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_tiny = pygame.font.Font(None, 18)
        self.font_title = pygame.font.Font(None, 72)
        self._initialized = True

    def draw_playing(self, surface, game):
        """Draw the full in-game HUD using the game object."""
        self._init()
        
        if not game.player:
            return

        # Extract variables from game object
        player = game.player
        game_time = game.game_time
        score = game.score
        combo = game.combo
        evolution_sys = game.evolution
        active_powerups = game.active_powerups
        enemies = game.enemies
        foods = game.foods
        hazards = game.hazards
        clones = game.clones
        boss = game.current_boss if game.current_boss in game.enemies else None

        # ── Status bars (top-left) ──
        bar_x = 15
        bar_y = 12
        bar_w = 180
        bar_h = 12
        spacing = 20

        # Health bar
        self._draw_bar(surface, bar_x, bar_y, bar_w, bar_h,
                       player.health, player.max_health,
                       COLOR_UI_HEALTH, COLOR_UI_HEALTH_BG, "HP")
        # Energy bar
        self._draw_bar(surface, bar_x, bar_y + spacing, bar_w, bar_h,
                       player.energy, player.max_energy,
                       COLOR_UI_ENERGY, COLOR_UI_ENERGY_BG, "EN")
        # XP bar
        self._draw_bar(surface, bar_x, bar_y + spacing * 2, bar_w, bar_h,
                       evolution_sys.xp_progress * 100, 100,
                       COLOR_UI_XP, COLOR_UI_XP_BG,
                       f"Level {evolution_sys.current_level}")

        # Clone count
        clone_text = self.font_tiny.render(f"Clones: {len(clones)}", True, COLOR_UI_TEXT)
        surface.blit(clone_text, (bar_x, bar_y + spacing * 3 + 2))

        # ── Survival Timer (top-center) ──
        minutes = int(game_time) // 60
        seconds = int(game_time) % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        time_surf = self.font_medium.render(time_str, True, COLOR_UI_TEXT)
        # Shadow for readability
        time_shadow = self.font_medium.render(time_str, True, (15, 30, 15))
        time_rect = time_surf.get_rect(center=(SCREEN_WIDTH // 2, 18))
        surface.blit(time_shadow, time_rect.move(1, 1))
        surface.blit(time_surf, time_rect)
        
        # ── Event Status (below timer) ──
        event_label = ""
        event_color = (255, 255, 255)
        if game.pacing_state == "AMBUSH":
            event_label = "🚨 IMMUNE RESPONSE 🚨"
            event_color = (255, 50, 50) # Bright red
        elif game.pacing_state == "BLOOM":
            event_label = "✨ NUTRIENT BLOOM ✨"
            event_color = (100, 255, 150) # Soft green
        elif game.pacing_state == "DORMANT":
            event_label = "-- RECOVERY --"
            event_color = (150, 150, 180) # Grey-blue
        elif game.elite_hunt_target and game.elite_hunt_target.alive():
             event_label = "👁️ ELITE PURSUIT 👁️"
             event_color = (255, 100, 0) # Orange
        
        if event_label:
            # Flash effect
            if (int(game.game_time * 5) % 2 == 0):
                ev_surf = self.font_small.render(event_label, True, event_color)
                ev_rect = ev_surf.get_rect(center=(SCREEN_WIDTH // 2, 45))
                surface.blit(ev_surf, ev_rect)

        # ── Score (top-right) ──
        score_str = f"SCORE {score}"
        score_surf = self.font_medium.render(score_str, True, COLOR_UI_TEXT)
        score_rect = score_surf.get_rect(topright=(SCREEN_WIDTH - 15, 12))
        surface.blit(score_surf, score_rect)

        # ── Boss health bar ──
        if boss and boss.alive():
            self._draw_boss_bar(surface, boss)

        # ── Combo counter ──
        if combo > 1:
            self._draw_combo(surface, combo)

        # ── Active mutations (left edge) ──
        self._draw_mutations(surface, evolution_sys)

        # ── Active power-ups (right side) ──
        self._draw_active_powerups(surface, active_powerups)

        # ── Mini-map (bottom-right) ──
        self._draw_minimap(surface, player, enemies, foods, hazards, clones, game_time)
        
        # ── Inventory (bottom-center) ──
        self._draw_inventory(surface, player)
        
        # ── Burst Indicator (bottom-left) ──
        self._draw_burst_indicator(surface, game)

    def _draw_bar(self, surface, x, y, w, h, value, max_value, color, bg_color, label=""):
        """Draw a retro-style pixel status bar."""
        # Outer border (2px retro border)
        border_color = (60, 60, 50)
        pygame.draw.rect(surface, border_color, (x - 1, y - 1, w + 2, h + 2))

        # Background
        pygame.draw.rect(surface, bg_color, (x, y, w, h))

        # Fill
        fill_w = int(w * min(1.0, value / max(1, max_value)))
        if fill_w > 0:
            pygame.draw.rect(surface, color, (x, y, fill_w, h))
            # Highlight line on top (retro 3D effect)
            lighter = tuple(min(255, c + 50) for c in color[:3])
            pygame.draw.line(surface, lighter, (x, y), (x + fill_w - 1, y))
            # Shadow on bottom
            darker = tuple(max(0, c - 40) for c in color[:3])
            pygame.draw.line(surface, darker, (x, y + h - 1), (x + fill_w - 1, y + h - 1))

        # Label text
        if label:
            label_surf = self.font_tiny.render(label, True, COLOR_UI_WHITE)
            surface.blit(label_surf, (x + 3, y))

    def _draw_boss_bar(self, surface, boss):
        """Draw boss health bar at top-center."""
        bar_w = 350
        bar_h = 14
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 42

        # Label
        name_surf = self.font_small.render(f"* BOSS Lv.{boss.tier} *", True, (255, 100, 80))
        name_rect = name_surf.get_rect(center=(SCREEN_WIDTH // 2, bar_y - 10))
        surface.blit(name_surf, name_rect)

        # Bar
        pygame.draw.rect(surface, (40, 10, 10), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, (60, 15, 15), (bar_x, bar_y, bar_w, bar_h))
        fill = int(bar_w * max(0, boss.health / boss.max_health))
        if fill > 0:
            pygame.draw.rect(surface, (200, 40, 40), (bar_x, bar_y, fill, bar_h))
            pygame.draw.line(surface, (255, 80, 80), (bar_x, bar_y), (bar_x + fill - 1, bar_y))

    def _draw_combo(self, surface, combo):
        """Draw combo counter — clean retro text, no over-animated effects."""
        font = self.font_large
        text = f"x{combo} COMBO!"
        # Shadow
        shadow_surf = font.render(text, True, (60, 50, 0))
        surface.blit(shadow_surf,
                    shadow_surf.get_rect(center=(SCREEN_WIDTH // 2 + 1, SCREEN_HEIGHT - 59)))
        # Text
        combo_surf = font.render(text, True, COLOR_UI_COMBO)
        surface.blit(combo_surf,
                    combo_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))

    def _draw_mutations(self, surface, evolution_sys):
        """Draw active mutation icons along the left edge."""
        if not evolution_sys.active_mutations:
            return

        x = 10
        y = 105
        from settings import MUTATIONS

        for key, level in evolution_sys.active_mutations.items():
            if key in MUTATIONS:
                mut = MUTATIONS[key]
                # Small pixel card
                pygame.draw.rect(surface, (15, 12, 18), (x, y, 28, 28))
                pygame.draw.rect(surface, mut["color"], (x, y, 28, 28), 1)

                # Icon text
                icon_surf = self.font_small.render(mut["icon"], True, mut["color"])
                surface.blit(icon_surf, icon_surf.get_rect(center=(x + 14, y + 11)))

                # Level number
                lv_surf = self.font_tiny.render(str(level), True, COLOR_UI_WHITE)
                surface.blit(lv_surf, (x + 20, y + 17))

                y += 32

    def _draw_active_powerups(self, surface, active_powerups):
        """Draw active power-up icons with countdown bars."""
        if not active_powerups:
            return

        x = SCREEN_WIDTH - 45
        y = 45

        for pu in active_powerups:
            # Background
            pygame.draw.rect(surface, (15, 12, 18), (x, y, 32, 32))
            pygame.draw.rect(surface, pu.color, (x, y, 32, 32), 1)

            # Icon letter
            letter = pu.name[0].upper()
            icon_surf = self.font_medium.render(letter, True, pu.color)
            surface.blit(icon_surf, icon_surf.get_rect(center=(x + 16, y + 14)))

            # Timer bar below icon
            progress = pu.progress
            bar_w = int(30 * progress)
            if bar_w > 0:
                pygame.draw.rect(surface, pu.color, (x + 1, y + 29, bar_w, 2))

            y += 38

    def _draw_minimap(self, surface, player, enemies, foods, hazards, clones, game_time):
        """Draw a retro sonar mini-map in the bottom-right corner."""
        map_w = 120
        map_h = 120
        map_x = SCREEN_WIDTH - map_w - 10
        map_y = SCREEN_HEIGHT - map_h - 10
        scale_x = map_w / WORLD_WIDTH
        scale_y = map_h / WORLD_HEIGHT

        # Background with border (Dark green for military radar feel)
        pygame.draw.rect(surface, (8, 12, 8), (map_x - 1, map_y - 1, map_w + 2, map_h + 2))
        pygame.draw.rect(surface, (10, 18, 10), (map_x, map_y, map_w, map_h))
        pygame.draw.rect(surface, (40, 80, 40), (map_x, map_y, map_w, map_h), 1)

        # Radar grid lines
        pygame.draw.line(surface, (20, 40, 20), (map_x + map_w//2, map_y), (map_x + map_w//2, map_y + map_h), 1)
        pygame.draw.line(surface, (20, 40, 20), (map_x, map_y + map_h//2), (map_x + map_w, map_y + map_h//2), 1)

        # Player position
        px = map_x + int(player.world_x * scale_x)
        py = map_y + int(player.world_y * scale_y)

        # Sonar sweep
        sweep_speed = 1.5  # Radians per second (Reduced from 3.0)
        sweep_angle = (game_time * sweep_speed) % (math.pi * 2)
        
        # Draw sweeping radar line from player
        sweep_len = max(map_w, map_h)
        end_x = px + math.cos(sweep_angle) * sweep_len
        end_y = py + math.sin(sweep_angle) * sweep_len
        
        # We must clip the line to the minimap rect
        map_rect = pygame.Rect(map_x, map_y, map_w, map_h)
        # Create a surface for radar clipping
        radar_surf = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        
        # Draw scanning cone (faint green)
        cone_pts = [(int(player.world_x * scale_x), int(player.world_y * scale_y))]
        for i in range(15):
            a = sweep_angle - (i * 0.05)
            cx = cone_pts[0][0] + math.cos(a) * sweep_len
            cy = cone_pts[0][1] + math.sin(a) * sweep_len
            cone_pts.append((cx, cy))
        if len(cone_pts) > 2:
            pygame.draw.polygon(radar_surf, (50, 255, 100, 30), cone_pts)
            
        # Draw sharp sweep line
        pygame.draw.line(radar_surf, (150, 255, 180, 200), cone_pts[0], (int(end_x - map_x), int(end_y - map_y)), 1)

        def get_sonar_intensity(wx, wy):
            """Calculate brightness based on how recently the radar swept past."""
            dx = wx - player.world_x
            dy = wy - player.world_y
            if dx == 0 and dy == 0: return 1.0
            
            e_angle = math.atan2(dy, dx)
            if e_angle < 0: e_angle += math.pi * 2
            
            diff = (sweep_angle - e_angle) % (math.pi * 2)
            # 0 diff = bright, max diff = dark. Only keep tail visible.
            intensity = 1.0 - (diff / (math.pi * 1.0)) # Visible for half a rotation
            return max(0.15, intensity)  # 15% baseline visibility

        # Helper to draw fading dots
        def draw_dot(wx, wy, color, size=2, is_circle=False):
            intensity = get_sonar_intensity(wx, wy)
            # Dim the color by intensity
            dim_color = (int(color[0] * intensity), int(color[1] * intensity), int(color[2] * intensity))
            dx = int(wx * scale_x)
            dy = int(wy * scale_y)
            if 0 <= dx < map_w and 0 <= dy < map_h:
                if is_circle:
                    pygame.draw.circle(radar_surf, dim_color, (dx, dy), size)
                else:
                    pygame.draw.rect(radar_surf, dim_color, (dx - size//2, dy - size//2, size, size))

        # Food dots
        for food in foods:
            draw_dot(food.world_x, food.world_y, (60, 200, 100), 2)

        # Hazard zones (Soap / Water)
        for h in hazards:
            draw_dot(h.world_x, h.world_y, (200, 180, 50), 3)

        # Clones (Player's team)
        for clone in clones:
            draw_dot(clone.world_x, clone.world_y, (100, 220, 255), 2)

        # Enemy dots
        for enemy in enemies:
            if hasattr(enemy, 'tier'):  # Boss
                draw_dot(enemy.world_x, enemy.world_y, (255, 50, 50), 4, is_circle=True)
            else:
                draw_dot(enemy.world_x, enemy.world_y, (255, 80, 80), 3)

        # Player dot (Always bright)
        px_local = int(player.world_x * scale_x)
        py_local = int(player.world_y * scale_y)
        pygame.draw.circle(radar_surf, (255, 255, 255), (px_local, py_local), 3)

        # Blit the radar composition to the screen
        surface.blit(radar_surf, (map_x, map_y))

    # ─── Menu and Game Over screens ─────────────────────────────────

    def draw_menu(self, surface):
        """Draw a nostalgic title screen — clean, warm, inviting."""
        self._init()
        surface.fill((12, 10, 16))

        tick = pygame.time.get_ticks()

        # Floating background particles (subtle, organic)
        for i in range(25):
            phase = tick * 0.0005 + i * 1.7
            x = int((SCREEN_WIDTH * 0.5) + math.sin(phase * 0.7 + i) * (SCREEN_WIDTH * 0.4))
            y = int((SCREEN_HEIGHT * 0.5) + math.cos(phase * 0.5 + i * 0.8) * (SCREEN_HEIGHT * 0.4))
            r = 2 + int(math.sin(phase * 2) * 1)
            brightness = 25 + int(15 * math.sin(phase * 3))
            pygame.draw.circle(surface, (brightness, brightness + 15, brightness + 5), (x, y), r)

        # Title with shadow
        title_text = "MICRO INVASION"
        shadow_surf = self.font_title.render(title_text, True, (15, 40, 20))
        title_surf = self.font_title.render(title_text, True, COLOR_UI_TITLE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        surface.blit(shadow_surf, title_rect.move(2, 2))
        surface.blit(title_surf, title_rect)

        # Subtitle (gentle fade)
        sub_alpha = 140 + int(60 * math.sin(tick * 0.002))
        subtitle_surf = self.font_medium.render(
            "A Germ's Journey Into Human Skin", True, COLOR_UI_TEXT_DIM
        )
        subtitle_surf.set_alpha(sub_alpha)
        sub_rect = subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 45))
        surface.blit(subtitle_surf, sub_rect)

        # Decorative line
        line_y = SCREEN_HEIGHT // 3 + 70
        line_w = 200
        line_x = (SCREEN_WIDTH - line_w) // 2
        pygame.draw.line(surface, (40, 60, 40), (line_x, line_y), (line_x + line_w, line_y))

        # Controls
        y_base = SCREEN_HEIGHT // 2 + 20
        controls = [
            ("[WASD / Arrows]", "Move"),
            ("[SPACE]", "Replicate"),
            ("[1] [2] [3]", "Choose Mutation"),
            ("[F11]", "Toggle Fullscreen"),
        ]
        for i, (key, action) in enumerate(controls):
            key_surf = self.font_small.render(key, True, COLOR_UI_TEXT)
            action_surf = self.font_small.render(f"  {action}", True, COLOR_UI_TEXT_DIM)
            total_w = key_surf.get_width() + action_surf.get_width()
            kx = SCREEN_WIDTH // 2 - total_w // 2
            ky = y_base + i * 26
            surface.blit(key_surf, (kx, ky))
            surface.blit(action_surf, (kx + key_surf.get_width(), ky))

        # Start prompt (blinking)
        if (tick // 600) % 2 == 0:
            start_surf = self.font_large.render("Press ENTER to Start", True, COLOR_UI_TITLE)
            start_rect = start_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90))
            surface.blit(start_surf, start_rect)

    def draw_game_over(self, surface, score, game_time, enemies_killed, clones_made, level):
        """Draw the game over screen with stats."""
        self._init()

        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_title.render("GAME OVER", True, (200, 55, 55))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        surface.blit(title_surf, title_rect)

        # Stats
        minutes = int(game_time) // 60
        seconds = int(game_time) % 60
        stats = [
            f"Survival Time:  {minutes:02d}:{seconds:02d}",
            f"Score:  {score}",
            f"Enemies Defeated:  {enemies_killed}",
            f"Clones Created:  {clones_made}",
            f"Evolution Level:  {level}",
        ]
        y_start = SCREEN_HEIGHT // 3 + 20
        for i, stat in enumerate(stats):
            stat_surf = self.font_medium.render(stat, True, COLOR_UI_TEXT)
            stat_rect = stat_surf.get_rect(center=(SCREEN_WIDTH // 2, y_start + i * 32))
            surface.blit(stat_surf, stat_rect)

        # Restart prompt
        tick = pygame.time.get_ticks()
        if (tick // 600) % 2 == 0:
            restart_surf = self.font_large.render("Press R to Restart", True, COLOR_UI_TITLE)
            restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            surface.blit(restart_surf, restart_rect)

    def draw_settings(self, surface, selected_index, settings_data):
        """Draw a retro settings menu with sliders and toggles."""
        self._init()
        # Dark translucent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 8, 15, 230))
        surface.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_large.render("SETTINGS", True, COLOR_UI_TITLE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 70))
        surface.blit(title_surf, title_rect)

        y_base = 150
        spacing = 45

        for i, (key, label, val_type, value) in enumerate(settings_data):
            color = COLOR_UI_TEXT if i == selected_index else COLOR_UI_TEXT_DIM
            
            # Label
            label_surf = self.font_medium.render(label, True, color)
            surface.blit(label_surf, (SCREEN_WIDTH // 4, y_base + i * spacing))

            # Value visualization
            vx = SCREEN_WIDTH // 2 + 50
            vy = y_base + i * spacing + 10
            
            if val_type == "bool":
                txt = "ON" if value else "OFF"
                val_color = (100, 255, 100) if value else (255, 100, 100)
                if i != selected_index: val_color = tuple(c//2 for c in val_color)
                val_surf = self.font_medium.render(txt, True, val_color)
                surface.blit(val_surf, (vx, y_base + i * spacing))
                
            elif val_type == "float":
                # Slider
                bar_w = 150
                bar_h = 10
                pygame.draw.rect(surface, (40, 40, 40), (vx, vy, bar_w, bar_h))
                fill_w = int(bar_w * value)
                pygame.draw.rect(surface, color, (vx, vy, fill_w, bar_h))
                # Knob
                pygame.draw.circle(surface, (255, 255, 255) if i == selected_index else color, 
                                   (vx + fill_w, vy + bar_h // 2), 7)

        # Footer hint
        hint_surf = self.font_small.render("UP/DOWN: Select  LEFT/RIGHT: Adjust  ESC: Return", True, COLOR_UI_TEXT_DIM)
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 75))
        surface.blit(hint_surf, hint_rect)

        # Credits
        credit_text = "Developed by Nxt2Pat"
        credit_surf = self.font_small.render(credit_text, True, COLOR_UI_TITLE)
        credit_rect = credit_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 45))
        surface.blit(credit_surf, credit_rect)

        ai_text = "This project was developed with assistance from AI tools during programming and development."
        ai_surf = self.font_tiny.render(ai_text, True, COLOR_UI_TEXT_DIM)
        ai_rect = ai_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 35))
        surface.blit(ai_surf, ai_rect)

        legendary_text = "This Legendary game is the base game. There have been no updates to this version of the game."
        legend_surf = self.font_tiny.render(legendary_text, True, COLOR_UI_TEXT_DIM)
        legend_rect = legend_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 18))
        surface.blit(legend_surf, legend_rect)

    def draw_boss_intro(self, surface, boss_name, timer):
        """Draw a cinematic splash intro for bosses."""
        self._init()
        # Animated overlay alpha based on timer
        # timer goes from 100 to 0
        if timer > 80:
            alpha = int((100 - timer) / 20 * 180)
        elif timer > 20:
            alpha = 180
        else:
            alpha = int(timer / 20 * 180)
            
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        surface.blit(overlay, (0, 0))
        
        # Center splash text
        text_color = (255, 60, 60)
        title_surf = self.font_title.render(boss_name, True, text_color)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        
        warning_surf = self.font_medium.render("── BIOTIC THREAT DETECTED ──", True, (255, 200, 200))
        warning_rect = warning_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        
        # Scale logic for "pop-in" effect
        scale = 1.0
        if timer > 90: scale = 2.0 - (timer - 90) / 10 # Zoom in
        
        if scale != 1.0:
            title_surf = pygame.transform.smoothscale(title_surf, 
                (int(title_rect.width * scale), int(title_rect.height * scale)))
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))

        if alpha > 0:
            surface.blit(title_surf, title_rect)
            surface.blit(warning_surf, warning_rect)
    def _draw_inventory(self, surface, player):
        """Draw inventory slots at the bottom center."""
        slot_size = 36
        spacing = 10
        total_w = (slot_size * len(player.inventory)) + (spacing * (len(player.inventory) - 1))
        start_x = (SCREEN_WIDTH - total_w) // 2
        start_y = SCREEN_HEIGHT - slot_size - 15

        for i, item_type in enumerate(player.inventory):
            x = start_x + i * (slot_size + spacing)
            y = start_y
            
            # Slot background
            rect = pygame.Rect(x, y, slot_size, slot_size)
            pygame.draw.rect(surface, (20, 30, 20), rect) # Dark green slot
            pygame.draw.rect(surface, (40, 70, 40), rect, 1) # Border
            
            # Hotkey label
            key_text = self.font_tiny.render(str(i + 1), True, (100, 150, 100))
            surface.blit(key_text, (x + 3, y + 2))
            
            if item_type:
                info = ITEM_TYPES[item_type]
                # Icon
                icon_surf = self.font_small.render(info["icon"], True, (255, 255, 255))
                surface.blit(icon_surf, icon_surf.get_rect(center=rect.center))
                # Polish: small glow dot
                pygame.draw.circle(surface, info["color"], (x + slot_size - 6, y + 6), 3)

    def _draw_burst_indicator(self, surface, game):
        """Draw the manual burst skill indicator and cooldown."""
        level = game.evolution.get_mutation_level("cytotoxic_burst")
        if level <= 0:
            return
            
        x, y = 20, SCREEN_HEIGHT - 50
        radius = 20
        
        # Background circle
        pygame.draw.circle(surface, (30, 30, 40), (x, y), radius)
        pygame.draw.circle(surface, (60, 60, 80), (x, y), radius, 1)
        
        # Burst Icon
        burst_text = self.font_medium.render("💥", True, (255, 255, 255))
        surface.blit(burst_text, burst_text.get_rect(center=(x, y)))
        
        # Cooldown overlay (dark wedge)
        if game.player.burst_cooldown > 0:
            # Simple dark overlay for now
            overlay = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (0, 0, 0, 150), (radius, radius), radius)
            surface.blit(overlay, (x - radius, y - radius))
            
        # Label
        label = self.font_tiny.render(" [J] / CLICK", True, (150, 200, 150))
        surface.blit(label, (x + radius + 5, y - 6))
