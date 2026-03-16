"""
world.py — World map: skin-textured background, bio-film zones, ambient life
Redesigned for clean rendering — no black gaps, authentic organic feel.
"""
import pygame
import random
import math
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BG_SKIN, COLOR_BG_SKIN_LIGHT, COLOR_BG_SKIN_DARK,
    COLOR_BG_VEIN_BLUE, COLOR_BG_VEIN_RED, COLOR_BG_WOUND, COLOR_BG_FOLLICLE,
    COLOR_BG_CYST, COLOR_BG_CRYSTAL,
    NERVE_RADIUS, NERVE_SPAWN_COUNT, COLOR_NERVE, COLOR_NERVE_GLOW
)


class AmbientMicrobe:
    """Tiny background microorganism for atmosphere only (non-interactive)."""

    def __init__(self):
        self.x = random.uniform(0, WORLD_WIDTH)
        self.y = random.uniform(0, WORLD_HEIGHT)
        self.size = random.uniform(1.5, 3.5)
        self.speed = random.uniform(0.08, 0.3)
        self.angle = random.uniform(0, math.pi * 2)
        self.turn_timer = random.randint(60, 200)
        self.alpha = random.randint(20, 50)
        self.color = random.choice([
            (90, 70, 55),
            (70, 60, 50),
            (80, 65, 48),
            (55, 85, 65),
            (100, 80, 60),
        ])
        self.wobble_phase = random.uniform(0, math.pi * 2)

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.wobble_phase += 0.03
        self.turn_timer -= 1
        if self.turn_timer <= 0:
            self.angle += random.uniform(-0.5, 0.5)
            self.turn_timer = random.randint(60, 200)
        # Wrap around
        self.x %= WORLD_WIDTH
        self.y %= WORLD_HEIGHT

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.x, self.y))
        sx, sy = int(sx), int(sy)
        if -5 < sx < SCREEN_WIDTH + 5 and -5 < sy < SCREEN_HEIGHT + 5:
            s = max(1, int(self.size + 0.5 * math.sin(self.wobble_phase)))
            # Draw directly — skip per-particle SRCALPHA surfaces for speed
            pygame.draw.circle(surface, self.color, (sx, sy), s)


class TissueObstacle(pygame.sprite.Sprite):
    """A solid map obstacle (like cartilage or dense tissue) that stops movement."""
    
    def __init__(self, x, y, radius):
        super().__init__()
        self.world_x = float(x)
        self.world_y = float(y)
        self.radius = radius
        # Visual setup
        self.wobble_points = [random.uniform(-0.1, 0.1) for _ in range(12)]
        self.color = (130, 90, 70)  # Dense tissue color
        self.edge_color = (160, 110, 80)
        
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        
    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)
        
        # Don't draw if heavily off-screen
        if sx < -self.radius or sx > SCREEN_WIDTH + self.radius or sy < -self.radius or sy > SCREEN_HEIGHT + self.radius:
            return
            
        num_points = len(self.wobble_points)
        points = []
        for i in range(num_points):
            angle = (math.pi * 2 / num_points) * i
            r = self.radius * (1.0 + self.wobble_points[i])
            px = sx + math.cos(angle) * r
            py = sy + math.sin(angle) * r
            points.append((px, py))
            
        if len(points) >= 3:
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, self.edge_color, points, max(2, int(self.radius * 0.1)))
            
            # Draw core details
            pygame.draw.circle(surface, (110, 70, 50), (sx, sy), int(self.radius * 0.5))
            pygame.draw.circle(surface, (140, 100, 80), (sx, sy), int(self.radius * 0.3))


