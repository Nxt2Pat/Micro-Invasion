"""
settings.py — All game constants and configuration
Micro Invasion: A retro-nostalgia germ survival game
"""
import math

# ─── Display ────────────────────────────────────────────────────────
SCREEN_WIDTH = 854   # Native 480p (16:9 widescreen)
SCREEN_HEIGHT = 480
FPS = 24             # Retro chunky frame rate
TITLE = "🦠 MICRO INVASION"

# ─── Screen Settings ──────────────────────────────────────────────────
FULLSCREEN = False

# ─── World ──────────────────────────────────────────────────────────
WORLD_WIDTH = 4000
WORLD_HEIGHT = 4000

# ─── Scary Atmosphere (Lighting) ────────────────────────────────────
LIGHT_RADIUS_PLAYER = 450    # How far the player can see
LIGHT_DARKNESS_ALPHA = 210   # 0 = bright, 255 = pitch black
LIGHT_MIN_RADIUS = 150       # Smallest radius at 0 HP

# ─── Audio Settings ──────────────────────────────────────────────────
SFX_VOLUME = 0.5
MUSIC_VOLUME = 0.4

# ─── Juice / Feedback Settings ───────────────────────────────────────
SETTING_SCREEN_SHAKE = True
SETTING_CRT_FX       = True
SETTING_GLITCH_FX    = True

# ─── Nostalgia / Retro Color Palette ────────────────────────────────
# Warm, muted tones inspired by 90s arcade & old CRT monitors

# Backgrounds
COLOR_BG_SKIN       = (45, 30, 28)          # Dark warm skin tone
COLOR_BG_SKIN_LIGHT = (60, 42, 38)          # Lighter skin cell
COLOR_BG_SKIN_DARK  = (35, 22, 20)          # Darker skin cell

# Map Landmarks / Biomes
COLOR_BG_VEIN_BLUE  = (20, 25, 45)          # Deep blue veins beneath skin
COLOR_BG_VEIN_RED   = (55, 15, 15)          # Deep red arteries
COLOR_BG_WOUND      = (70, 20, 20)          # Dark red scab/wound patches
COLOR_BG_FOLLICLE   = (15, 10, 8)           # Extremely dark hair root
COLOR_BG_CYST       = (120, 30, 90)         # Glowing Magenta cyst
COLOR_BG_CRYSTAL    = (40, 110, 130)        # Neon Teal crystalline growth
COLOR_BG_SLIME      = (40, 100, 40)         # Radioactive Green biofilm

# Player (vibrant retro green — like old Game Boy)
COLOR_PLAYER        = (80, 200, 120)
COLOR_PLAYER_GLOW   = (120, 255, 160, 80)
COLOR_PLAYER_CORE   = (180, 255, 200)

# Clones (slightly different hue)
COLOR_CLONE         = (100, 220, 150)
COLOR_CLONE_GLOW    = (140, 255, 180, 60)

# Enemy germs (retro warm colors)
COLOR_ENEMY_1       = (220, 100, 80)        # Rusty red
COLOR_ENEMY_2       = (200, 150, 60)        # Mustard yellow
COLOR_ENEMY_3       = (180, 80, 160)        # Faded purple

# White blood cell
COLOR_WBC           = (200, 210, 230)       # Cold blueish white
COLOR_WBC_GLOW      = (150, 180, 220, 60)

# Boss
COLOR_BOSS          = (180, 40, 40)         # Deep crimson
COLOR_BOSS_GLOW     = (255, 60, 60, 80)

# Food / pickups
COLOR_FOOD_ENERGY   = (100, 255, 180)       # Bright green
COLOR_FOOD_HEALTH   = (255, 120, 120)       # Soft red
COLOR_XP_ORB        = (200, 160, 255)       # Lavender purple

# Hazards
COLOR_SOAP          = (240, 240, 255, 120)  # Translucent white-blue
COLOR_WATER         = (80, 140, 220, 100)   # Translucent blue

# Power-ups
COLOR_POWERUP_SPEED = (255, 220, 60)        # Gold
COLOR_POWERUP_RAGE  = (255, 60, 60)         # Red
COLOR_POWERUP_REGEN = (60, 220, 120)        # Green
COLOR_POWERUP_SHIELD = (80, 160, 255)       # Blue
COLOR_POWERUP_MAGNET = (200, 120, 255)      # Purple

