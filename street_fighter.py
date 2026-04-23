# Κύριο αρχείο του παιχνιδιού Street Fighter
# Διαχειρίζεται το main game loop, τις συγκρούσεις, τα backgrounds, το menu και την ροή των γύρων

import pygame
import sys
import random

# Imports από τα modules
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WHITE, BLACK, RED, BLUE,
    YELLOW, GRAY, DARK_GRAY, GOLD
)
from fighter import Fighter
from round_manager import RoundManager
from cpu_controller import CPUController, KeyState
from menu import Menu

# Αρχικοποίηση Pygame
pygame.init()

class Game:
    # Κύρια κλάση του παιχνιδιού
    # Διαχειρίζεται το main loop, collisions, backgrounds, menus, κτλ
    
    def __init__(self):
        # Αρχικοποίηση του παιχνιδιού
        # Δημιουργία οθόνης
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Street Fighter")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 72)
        
        # Menu
        self.menu = Menu(self.screen)
        self.game_mode = None  # "singleplayer" ή "multiplayer"
        self.running = True  # Αν το παιχνίδι τρέχει
        self.in_menu = True  # Αν βρισκόμαστε στο menu
        self.in_end_menu = False  # Αν βρισκόμαστε στο end menu
        
        # Game objects (αρχικοποιούνται αργότερα)
        self.fighter1 = None
        self.fighter2 = None
        self.cpu_controller = None
        self.round_manager = None
        
        # End menu buttons (για mouse clicks)
        self.restart_button_rect = None
        self.menu_button_rect = None
        
        # Button images για end menu (με scaling)
        self.end_button_images = {}
        max_button_width = 300
        max_button_height = 80
        
        restart_img = pygame.image.load("assets/buttons/restart_btn.png").convert_alpha()
        # Scale down αν είναι πολύ μεγάλο
        rw, rh = restart_img.get_size()
        scale_r = min(max_button_width / rw if rw > max_button_width else 1.0,
                        max_button_height / rh if rh > max_button_height else 1.0)
        if scale_r < 1.0:
            restart_img = pygame.transform.scale(restart_img, (int(rw * scale_r), int(rh * scale_r)))
        self.end_button_images["Restart"] = restart_img
        
        menu_img = pygame.image.load("assets/buttons/exit_to_menu_btn.png").convert_alpha()
        # Scale down αν είναι πολύ μεγάλο
        mw, mh = menu_img.get_size()
        scale_m = min(max_button_width / mw if mw > max_button_width else 1.0,
                        max_button_height / mh if mh > max_button_height else 1.0)
        if scale_m < 1.0:
            menu_img = pygame.transform.scale(menu_img, (int(mw * scale_m), int(mh * scale_m)))
        self.end_button_images["Exit to Main Menu"] = menu_img

        # Button states για effects
        self.end_button_hover = None
        self.end_button_clicked = None
        self.end_click_timer = 0
        
        # Arena (πίστα) - το rectangle όπου γίνεται ο αγώνας
        # Platform πιο κάτω - collision detection μόνο
        self.arena_rect = pygame.Rect(50, 100, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200)
        self.platform_y = SCREEN_HEIGHT - 20  # Platform πιο κάτω
        
        # Background images - φόρτωση από assets/backgrounds/
        self.bg_single = None
        self.bg_multi = None
        self.bg_single = pygame.image.load("assets/backgrounds/background_01.png").convert()
        self.bg_single = pygame.transform.scale(self.bg_single, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.bg_multi = pygame.image.load("assets/backgrounds/background_02.png").convert()
        self.bg_multi = pygame.transform.scale(self.bg_multi, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Fallback colors
        self.bg_color_single = (30, 40, 60)  # Dark blue για singleplayer
        self.bg_color_multi = (60, 30, 40)   # Dark red για multiplayer
        self.arena_color = (40, 50, 70)  # Modern arena color
        
    def start_game(self, mode):
        # Ξεκινάει το παιχνίδι με το συγκεκριμένο mode (singleplayer/multiplayer)
        self.game_mode = mode
        self.in_menu = False
        self.in_end_menu = False
        
        # Δημιουργία fighters με sprite paths - στο platform_y (rect.bottom = platform_y)
        # Το rect.height είναι ~110, οπότε rect.y = platform_y - 110 για να είναι το bottom στο platform_y
        fighter1_y = self.platform_y - 110
        fighter2_y = self.platform_y - 110
        self.fighter1 = Fighter(200, fighter1_y, "Player 1", RED, "sprites/player1")
        if mode == "singleplayer":
            self.fighter2 = Fighter(700, fighter2_y, "Player 2", BLUE, "sprites/cpu")
        else:
            self.fighter2 = Fighter(700, fighter2_y, "Player 2", BLUE, "sprites/player2")
        
        # Δημιουργία CPU controller αν είναι singleplayer
        if mode == "singleplayer":
            # Default: λίγο πιο εύκολο CPU για να μην είναι ανίκητο
            self.cpu_controller = CPUController(self.fighter2, self.fighter1, difficulty="easy")
        else:
            self.cpu_controller = None
            
        # Δημιουργία/reset round manager
        if self.round_manager:
            self.round_manager.reset()
        else:
            self.round_manager = RoundManager()
        
        # Reset positions και directions - face to face
        self.reset_fighter_positions()
    
    def reset_fighter_positions(self):
        # Επαναφέρει τις θέσεις και directions των fighters - face to face
        if self.fighter1 and self.fighter2:
            # Θέσεις - στο platform_y, με βάση το πραγματικό ύψος των rect
            fighter1_y = self.platform_y - self.fighter1.rect.height
            fighter2_y = self.platform_y - self.fighter2.rect.height
            
            # X θέσεις - Player 1 αριστερά, Player 2 δεξιά
            fighter1_x = 200
            fighter2_x = 700
            
            # Set positions
            self.fighter1.rect.x = fighter1_x
            self.fighter1.rect.y = fighter1_y
            self.fighter1.rect.bottom = self.platform_y  # Βεβαιώνουμε ότι είναι στο platform
            
            self.fighter2.rect.x = fighter2_x
            self.fighter2.rect.y = fighter2_y
            self.fighter2.rect.bottom = self.platform_y  # Βεβαιώνουμε ότι είναι στο platform
            
            # Face to face - Player 1 κοιτάει δεξιά, Player 2 κοιτάει αριστερά
            self.fighter1.dir = 1  # Κοιτάει δεξιά (προς Player 2)
            self.fighter2.dir = -1  # Κοιτάει αριστερά (προς Player 1)
            
            # Reset states
            self.fighter1.on_ground = True
            self.fighter2.on_ground = True
            self.fighter1.velocity_y = 0
            self.fighter2.velocity_y = 0
        
    def handle_collisions(self):
        # Χειρίζεται όλες τις collisions (fighter-to-fighter, attacks)
        # Collision μεταξύ fighters (για να μην περνούν ο ένας μέσα από τον άλλο)
        # Μόνο όταν και οι δύο είναι στο έδαφος - επιτρέπουμε jump πάνω από τον αντίπαλο
        if (self.fighter1.rect.colliderect(self.fighter2.rect) and 
            self.fighter1.on_ground and self.fighter2.on_ground):
            # Υπολογισμός overlap
            if self.fighter1.rect.centerx < self.fighter2.rect.centerx:
                # Player 1 είναι αριστερά, σπρώχνουμε αριστερά
                overlap = self.fighter1.rect.right - self.fighter2.rect.left
                if overlap > 0:
                    self.fighter1.rect.x -= overlap // 2
                    self.fighter2.rect.x += overlap // 2
            else:
                # Player 2 είναι αριστερά, σπρώχνουμε δεξιά
                overlap = self.fighter2.rect.right - self.fighter1.rect.left
                if overlap > 0:
                    self.fighter1.rect.x += overlap // 2
                    self.fighter2.rect.x -= overlap // 2
            
            # Διασφάλιση ότι δεν βγαίνουν εκτός arena
            if self.fighter1.rect.left < self.arena_rect.left:
                self.fighter1.rect.left = self.arena_rect.left
            if self.fighter1.rect.right > self.arena_rect.right:
                self.fighter1.rect.right = self.arena_rect.right
            if self.fighter2.rect.left < self.arena_rect.left:
                self.fighter2.rect.left = self.arena_rect.left
            if self.fighter2.rect.right > self.arena_rect.right:
                self.fighter2.rect.right = self.arena_rect.right
            
        # Collisions επιθέσεων
        hitbox1 = self.fighter1.attack_hitbox()
        hitbox2 = self.fighter2.attack_hitbox()
        
        # Αν ο Player 1 επιτίθεται και χτυπάει τον Player 2
        if hitbox1 and hitbox1.colliderect(self.fighter2.rect):
            if not self.fighter2.invulnerable and not self.fighter2.is_dead:
                # Player 1: δυνατό, πιο αργό μονό χτύπημα
                damage = random.randint(8, 14)  # Λίγο μεγαλύτερη ζημιά για ένα hit
                self.fighter2.take_damage(damage)
                
        # Αν ο Player 2 επιτίθεται και χτυπάει τον Player 1 (double hit)
        if hitbox2 and hitbox2.colliderect(self.fighter1.rect):
            if not self.fighter1.invulnerable and not self.fighter1.is_dead:
                # Double hit για Player 2 - 2 hits διαδοχικά
                # Χρησιμοποιούμε ένα flag για να αποφύγουμε duplicate hits στο ίδιο frame
                if not hasattr(self, '_p2_last_hit_frame'):
                    self._p2_last_hit_frame = -1
                current_frame = pygame.time.get_ticks() // 16  # Approximate frame number
                
                # Έλεγχος αν είναι στο πρώτο ή δεύτερο hit του double hit
                attack_frames = 4
                if self.fighter2.sprite_loader:
                    attack_frames = len(self.fighter2.sprite_loader.sprites.get('attacking', []))
                    if attack_frames == 0:
                        attack_frames = 4
                frames_per_frame = 6
                total_attack_duration = attack_frames * frames_per_frame
                elapsed_frames = total_attack_duration - self.fighter2.attack_timer
                
                # Πρώτο hit: 30-40% του animation (όταν «βγάζει» το σπαθί)
                hit1_start = int(total_attack_duration * 0.30)
                hit1_end = int(total_attack_duration * 0.40)
                # Δεύτερο hit: 70-80% του animation (όταν το «μαζεύει»)
                hit2_start = int(total_attack_duration * 0.70)
                hit2_end = int(total_attack_duration * 0.80)
                
                # Damage μόνο αν είμαστε στο hit frame και δεν έχουμε κάνει hit στο ίδιο frame
                if (hit1_start <= elapsed_frames <= hit1_end) or (hit2_start <= elapsed_frames <= hit2_end):
                    if current_frame != self._p2_last_hit_frame:
                        # Player 2: δύο διαδοχικά, πιο γρήγορα χτυπήματα με μικρότερο damage το καθένα
                        # ώστε τα 2 hits μαζί να είναι περίπου ίσα με 1 δυνατό hit του Player 1.
                        damage = random.randint(3, 7)
                        self.fighter1.take_damage(damage)
                        self._p2_last_hit_frame = current_frame
                
    def draw_health_bars(self):
        # Σχεδιάζει τις health bars των δύο players - modern style
        # Health bar Player 1
        bar_width = 300
        bar_height = 35
        bar_x = 50
        bar_y = 50  # Πιο κάτω για να χωράει το όνομα
        
        # Font για ονόματα - μεγαλύτερο και bold
        name_font = pygame.font.Font(None, 36)
        
        # Όνομα Player 1 - με καλύτερο shadow/outline
        player1_name = "Player 1"
        # Multiple shadow layers για καλύτερη ορατότητα
        for offset_x, offset_y in [(3, 3), (2, 2), (1, 1)]:
            shadow_text1 = name_font.render(player1_name, True, BLACK)
            self.screen.blit(shadow_text1, (bar_x + offset_x, bar_y - 32 + offset_y))
        name_text1 = name_font.render(player1_name, True, WHITE)
        self.screen.blit(name_text1, (bar_x, bar_y - 30))
        
        # Background
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
        # Health (κόκκινο)
        health_width = int((self.fighter1.hp / self.fighter1.max_hp) * bar_width)
        pygame.draw.rect(self.screen, RED, (bar_x, bar_y, health_width, bar_height))
        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Medals κάτω από την μπάρα Player 1
        medal_size = 12
        medal_y = bar_y + bar_height + 15
        medal_start_x = bar_x + 10
        for i in range(2):
            medal_x = medal_start_x + (i * 25)
            color = GOLD if i < self.round_manager.wins_p1 else GRAY
            # Σχεδίαση medal (κύκλος με border)
            pygame.draw.circle(self.screen, color, (medal_x, medal_y), medal_size)
            pygame.draw.circle(self.screen, WHITE, (medal_x, medal_y), medal_size, 2)
        
        # VS text - μεγαλύτερο και prominent (ανάμεσα στις health bars, πιο πάνω)
        vs_font = pygame.font.Font(None, 120)  # Μεγαλύτερο font (από 108 σε 120)
        vs_text = vs_font.render("VS", True, (255, 200, 0))  # Gold color
        # Shadow για VS
        vs_shadow = vs_font.render("VS", True, BLACK)
        vs_x = SCREEN_WIDTH // 2 - vs_text.get_width() // 2
        # VS πιο πάνω - ανάμεσα στις health bars (λίγο πιο πάνω από το κέντρο)
        vs_y = bar_y + bar_height // 2 - vs_text.get_height() // 2 - 5  # Κέντρο health bars - 5px πάνω
        # Multiple shadow layers
        for offset_x, offset_y in [(3, 3), (2, 2)]:
            self.screen.blit(vs_shadow, (vs_x + offset_x, vs_y + offset_y))
        self.screen.blit(vs_text, (vs_x, vs_y))
        
        # Health bar Player 2 - ίδιο style με Player 1 (απλό)
        bar_x2 = SCREEN_WIDTH - 50 - bar_width
        
        # Όνομα Player 2 (ή CPU) - με καλύτερο shadow/outline
        if self.game_mode == "singleplayer":
            player2_name = "CPU"
        else:
            player2_name = "Player 2"
        # Multiple shadow layers για καλύτερη ορατότητα
        name_text2 = name_font.render(player2_name, True, WHITE)
        name_rect2 = name_text2.get_rect()
        name_rect2.right = bar_x2 + bar_width
        name_rect2.y = bar_y - 30
        for offset_x, offset_y in [(3, 3), (2, 2), (1, 1)]:
            shadow_text2 = name_font.render(player2_name, True, BLACK)
            shadow_rect2 = shadow_text2.get_rect()
            shadow_rect2.right = bar_x2 + bar_width + offset_x
            shadow_rect2.y = bar_y - 32 + offset_y
            self.screen.blit(shadow_text2, shadow_rect2)
        self.screen.blit(name_text2, name_rect2)
        
        # Health bar Player 2 - ίδιο style με Player 1 (απλό)
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x2, bar_y, bar_width, bar_height))
        health_width2 = int((self.fighter2.hp / self.fighter2.max_hp) * bar_width)
        pygame.draw.rect(self.screen, RED, (bar_x2, bar_y, health_width2, bar_height))
        pygame.draw.rect(self.screen, WHITE, (bar_x2, bar_y, bar_width, bar_height), 2)
        
        # Medals κάτω από την μπάρα Player 2
        medal_start_x2 = bar_x2 + 10
        for i in range(2):
            medal_x = medal_start_x2 + (i * 25)
            color = GOLD if i < self.round_manager.wins_p2 else GRAY
            # Σχεδίαση medal (κύκλος με border)
            pygame.draw.circle(self.screen, color, (medal_x, medal_y), medal_size)
            pygame.draw.circle(self.screen, WHITE, (medal_x, medal_y), medal_size, 2)
        
    def draw_round_info(self):
        # Σχεδιάζει πληροφορίες για τον γύρο (round number, countdown, KO)
        # Round number στα ελληνικά - με καλύτερο shadow/outline, ΚΑΤΩ από το VS
        round_font = pygame.font.Font(None, 42)  # Μεγαλύτερο font
        round_text_str = f"Γύρος {self.round_manager.round_num}"

        # Το VS στη health bar βρίσκεται περίπου στο ύψος ~120px.
        # Βάζουμε τον γύρο λίγο πιο κάτω, με ένα μικρό κενό.
        round_y_center = 135

        round_text = round_font.render(round_text_str, True, (255, 200, 0))  # Gold color
        round_rect = round_text.get_rect(center=(SCREEN_WIDTH // 2, round_y_center))

        # Multiple shadow layers για καλύτερη ορατότητα
        for offset_x, offset_y in [(3, 3), (2, 2), (1, 1)]:
            round_shadow = round_font.render(round_text_str, True, BLACK)
            shadow_rect = round_shadow.get_rect(center=(SCREEN_WIDTH // 2 + offset_x,
                                                        round_y_center + offset_y))
            self.screen.blit(round_shadow, shadow_rect)

        self.screen.blit(round_text, round_rect)
            
        # Countdown ή KO text
        if self.round_manager.state == "COUNTDOWN":
            # Εμφάνιση countdown - modern style με shadow
            if self.round_manager.countdown_text:
                countdown_text = self.font_large.render(
                    self.round_manager.countdown_text, True, (255, 200, 0)  # Gold
                )
                countdown_shadow = self.font_large.render(
                    self.round_manager.countdown_text, True, (0, 0, 0)
                )
                text_rect = countdown_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                shadow_rect = countdown_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, SCREEN_HEIGHT // 2 + 3))
                self.screen.blit(countdown_shadow, shadow_rect)
                self.screen.blit(countdown_text, text_rect)
            
        elif self.round_manager.state == "ROUND_END":
            # Εμφάνιση K.O. στην πλευρά του χαμένου
            if self.round_manager.winner == "P1":
                # Player 2 έχασε - K.O. στην δεξιά πλευρά
                ko_text = self.font_large.render("K.O.", True, RED)
                ko_x = SCREEN_WIDTH - 150
                ko_y = SCREEN_HEIGHT // 2
            else:
                # Player 1 έχασε - K.O. στην αριστερή πλευρά
                ko_text = self.font_large.render("K.O.", True, RED)
                ko_x = 150
                ko_y = SCREEN_HEIGHT // 2
            text_rect = ko_text.get_rect(center=(ko_x, ko_y))
            self.screen.blit(ko_text, text_rect)
            
    def draw_end_menu(self):
        # Σχεδιάζει το end menu (μετά το τέλος του match) με mouse support
        # Overlay (ημιδιαφανές μαύρο)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Κείμενο νικητή στα ελληνικά
        if self.round_manager.wins_p1 >= 2:
            winner_name = "Player 1"
        else:
            if self.game_mode == "singleplayer":
                winner_name = "CPU"
            else:
                winner_name = "Player 2"
        winner_text = self.font_large.render(f"Winner: {winner_name}!", True, GOLD)
        text_rect = winner_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(winner_text, text_rect)
        
        # Κουμπιά με mouse support - με images
        button_spacing = 30
        button_y = SCREEN_HEIGHT // 2 + 50
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Update click timer
        if self.end_click_timer > 0:
            self.end_click_timer -= 1
        
        # Κουμπί Restart - με image
        restart_img = self.end_button_images.get("Restart")
        if restart_img is None:
            # Fallback σε text
            restart_text_surface = self.font.render("Restart", True, WHITE)
            restart_text_width, restart_text_height = restart_text_surface.get_size()
            restart_button_width = restart_text_width + 60
            restart_button_height = restart_text_height + 40
        else:
            restart_button_width, restart_button_height = restart_img.get_size()
        
        restart_x = SCREEN_WIDTH // 2 - restart_button_width // 2
        restart_rect = pygame.Rect(restart_x, button_y, restart_button_width, restart_button_height)
        
        restart_hover = restart_rect.collidepoint(mouse_pos)
        restart_clicked = (self.end_button_clicked == "Restart" and self.end_click_timer > 0)
        
        # Simple modern effects
        restart_scale = 1.0
        if restart_clicked:
            restart_scale = 0.97
        elif restart_hover:
            restart_scale = 1.03
        
        # Σχεδίαση Restart button με simple effects
        if restart_img is not None:
            scaled_width = int(restart_button_width * restart_scale)
            scaled_height = int(restart_button_height * restart_scale)
            scaled_x = restart_x + (restart_button_width - scaled_width) // 2
            scaled_y = button_y + (restart_button_height - scaled_height) // 2
            
            scaled_img = pygame.transform.scale(restart_img, (scaled_width, scaled_height))
            
            if restart_hover or restart_clicked:
                brightness_surf = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                brightness_value = 20 if restart_hover else 30
                brightness_surf.fill((brightness_value, brightness_value, brightness_value, 0))
                scaled_img.blit(brightness_surf, (0, 0), special_flags=pygame.BLEND_ADD)
            
            self.screen.blit(scaled_img, (scaled_x, scaled_y))
        else:
            # Fallback text
            restart_text_surface = self.font.render("Restart", True, (255, 200, 0) if restart_hover else WHITE)
            restart_text_rect = restart_text_surface.get_rect(center=restart_rect.center)
            self.screen.blit(restart_text_surface, restart_text_rect)
        
        # Κουμπί Exit to Main Menu - με image
        menu_img = self.end_button_images.get("Exit to Main Menu")
        if menu_img is None:
            # Fallback σε text
            menu_text_surface = self.font.render("Exit to Main Menu", True, WHITE)
            menu_text_width, menu_text_height = menu_text_surface.get_size()
            menu_button_width = menu_text_width + 60
            menu_button_height = menu_text_height + 40
        else:
            menu_button_width, menu_button_height = menu_img.get_size()
        
        menu_x = SCREEN_WIDTH // 2 - menu_button_width // 2
        menu_y = button_y + restart_button_height + button_spacing
        menu_rect = pygame.Rect(menu_x, menu_y, menu_button_width, menu_button_height)
        
        menu_hover = menu_rect.collidepoint(mouse_pos)
        menu_clicked = (self.end_button_clicked == "Exit to Main Menu" and self.end_click_timer > 0)
        
        # Simple modern effects
        menu_scale = 1.0
        if menu_clicked:
            menu_scale = 0.97
        elif menu_hover:
            menu_scale = 1.03
        
        # Σχεδίαση Exit to Main Menu button με simple effects
        if menu_img is not None:
            scaled_width = int(menu_button_width * menu_scale)
            scaled_height = int(menu_button_height * menu_scale)
            scaled_x = menu_x + (menu_button_width - scaled_width) // 2
            scaled_y = menu_y + (menu_button_height - scaled_height) // 2
            
            scaled_img = pygame.transform.scale(menu_img, (scaled_width, scaled_height))
            
            if menu_hover or menu_clicked:
                brightness_surf = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                brightness_value = 20 if menu_hover else 30
                brightness_surf.fill((brightness_value, brightness_value, brightness_value, 0))
                scaled_img.blit(brightness_surf, (0, 0), special_flags=pygame.BLEND_ADD)
            
            self.screen.blit(scaled_img, (scaled_x, scaled_y))
        else:
            # Fallback text
            menu_text_surface = self.font.render("Exit to Main Menu", True, (255, 200, 0) if menu_hover else WHITE)
            menu_text_rect = menu_text_surface.get_rect(center=menu_rect.center)
            self.screen.blit(menu_text_surface, menu_text_rect)
        
        # Αποθήκευση των rectangles για mouse click detection
        self.restart_button_rect = restart_rect
        self.menu_button_rect = menu_rect
        
    def run(self):
        # Κύριος game loop - τρέχει μέχρι να κλείσει το παιχνίδι
        while self.running:
            # Κρατάει σταθερό FPS
            self.clock.tick(FPS)
            
            # Επεξεργασία events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
                # Events στο menu (mouse clicks)
                if self.in_menu:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        result = self.menu.handle_event(event)
                        if result == "Singleplayer":
                            self.start_game("singleplayer")
                        elif result == "Multiplayer":
                            self.start_game("multiplayer")
                        elif result == "Exit":
                            self.running = False
                        
                # Events στο end menu (mouse clicks)
                elif self.in_end_menu:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Αριστερό click
                            if self.restart_button_rect and self.restart_button_rect.collidepoint(event.pos):
                                # Click effect
                                self.end_button_clicked = "Restart"
                                self.end_click_timer = 10
                                # Επαναληψη - ξεκινάει νέο match
                                self.start_game(self.game_mode)
                            elif self.menu_button_rect and self.menu_button_rect.collidepoint(event.pos):
                                # Click effect
                                self.end_button_clicked = "Exit to Main Menu"
                                self.end_click_timer = 10
                                # Επιστροφη στο μενου
                                self.in_menu = True
                                self.in_end_menu = False
                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:
                            self.end_button_clicked = None
                            
            # Σχεδίαση
            if self.in_menu:
                # Σχεδίαση menu
                self.menu.draw()
                
            elif not self.in_end_menu:
                # Game loop
                # Background (image ή color fallback)
                if self.game_mode == "singleplayer":
                    if self.bg_single:
                        self.screen.blit(self.bg_single, (0, 0))
                    else:
                        self.screen.fill(self.bg_color_single)
                else:
                    if self.bg_multi:
                        self.screen.blit(self.bg_multi, (0, 0))
                    else:
                        self.screen.fill(self.bg_color_multi)
                
                # Platform collision μόνο - δεν σχεδιάζεται (background έχει platform)
                
                # Ενημέρωση round manager
                old_state = self.round_manager.state
                self.round_manager.update(self.fighter1, self.fighter2)
                # Αν αλλάξει σε COUNTDOWN (νέος γύρος), reset positions
                if old_state != "COUNTDOWN" and self.round_manager.state == "COUNTDOWN":
                    self.reset_fighter_positions()
                
                # Ενημέρωση fighters κατά την κατάσταση FIGHT και ROUND_END (για dead animation)
                if self.round_manager.state == "FIGHT" or self.round_manager.state == "ROUND_END":
                    keys = pygame.key.get_pressed()
                    
                    # Controls Player 1: a=left, d=right, w=jump, s=crouch, e=punch
                    p1_controls = {
                        'left': pygame.K_a,
                        'right': pygame.K_d,
                        'jump': pygame.K_w,
                        'duck': pygame.K_s,
                        'attack': pygame.K_e
                    }
                    # Update fighters με opponent_rect, opponent_on_ground και platform_y
                    # Στο ROUND_END, update μόνο για animations (dead), όχι για inputs
                    if self.round_manager.state == "FIGHT":
                        self.fighter1.update(keys, p1_controls, self.arena_rect, 
                                            opponent_rect=self.fighter2.rect,
                                            opponent_on_ground=self.fighter2.on_ground,
                                            platform_y=self.platform_y)
                    else:  # ROUND_END - μόνο animation update
                        # Δημιουργία empty key state για animation-only update
                        empty_keys = KeyState()
                        self.fighter1.update(empty_keys, p1_controls, self.arena_rect,
                                            opponent_rect=self.fighter2.rect,
                                            opponent_on_ground=self.fighter2.on_ground,
                                            platform_y=self.platform_y)
                    
                    # Controls Player 2 (CPU ή Player)
                    if self.round_manager.state == "FIGHT":
                        if self.game_mode == "singleplayer":
                            # Singleplayer - CPU ελέγχει τον Player 2
                            cpu_keys = self.cpu_controller.update()
                            p2_controls = {
                                'left': pygame.K_LEFT,
                                'right': pygame.K_RIGHT,
                                'jump': pygame.K_UP,
                                'duck': pygame.K_DOWN,
                                'attack': pygame.K_RCTRL
                            }
                            self.fighter2.update(cpu_keys, p2_controls, self.arena_rect,
                                                opponent_rect=self.fighter1.rect,
                                                opponent_on_ground=self.fighter1.on_ground,
                                                platform_y=self.platform_y)
                        else:
                            # Multiplayer - Player 2: arrows + right ctrl
                            p2_controls = {
                                'left': pygame.K_LEFT,
                                'right': pygame.K_RIGHT,
                                'jump': pygame.K_UP,
                                'duck': pygame.K_DOWN,
                                'attack': pygame.K_RCTRL
                            }
                            self.fighter2.update(keys, p2_controls, self.arena_rect,
                                                opponent_rect=self.fighter1.rect,
                                                opponent_on_ground=self.fighter1.on_ground,
                                                platform_y=self.platform_y)
                    else:  # ROUND_END - μόνο animation update
                        empty_keys = KeyState()
                        p2_controls = {
                            'left': pygame.K_LEFT,
                            'right': pygame.K_RIGHT,
                            'jump': pygame.K_UP,
                            'duck': pygame.K_DOWN,
                            'attack': pygame.K_RCTRL
                        }
                        self.fighter2.update(empty_keys, p2_controls, self.arena_rect,
                                            opponent_rect=self.fighter1.rect,
                                            opponent_on_ground=self.fighter1.on_ground,
                                            platform_y=self.platform_y)
                    
                    # Επεξεργασία collisions μόνο κατά την κατάσταση FIGHT
                    if self.round_manager.state == "FIGHT":
                        self.handle_collisions()
                
                # Σχεδίαση όλων
                self.fighter1.draw(self.screen, self.arena_rect)
                self.fighter2.draw(self.screen, self.arena_rect)
                self.draw_health_bars()
                self.draw_round_info()
                
                # Έλεγχος τέλους match
                if self.round_manager.state == "MATCH_END":
                    self.in_end_menu = True
                    
            else:
                # Σχεδίαση end menu (με game στο background) - κρατάμε το background image
                # Background (image ή color fallback) - ίδιο με το game
                if self.game_mode == "singleplayer":
                    if self.bg_single:
                        self.screen.blit(self.bg_single, (0, 0))
                    else:
                        self.screen.fill(self.bg_color_single)
                else:
                    if self.bg_multi:
                        self.screen.blit(self.bg_multi, (0, 0))
                    else:
                        self.screen.fill(self.bg_color_multi)
                
                # Σχεδίαση fighters και health bars (στο background)
                self.fighter1.draw(self.screen, self.arena_rect)
                self.fighter2.draw(self.screen, self.arena_rect)
                self.draw_health_bars()
                self.draw_end_menu()
                
            # Ενημέρωση οθόνης
            pygame.display.flip()
            
        # Κλείσιμο Pygame
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # Ξεκινάει το παιχνίδι
    game = Game()
    game.run()