class World:
    """Manages background rendering, bio-film zones, and ambient life."""

    def __init__(self):
        # Biome storage (x, y, radius, properties...)
        self.wounds = []
        self.veins = []
        self.follicles = []
        self.cysts = []
        self.crystals = []
        self.nerves = []  # New: Nerve Ending interactables
        self._generate_biome_data()
        self._generate_nerves()

        # Pre-render skin texture background using biome data
        self.tile_size = 80
        self.background = self._generate_background()

        # Bio-film tracking grid
        self.biofilm_grid_size = 40
        cols = WORLD_WIDTH // self.biofilm_grid_size + 1
        rows = WORLD_HEIGHT // self.biofilm_grid_size + 1
        self.biofilm = [[0 for _ in range(cols)] for _ in range(rows)]

        # Pre-build a reusable tinted cell surface for bio-film
        self.biofilm_cell = pygame.Surface(
            (self.biofilm_grid_size, self.biofilm_grid_size), pygame.SRCALPHA
        )

        # Ambient life
        self.ambient_microbes = [AmbientMicrobe() for _ in range(80)]

    def _generate_biome_data(self):
        """Pre-calculate coordinates and sizes for all biomes for physics/spawning queries."""
        # 1. Wounds / Scabs
        for _ in range(8):
            wx = random.uniform(200, WORLD_WIDTH - 200)
            wy = random.uniform(200, WORLD_HEIGHT - 200)
            base_r = random.uniform(150, 400)
            clusters = []
            for _ in range(30):
                ox = wx + random.uniform(-base_r, base_r) * 0.7
                oy = wy + random.uniform(-base_r, base_r) * 0.7
                r = random.uniform(40, 100)
                clusters.append((ox, oy, r))
            self.wounds.append({"center": (wx, wy), "radius": base_r, "clusters": clusters})

        # 2. Veins
        for _ in range(12):
            vy = random.uniform(0, WORLD_HEIGHT)
            vx = random.uniform(0, WORLD_WIDTH)
            color = random.choice([COLOR_BG_VEIN_BLUE, COLOR_BG_VEIN_RED])
            thickness = random.randint(30, 80)
            points = [(vx, vy)]
            angle = random.uniform(0, math.pi * 2)
            for _ in range(6):
                angle += random.uniform(-0.5, 0.5)
                dist = random.uniform(300, 800)
                vx += math.cos(angle) * dist
                vy += math.sin(angle) * dist
                points.append((vx, vy))
            self.veins.append({"points": points, "thickness": thickness, "color": color})
            
        # 3. Cysts (Glowing clusters)
        for _ in range(6):
            cx = random.uniform(300, WORLD_WIDTH - 300)
            cy = random.uniform(300, WORLD_HEIGHT - 300)
            r = random.uniform(80, 180)
            blobs = []
            for _ in range(12):
                bx = cx + random.uniform(-r, r) * 0.6
                by = cy + random.uniform(-r, r) * 0.6
                br = random.uniform(15, 40)
                blobs.append((bx, by, br))
            self.cysts.append({"center": (cx, cy), "radius": r, "blobs": blobs})

        # 4. Crystals (Geometric growth)
        for _ in range(15):
            cx = random.uniform(200, WORLD_WIDTH - 200)
            cy = random.uniform(200, WORLD_HEIGHT - 200)
            points = []
            sides = random.randint(3, 6)
            size = random.uniform(30, 70)
            for i in range(sides):
                angle = (i / sides) * math.pi * 2
                px = cx + math.cos(angle) * size
                py = cy + math.sin(angle) * size
                points.append((px, py))
            self.crystals.append({"points": points, "color": COLOR_BG_CRYSTAL})

    def _generate_nerves(self):
        """Generate Bio-Electric Nerve Endings across the map."""
        for _ in range(NERVE_SPAWN_COUNT):
            x = random.uniform(200, WORLD_WIDTH - 200)
            y = random.uniform(200, WORLD_HEIGHT - 200)
            self.nerves.append(NerveEnding(x, y))

        # 3. Follicles
        for _ in range(30):
            fx = random.uniform(100, WORLD_WIDTH - 100)
            fy = random.uniform(100, WORLD_HEIGHT - 100)
            r = random.uniform(40, 90)
            self.follicles.append((fx, fy, r))

    def _generate_background(self):
        """Generate a procedural skin-texture background surface using pre-calculated biome data."""
        bg = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        bg.fill(COLOR_BG_SKIN)

        for x in range(0, WORLD_WIDTH, self.tile_size):
            for y in range(0, WORLD_HEIGHT, self.tile_size):
                var = random.randint(-6, 6)
                color = tuple(max(0, min(255, c + var)) for c in COLOR_BG_SKIN)
                rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                pygame.draw.rect(bg, color, rect)
                pygame.draw.rect(bg, COLOR_BG_SKIN_DARK, rect, 1)

                if random.random() < 0.12:
                    px = x + random.randint(10, self.tile_size - 10)
                    py = y + random.randint(10, self.tile_size - 10)
                    pore_r = random.randint(2, 4)
                    pore_color = tuple(max(0, c - 12) for c in COLOR_BG_SKIN)
                    pygame.draw.circle(bg, pore_color, (px, py), pore_r)
                    highlight = tuple(min(255, c + 6) for c in COLOR_BG_SKIN)
                    pygame.draw.circle(bg, highlight, (px, py), pore_r + 1, 1)

                if random.random() < 0.06:
                    px = x + random.randint(5, self.tile_size - 5)
                    py = y + random.randint(5, self.tile_size - 5)
                    patch_r = random.randint(8, 18)
                    pygame.draw.circle(bg, COLOR_BG_SKIN_LIGHT, (px, py), patch_r)

        # Draw Wounds
        for wound in self.wounds:
            for ox, oy, r in wound["clusters"]:
                wound_color = tuple(min(255, max(0, c + random.randint(-10, 10))) for c in COLOR_BG_WOUND)
                pygame.draw.circle(bg, wound_color, (int(ox), int(oy)), int(r))
                if random.random() < 0.3:
                    pygame.draw.circle(bg, (40, 10, 10), (int(ox), int(oy)), int(r * 0.5))

        # Draw Veins
        for vein in self.veins:
            points = vein["points"]
            thickness = vein["thickness"]
            color = vein["color"]
            if len(points) >= 2:
                pygame.draw.lines(bg, color, False, [(int(p[0]), int(p[1])) for p in points], thickness)
                inner_color = tuple(min(255, c + 15) for c in color)
                pygame.draw.lines(bg, inner_color, False, [(int(p[0]), int(p[1])) for p in points], thickness // 2)

        # Draw Follicles
        for fx, fy, r in self.follicles:
            pygame.draw.circle(bg, COLOR_BG_FOLLICLE, (int(fx), int(fy)), int(r))
            pygame.draw.circle(bg, COLOR_BG_SKIN_DARK, (int(fx), int(fy)), int(r + 15), 5)
            pygame.draw.circle(bg, (5, 5, 5), (int(fx), int(fy)), int(r * 0.4))

        # Draw Cysts
        for cyst in self.cysts:
            for bx, by, br in cyst["blobs"]:
                # Layered glow
                for i in range(3):
                    alpha_r = int(br * (1.2 + i * 0.4))
                    color = (*COLOR_BG_CYST, 60 // (i + 1))
                    glow_surf = pygame.Surface((alpha_r * 2, alpha_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, color, (alpha_r, alpha_r), alpha_r)
                    bg.blit(glow_surf, (int(bx) - alpha_r, int(by) - alpha_r))
                pygame.draw.circle(bg, COLOR_BG_CYST, (int(bx), int(by)), int(br))
                pygame.draw.circle(bg, (255, 100, 200), (int(bx), int(by)), int(br * 0.5))

        # Draw Crystals
        for crys in self.crystals:
            pygame.draw.polygon(bg, crys["color"], crys["points"])
            pygame.draw.polygon(bg, (100, 200, 220), crys["points"], 2)
            # Add a small shine line
            if len(crys["points"]) >= 2:
                pygame.draw.line(bg, (255, 255, 255), crys["points"][0], crys["points"][1], 1)

        return bg

    def get_biome_at(self, x, y):
        """Returns the name of the biome at the given world coordinates."""
        # Check Follicles
        for fx, fy, r in self.follicles:
            if (x - fx)**2 + (y - fy)**2 <= (r + 15)**2:
                return "follicle"
                
        # Check Wounds
        for wound in self.wounds:
            cx, cy = wound["center"]
            br = wound["radius"]
            if cx - br <= x <= cx + br and cy - br <= y <= cy + br:
                for ox, oy, cluster_r in wound["clusters"]:
                    if (x - ox)**2 + (y - oy)**2 <= cluster_r**2:
                        return "wound"
                        
        # Check Veins
        for vein in self.veins:
            pts = vein["points"]
            thickness = vein["thickness"]
            for i in range(len(pts) - 1):
                p1x, p1y = pts[i]
                p2x, p2y = pts[i+1]
                minx, maxx = min(p1x, p2x) - thickness, max(p1x, p2x) + thickness
                miny, maxy = min(p1y, p2y) - thickness, max(p1y, p2y) + thickness
                if minx <= x <= maxx and miny <= y <= maxy:
                    length2 = (p2x - p1x)**2 + (p2y - p1y)**2
                    if length2 > 0:
                        t = max(0, min(1, ((x - p1x) * (p2x - p1x) + (y - p1y) * (p2y - p1y)) / length2))
                        if (x - (p1x + t * (p2x - p1x)))**2 + (y - (p1y + t * (p2y - p1y)))**2 <= (thickness / 2)**2:
                            return "vein"

        # Check Cysts
        for cyst in self.cysts:
            cx, cy = cyst["center"]
            r = cyst["radius"]
            if (x - cx)**2 + (y - cy)**2 <= r**2:
                return "cyst"

        # Check Crystals
        for crys in self.crystals:
            points = crys["points"]
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            if min_x <= x <= max_x and min_y <= y <= max_y:
                return "crystal"

        return "skin"

    def add_splatter(self, x, y, color):
        """Paint a permanent goop/blood stain onto the world background."""
        splat = pygame.Surface((60, 60), pygame.SRCALPHA)
        color_alpha = (*color[:3], 90)  # Semi-transparent stain
        
        # Draw 4-8 random circles to form a splat
        for _ in range(random.randint(4, 8)):
            ox = random.uniform(10, 50)
            oy = random.uniform(10, 50)
            r = random.randint(3, 10)
            pygame.draw.circle(splat, color_alpha, (int(ox), int(oy)), r)
            
        # Draw a brighter, smaller core for some drops
        for _ in range(random.randint(1, 3)):
            ox = random.uniform(20, 40)
            oy = random.uniform(20, 40)
            r = random.randint(2, 4)
            pygame.draw.circle(splat, color, (int(ox), int(oy)), r)

        self.background.blit(splat, (int(x) - 30, int(y) - 30))

    def update(self, player_pos):
        """Update bio-film and ambient microbes."""
        gx = int(player_pos[0] // self.biofilm_grid_size)
        gy = int(player_pos[1] // self.biofilm_grid_size)
        rows = len(self.biofilm)
        cols = len(self.biofilm[0]) if rows > 0 else 0

        # Mark cells around player
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = gx + dx, gy + dy
                if 0 <= ny < rows and 0 <= nx < cols:
                    if self.biofilm[ny][nx] < 255:
                        self.biofilm[ny][nx] = min(255, self.biofilm[ny][nx] + 2)

        for m in self.ambient_microbes:
            m.update()
            
        for nerve in self.nerves:
            nerve.update()

    def draw(self, surface, camera):
        """Draw the world background, bio-film, and ambient life."""
        # ── Fill screen with base color first (prevents any black gaps) ──
        surface.fill(COLOR_BG_SKIN)

        # ── Blit background with camera offset ──
        # Calculate the source rect on the world background
        ox = int(camera.offset.x + camera.shake_offset.x)
        oy = int(camera.offset.y + camera.shake_offset.y)

        # Clamp source rect to valid background area
        src_x = max(0, ox)
        src_y = max(0, oy)
        src_w = min(SCREEN_WIDTH, WORLD_WIDTH - src_x)
        src_h = min(SCREEN_HEIGHT, WORLD_HEIGHT - src_y)

        # Destination offset (if camera goes before 0)
        dst_x = max(0, -ox)
        dst_y = max(0, -oy)

        if src_w > 0 and src_h > 0:
            source_rect = pygame.Rect(src_x, src_y, src_w, src_h)
            surface.blit(self.background, (dst_x, dst_y), source_rect)

        # ── Bio-film overlay ──
        self._draw_biofilm(surface, camera)

        # ── Ambient microbes ──
        for m in self.ambient_microbes:
            m.draw(surface, camera)
            
        # ── Nerve endings ──
        for nerve in self.nerves:
            nerve.draw(surface, camera)

    def _draw_biofilm(self, surface, camera):
        """Draw green bio-film overlay on visited areas."""
        gs = self.biofilm_grid_size
        ox = int(camera.offset.x + camera.shake_offset.x)
        oy = int(camera.offset.y + camera.shake_offset.y)

        start_gx = max(0, ox // gs)
        start_gy = max(0, oy // gs)
        end_gx = min(len(self.biofilm[0]), (ox + SCREEN_WIDTH) // gs + 2)
        end_gy = min(len(self.biofilm), (oy + SCREEN_HEIGHT) // gs + 2)

        for gy in range(start_gy, end_gy):
            for gx in range(start_gx, end_gx):
                intensity = self.biofilm[gy][gx]
                if intensity > 15:
                    alpha = min(35, intensity // 7)
                    sx = gx * gs - ox
                    sy = gy * gs - oy
                    # Reuse the one surface, just refill
                    self.biofilm_cell.fill((50, 180, 90, alpha))
                    surface.blit(self.biofilm_cell, (sx, sy))

    def get_minimap_data(self):
        return self.biofilm

class NerveEnding:
    """A bio-electric node that causes a screen-wide stun when triggered."""
    def __init__(self, x, y):
        self.world_x = x
        self.world_y = y
        self.radius = NERVE_RADIUS
        self.pulse = 0
        self.active = True
        self.triggered = False
        self.cooldown = 0
        
    def update(self):
        self.pulse += 0.1
        if self.cooldown > 0:
            self.cooldown -= 1
            if self.cooldown == 0:
                self.active = True
                self.triggered = False

    def trigger(self):
        if self.active:
            self.active = False
            self.triggered = True
            self.cooldown = 600 # 25 second cooldown
            return True
        return False

    def draw(self, surface, camera):
        sx, sy = camera.apply((self.world_x, self.world_y))
        sx, sy = int(sx), int(sy)
        
        if not self.active:
            pygame.draw.circle(surface, (40, 40, 30), (sx, sy), self.radius)
            return

        glow_r = int(self.radius * (1.5 + 0.3 * math.sin(self.pulse)))
        pygame.draw.circle(surface, COLOR_NERVE_GLOW, (sx, sy), glow_r)
        
        pygame.draw.circle(surface, COLOR_NERVE, (sx, sy), self.radius, 2)
        core_r = int(self.radius * 0.5 + random.uniform(-2, 2))
        pygame.draw.circle(surface, (255, 255, 200), (sx, sy), max(1, core_r))