# UI colors (retro terminal / CRT feel)
COLOR_UI_BG         = (10, 8, 12, 180)      # Dark overlay
COLOR_UI_TEXT        = (200, 255, 200)       # Green terminal text
COLOR_UI_TEXT_DIM    = (100, 140, 100)       # Dimmed green
COLOR_UI_HEALTH     = (220, 60, 60)         # Red bar
COLOR_UI_HEALTH_BG  = (80, 20, 20)
COLOR_UI_ENERGY     = (60, 180, 220)        # Cyan bar
COLOR_UI_ENERGY_BG  = (20, 60, 80)
COLOR_UI_XP         = (180, 120, 255)       # Purple bar
COLOR_UI_XP_BG      = (50, 30, 80)
COLOR_UI_COMBO      = (255, 255, 100)       # Yellow combo text
COLOR_UI_WHITE      = (230, 230, 230)
COLOR_UI_TITLE      = (80, 255, 140)        # Bright retro green

# Particle colors
COLOR_PARTICLE_HIT     = [(255, 80, 60), (255, 120, 80), (255, 160, 60)]
COLOR_PARTICLE_DEATH   = [(200, 60, 60), (160, 40, 40), (120, 30, 30)]
COLOR_PARTICLE_DIVIDE  = [(80, 255, 150), (120, 255, 180), (160, 255, 200)]
COLOR_PARTICLE_FOOD    = [(100, 255, 200), (150, 255, 220), (200, 255, 240)]

# CRT / Nostalgia effects
CRT_SCANLINE_ALPHA  = 25          # Subtle scanline darkness (0-255)
CRT_VIGNETTE_STRENGTH = 0.4      # Edge darkening strength
CRT_CHROMATIC_SHIFT = 1           # Pixel offset for RGB separation
PIXEL_SCALE = 1                   # 1 = normal, 2 = chunky pixels

# ─── Player Stats ───────────────────────────────────────────────────
PLAYER_SPEED        = 5.5         # Faster base speed for better pacing
PLAYER_MAX_HEALTH   = 100
PLAYER_MAX_ENERGY   = 100
PLAYER_RADIUS       = 18
PLAYER_IFRAMES      = 45          # Invincibility frames after hit (ticks)
PLAYER_AURA_RADIUS  = 40          # Toxin aura base radius
PLAYER_AURA_DAMAGE  = 0.3         # Damage per frame to enemies in aura

# ─── Clone Stats ────────────────────────────────────────────────────
CLONE_SPEED         = 4.5
CLONE_HEALTH        = 35
CLONE_RADIUS        = 14
CLONE_ORBIT_DIST    = 60          # Distance from player
CLONE_ORBIT_SPEED   = 0.02        # Radians per frame
CLONE_ATTACK_RANGE  = 50
CLONE_ATTACK_DAMAGE = 1.5

# ─── Regular Enemy Stats ────────────────────────────────────────────
ENEMY_SPEED         = 2.8
ENEMY_HEALTH        = 30
ENEMY_RADIUS        = 15
ENEMY_DAMAGE        = 1.2         # Increased from 0.8
ENEMY_DETECTION     = 300         # Detection radius in pixels
ENEMY_WANDER_TIME   = 90          # Frames before changing direction
ENEMY_XP_DROP       = 15          # XP dropped on death

# ─── Biome Enemy Stats: Heavy (Wound) ───────────────────────────────
HEAVY_SPEED         = 1.1
HEAVY_HEALTH        = 250         # Increased from 150
HEAVY_RADIUS        = 32
HEAVY_DAMAGE        = 3.5         # Hits very hard
HEAVY_XP_DROP       = 60
HEAVY_SLOW_RADIUS   = 180
HEAVY_SLOW_FACTOR   = 0.5
HEAVY_PULL_FORCE    = 0.7

# ─── Biome Enemy Stats: Charger (Vein) ──────────────────────────────
CHARGER_SPEED       = 1.0         # Slow base speed
CHARGER_DASH_SPEED  = 7.0         # Insanely fast dash
CHARGER_HEALTH      = 20          # Squishy
CHARGER_RADIUS      = 12
CHARGER_DAMAGE      = 2.2         # Increased from 1.5
CHARGER_XP_DROP     = 25

# ─── Biome Enemy Stats: Spitter (Follicle) ──────────────────────────
SPITTER_SPEED       = 2.0         # Medium speed
SPITTER_HEALTH      = 40
SPITTER_RADIUS      = 16
SPITTER_DAMAGE      = 1.5         # Increased from 1.0
SPITTER_XP_DROP     = 30
SPITTER_RANGE       = 350         # Attack range

