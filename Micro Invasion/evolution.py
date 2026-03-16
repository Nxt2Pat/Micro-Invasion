"""
evolution.py — Mutation / Evolution system (Vampire Survivors-style level-up)
When XP bar fills, game pauses and shows 3 random mutation cards to pick from.
"""
import pygame
import random
import math
from settings import (
    MUTATIONS, SCREEN_WIDTH, SCREEN_HEIGHT,
    XP_PER_LEVEL, XP_LEVEL_SCALE,
    COLOR_UI_BG, COLOR_UI_TEXT, COLOR_UI_WHITE
)


class EvolutionSystem:
    """Manages player mutations and the level-up card selection UI."""

    def __init__(self):
        # Current mutations: {mutation_key: level (1-3)}
        self.active_mutations = {}
        # XP tracking
        self.current_xp = 0
        self.current_level = 1
        self.xp_to_next = XP_PER_LEVEL

        # Card selection state
        self.showing_cards = False
        self.card_choices = []  # List of 3 mutation keys
        self.selected_index = -1  # Hover / highlight index
        self.card_animation = 0  # Animation timer

        # Fonts (initialized later)
        self.font_title = None
        self.font_card = None
        self.font_desc = None

    def _init_fonts(self):
        if self.font_title is None:
            self.font_title = pygame.font.Font(None, 48)
            self.font_card = pygame.font.Font(None, 32)
            self.font_desc = pygame.font.Font(None, 22)

    def add_xp(self, amount):
        """Add XP. Returns True if level-up triggered."""
        self.current_xp += amount
        if self.current_xp >= self.xp_to_next:
            self.current_xp -= self.xp_to_next
            self.current_level += 1
            self.xp_to_next = int(XP_PER_LEVEL * (XP_LEVEL_SCALE ** self.current_level))
            self._generate_choices()
            return True
        return False

    @property
    def xp_progress(self):
        """XP progress toward next level as 0-1 fraction."""
        return self.current_xp / self.xp_to_next if self.xp_to_next > 0 else 0

    def _generate_choices(self):
        """Pick 3 random mutations for the player to choose from."""
        available = []
        for key in MUTATIONS:
            current_level = self.active_mutations.get(key, 0)
            if current_level < 3:  # Max level is 3
                available.append(key)

        # If fewer than 3 available, allow duplicates from available pool
        if len(available) >= 3:
            self.card_choices = random.sample(available, 3)
        elif len(available) > 0:
            self.card_choices = available[:]
            while len(self.card_choices) < 3:
                self.card_choices.append(random.choice(available))
        else:
            # All maxed out — no choices
            self.card_choices = []
            return

        self.showing_cards = True
        self.card_animation = 0
        self.selected_index = -1

    def select_mutation(self, index):
        """Player selects mutation card at the given index (0, 1, or 2)."""
        if not self.showing_cards or index >= len(self.card_choices):
            return None

        key = self.card_choices[index]
        current_level = self.active_mutations.get(key, 0)
        self.active_mutations[key] = min(3, current_level + 1)
        self.showing_cards = False
        self.card_choices = []
        return key

    def get_mutation_level(self, key):
        """Get current level of a mutation (0 if not acquired)."""
        return self.active_mutations.get(key, 0)

    # ─── Mutation effect helpers ────────────────────────────────────

    def get_speed_bonus(self):
        """Flagella Boost: +20% per level."""
        level = self.get_mutation_level("flagella_boost")
        return 1.0 + (0.20 * level)

    def get_max_hp_bonus(self):
        """Thick Membrane: +30 HP per level."""
        level = self.get_mutation_level("thick_membrane")
        return 30 * level

    def get_replication_discount(self):
        """Rapid Division: -20% cost per level."""
        level = self.get_mutation_level("rapid_division")
        return 1.0 - (0.20 * level)

    def get_aura_bonus(self):
        """Toxic Aura: +30% radius per level."""
        level = self.get_mutation_level("toxic_aura")
        return 1.0 + (0.30 * level)

    def get_lifesteal(self):
        """Enzyme Drain: 10%/15%/20% lifesteal."""
        level = self.get_mutation_level("enzyme_drain")
        return [0, 0.10, 0.15, 0.20][level]

    def can_acid_spit(self):
        """Acid Spit: level > 0 means active."""
        return self.get_mutation_level("acid_spit") > 0

    def acid_spit_pierces(self):
        return self.get_mutation_level("acid_spit") >= 3

    def aura_slows(self):
        return self.get_mutation_level("toxic_aura") >= 3

    def clones_spawn_full_hp(self):
        return self.get_mutation_level("rapid_division") >= 3

    def reflects_damage(self):
        return self.get_mutation_level("thick_membrane") >= 3

    def heals_clones(self):
        return self.get_mutation_level("enzyme_drain") >= 3

    # ─── Draw the evolution card selection screen ───────────────────

    def update_animation(self):
        if self.showing_cards:
            self.card_animation = min(1.0, self.card_animation + 0.04)

    def draw_cards(self, surface):
        """Draw the evolution card selection overlay."""
        if not self.showing_cards or not self.card_choices:
            return

        self._init_fonts()

        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        alpha = int(160 * self.card_animation)
        overlay.fill((0, 0, 0, alpha))
        surface.blit(overlay, (0, 0))

        # Title
        if self.card_animation > 0.3:
            title_alpha = min(255, int((self.card_animation - 0.3) * 400))
            title_text = self.font_title.render("⬆ EVOLUTION ⬆", True, COLOR_UI_TEXT)
            title_text.set_alpha(title_alpha)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            surface.blit(title_text, title_rect)

            subtitle = self.font_desc.render("Choose a mutation  [1]  [2]  [3]", True, COLOR_UI_WHITE)
            subtitle.set_alpha(title_alpha)
            sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 140))
            surface.blit(subtitle, sub_rect)

        # Draw 3 cards
        if self.card_animation > 0.5:
            card_alpha = min(255, int((self.card_animation - 0.5) * 500))
            card_width = 240
            card_height = 320
            spacing = 40
            total_width = card_width * 3 + spacing * 2
            start_x = (SCREEN_WIDTH - total_width) // 2

            for i, key in enumerate(self.card_choices):
                mutation = MUTATIONS[key]
                current_level = self.active_mutations.get(key, 0)
                next_level = current_level + 1

                # Card position with slide-in animation
                target_y = (SCREEN_HEIGHT - card_height) // 2 + 20
                card_x = start_x + i * (card_width + spacing)
                # Staggered slide-in
                delay = i * 0.1
                slide_progress = min(1.0, max(0, (self.card_animation - 0.5 - delay) * 4))
                card_y = int(target_y + (1 - slide_progress) * 100)

                # Card background
                card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                bg_alpha = int(200 * slide_progress)

                # Highlight if hovered
                if i == self.selected_index:
                    pygame.draw.rect(card_surf, (*mutation["color"], bg_alpha),
                                   (0, 0, card_width, card_height), border_radius=12)
                    pygame.draw.rect(card_surf, (*mutation["color"], min(255, bg_alpha + 50)),
                                   (0, 0, card_width, card_height), 3, border_radius=12)
                else:
                    pygame.draw.rect(card_surf, (20, 15, 25, bg_alpha),
                                   (0, 0, card_width, card_height), border_radius=12)
                    pygame.draw.rect(card_surf, (*mutation["color"], int(100 * slide_progress)),
                                   (0, 0, card_width, card_height), 2, border_radius=12)

                # Key number
                key_text = self.font_card.render(f"[{i + 1}]", True, mutation["color"])
                key_text.set_alpha(int(card_alpha * slide_progress))
                card_surf.blit(key_text, (card_width // 2 - key_text.get_width() // 2, 15))

                # Icon
                icon_text = self.font_title.render(mutation["icon"], True, COLOR_UI_WHITE)
                icon_text.set_alpha(int(card_alpha * slide_progress))
                card_surf.blit(icon_text, (card_width // 2 - icon_text.get_width() // 2, 50))

                # Name
                name_text = self.font_card.render(mutation["name"], True, mutation["color"])
                name_text.set_alpha(int(card_alpha * slide_progress))
                card_surf.blit(name_text, (card_width // 2 - name_text.get_width() // 2, 110))

                # Level indicator
                level_str = f"Lv.{current_level} → Lv.{next_level}"
                level_text = self.font_desc.render(level_str, True, COLOR_UI_WHITE)
                level_text.set_alpha(int(card_alpha * slide_progress))
                card_surf.blit(level_text, (card_width // 2 - level_text.get_width() // 2, 145))

                # Level pips
                pip_y = 170
                for lv in range(3):
                    pip_x = card_width // 2 - 25 + lv * 25
                    if lv < current_level:
                        pip_color = mutation["color"]
                    elif lv == current_level:
                        pip_color = (255, 255, 200)  # Next level highlight
                    else:
                        pip_color = (60, 60, 60)
                    pygame.draw.circle(card_surf, pip_color, (pip_x, pip_y), 6)
                    pygame.draw.circle(card_surf, (100, 100, 100), (pip_x, pip_y), 6, 1)

                # Description
                if next_level <= 3:
                    desc = mutation["desc"][next_level - 1]
                else:
                    desc = "MAX LEVEL"
                desc_text = self.font_desc.render(desc, True, (200, 200, 200))
                desc_text.set_alpha(int(card_alpha * slide_progress))
                card_surf.blit(desc_text, (card_width // 2 - desc_text.get_width() // 2, 200))

                card_surf.set_alpha(int(card_alpha * slide_progress))
                surface.blit(card_surf, (card_x, card_y))