# ─── Exploder Germ Stats ───────────────────────────────────────────
EXPLODER_SPEED       = 4.0
EXPLODER_HEALTH      = 15
EXPLODER_RADIUS      = 12
EXPLODER_DAMAGE      = 25          # AOE explosion damage
EXPLODER_XP_DROP     = 35
EXPLODER_DETECTION   = 400
EXPLODER_FUSE_TIME   = 40          # frames before explosion
EXPLODER_AOE_RADIUS  = 120

# ─── White Blood Cell Stats ─────────────────────────────────────────
WBC_SPEED           = 3.5
WBC_HEALTH          = 80
WBC_RADIUS          = 25
WBC_DAMAGE          = 3.0         # Increased from 2.0
WBC_XP_DROP         = 40

# ─── Elite WBC Stats ────────────────────────────────────────────────
ELITE_WBC_SPEED      = 4.5
ELITE_WBC_HEALTH     = 150
ELITE_WBC_RADIUS     = 30
ELITE_WBC_DAMAGE     = 3.5
ELITE_WBC_XP_DROP    = 80
ELITE_WBC_DASH_SPEED = 12.0
ELITE_WBC_DASH_COOLDOWN = 120 # frames

# ─── Boss Stats ─────────────────────────────────────────────────────
BOSS_HEALTH         = 500
BOSS_RADIUS         = 50
BOSS_SPEED          = 2.5
BOSS_DAMAGE         = 3.0
BOSS_XP_DROP        = 200
BOSS_SPAWN_INTERVAL = 90          # Seconds between boss spawns (faster)

# ─── Food ───────────────────────────────────────────────────────────
FOOD_RADIUS         = 6
FOOD_ENERGY_AMOUNT  = 15
FOOD_HEALTH_AMOUNT  = 10
FOOD_HEALTH_CHANCE  = 0.25        # 25% chance food is health type
FOOD_SPAWN_RATE     = 0.5         # Seconds between food spawns (much faster)
FOOD_MAX_COUNT      = 100         # More food allowed on map

# ─── XP Orbs ────────────────────────────────────────────────────────
XP_ORB_RADIUS       = 5
XP_ORB_MAGNET_RANGE = 100         # Auto-attract range
XP_ORB_SPEED        = 5.0         # Attraction speed

# ─── Power-ups ──────────────────────────────────────────────────────
POWERUP_RADIUS      = 12
POWERUP_DROP_CHANCE = 0.05        # 5% from normal enemies
POWERUP_BOSS_DROPS  = 2           # Guaranteed drops from boss

POWERUP_SPEED_DURATION  = 8.0     # seconds
POWERUP_SPEED_MULT      = 1.5
POWERUP_RAGE_DURATION   = 6.0
POWERUP_RAGE_MULT       = 2.0
POWERUP_REGEN_DURATION  = 10.0
POWERUP_REGEN_RATE      = 5.0     # HP/sec
POWERUP_SHIELD_HITS     = 3
POWERUP_MAGNET_DURATION = 10.0
POWERUP_MAGNET_RANGE    = 400

# ─── Hazards ────────────────────────────────────────────────────────
SOAP_RADIUS_MIN     = 40
SOAP_RADIUS_MAX     = 120
SOAP_EXPAND_SPEED   = 0.8         # Pixels per frame expansion
SOAP_LIFETIME       = 180         # Frames
SOAP_SPAWN_START    = 60          # Seconds before soap starts

WATER_WIDTH         = 60
WATER_LENGTH        = 300
WATER_PUSH_FORCE    = 4.0
WATER_LIFETIME      = 240         # Frames
WATER_SPAWN_START   = 90          # Seconds before water starts

# ─── Alcohol Zone Event ─────────────────────────────────────────────
ALCOHOL_ZONE_RADIUS     = 250     # Visible zone radius on map
ALCOHOL_ZONE_LIFETIME   = 360     # Frames (~15 seconds at 24 FPS)
ALCOHOL_WAVE_SPEED      = 4.5     # Fast pursuit speed
ALCOHOL_WAVE_HEALTH     = 200     # Very tanky
ALCOHOL_WAVE_DAMAGE     = 50      # Instant-kill level damage
ALCOHOL_WAVE_RADIUS     = 20      # Entity radius
ALCOHOL_WAVE_COUNT      = 4       # Entities per zone
ALCOHOL_SPAWN_START     = 120     # Seconds before alcohol events start
ALCOHOL_SPAWN_RATE      = 45.0    # Seconds between alcohol event attempts
COLOR_ALCOHOL_ZONE      = (200, 180, 255, 80)  # Pale purple translucent
COLOR_ALCOHOL_WAVE      = (180, 140, 255)       # Bright purple/lavender
COLOR_ALCOHOL_GLOW      = (220, 180, 255, 60)   # Soft glow

# ─── Nerve Endings ──────────────────────────────────────────────────
NERVE_RADIUS        = 25
NERVE_SPAWN_COUNT   = 8           # Total nodes on map
NERVE_STUN_DURATION = 120         # Frames (at 24 FPS = 5 seconds)
COLOR_NERVE         = (255, 240, 60)
COLOR_NERVE_GLOW    = (255, 255, 150, 80)

# ─── Replication ────────────────────────────────────────────────────
REPLICATE_COST      = 50          # Energy needed (much cheaper!)
MAX_CLONES          = 12

# ─── Combo System ───────────────────────────────────────────────────
COMBO_WINDOW        = 3.0         # Seconds to keep combo alive
COMBO_MAX           = 15          # Max multiplier

# ─── Evolution / XP ────────────────────────────────────────────────
XP_PER_LEVEL        = 100         # XP needed for first evolution
XP_LEVEL_SCALE      = 1.25        # Each level needs 25% more XP

# ─── Difficulty Scaling ─────────────────────────────────────────────
ENEMY_SPAWN_RATE_BASE   = 1.2     # Seconds between enemy spawns (instant action)
ENEMY_SPAWN_RATE_MIN    = 0.5     # Fastest spawn rate
ENEMY_SPAWN_SCALE       = 0.90    # Multiplier per 30 seconds

WBC_SPAWN_START     = 20          # Seconds before WBCs appear
WBC_SPAWN_RATE      = 6.0         # Seconds between WBC spawns

# ─── Inventory & Items ─────────────────────────────────────────────
INVENTORY_SLOTS     = 3
ITEM_SPAWN_RATE     = 15.0        # Seconds between item spawn attempts
ITEM_TYPES = {
    "adrenaline": {
        "name": "Adrenaline Shot",
        "icon": "💉",
        "color": (255, 50, 50),
        "desc": "Burst of speed/damage"
    },
    "grenade": {
        "name": "Bio-Grenade",
        "icon": "💣",
        "color": (100, 255, 50),
        "desc": "Powerful AOE explosion"
    },
    "nanobots": {
        "name": "Repair Nanobots",
        "icon": "🏥",
        "color": (100, 200, 255),
        "desc": "Heal over time"
    },
    "flare": {
        "name": "Sensor Flare",
        "icon": "📡",
        "color": (255, 200, 50),
        "desc": "Reveal enemies"
    }
}

# ─── Mutation Definitions ───────────────────────────────────────────
MUTATIONS = {
    "acid_spit": {
        "name": "Acid Spit",
        "icon": "💧",
        "desc": ["Shoot acid projectiles", "Faster fire rate", "Projectiles pierce"],
        "color": (180, 255, 60),
    },
    "thick_membrane": {
        "name": "Thick Membrane",
        "icon": "🛡️",
        "desc": ["+30 max HP", "+30 more HP", "Reflect 20% damage"],
        "color": (100, 180, 255),
    },
    "rapid_division": {
        "name": "Rapid Division",
        "icon": "🔄",
        "desc": ["-20% replication cost", "-20% more", "Clones spawn full HP"],
        "color": (100, 255, 180),
    },
    "toxic_aura": {
        "name": "Toxic Aura",
        "icon": "☠️",
        "desc": ["Aura radius +30%", "+30% more", "Aura slows enemies"],
        "color": (180, 100, 255),
    },
    "flagella_boost": {
        "name": "Flagella Boost",
        "icon": "⚡",
        "desc": ["+20% speed", "+20% more", "Dash ability"],
        "color": (255, 220, 60),
    },
    "enzyme_drain": {
        "name": "Enzyme Drain",
        "icon": "❤️",
        "desc": ["10% lifesteal", "15% lifesteal", "20% + heal clones"],
        "color": (255, 100, 120),
    },
    "cytotoxic_burst": {
        "name": "Cytotoxic Burst",
        "icon": "💥",
        "desc": ["Manual attack (J/Click)", "Increased radius/damage", "Adds knockback"],
        "color": (255, 150, 50),
    }
}

# ─── Burst Skill Stats ─────────────────────────────────────────────
BURST_BASE_RADIUS   = 80
BURST_BASE_DAMAGE   = 15
BURST_COOLDOWN      = 1.0         # Seconds
