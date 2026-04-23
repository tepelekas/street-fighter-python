# Κλάση Menu - Διαχειρίζεται το κύριο μενού του παιχνιδιού

import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, DARK_GRAY, RED, YELLOW, WHITE, GRAY


class Menu:
    # Κλάση που διαχειρίζεται το κύριο μενού
    # Εμφανίζει επιλογές: Singleplayer, Multiplayer, Exit
    
    def __init__(self, screen):
        # Αρχικοποίηση του menu
        self.screen = screen
        # Fonts για διαφορετικά μεγέθη κειμένου (modern)
        self.font_large = pygame.font.Font(None, 96)
        self.font_medium = pygame.font.Font(None, 42)
        self.options = ["Singleplayer", "Multiplayer", "Exit"]  # Οι επιλογές
        self.button_rects = []  # Rectangles για τα κουμπιά
        
        # Background image
        self.bg_image = None
        bg_path = "assets/backgrounds/main.png"
        # Δοκιμάζουμε πρώτα convert() και αν αποτύχει convert_alpha()
        temp_img = pygame.image.load(bg_path)
        try:
            self.bg_image = temp_img.convert()
        except:
            self.bg_image = temp_img.convert_alpha()
        self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Button images - φόρτωση από assets/buttons/
        self.button_images = {}
        self.button_names = {
            "Singleplayer": "singleplayer_btn.png",
            "Multiplayer": "multiplayer_btn.png",
            "Exit": "exit_btn.png"
        }
        
        # Max button dimensions για να μην καλύπτουν όλη την οθόνη
        max_button_width = 300
        max_button_height = 80
        
        for option, filename in self.button_names.items():
            img = pygame.image.load(f"assets/buttons/{filename}").convert_alpha()
            # Προσαρμογή μεγέθους button image αν είναι πολύ μεγάλο
            original_width, original_height = img.get_size()
            
            # Calculate scale factor αν είναι πολύ μεγάλο
            scale_w = max_button_width / original_width if original_width > max_button_width else 1.0
            scale_h = max_button_height / original_height if original_height > max_button_height else 1.0
            scale = min(scale_w, scale_h)  # Χρησιμοποιούμε το μικρότερο scale
            
            # Αν χρειάζεται scale down
            if scale < 1.0:
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                img = pygame.transform.scale(img, (new_width, new_height))
            
            self.button_images[option] = img
        
        # Button states για effects
        self.button_hover = None  # Ποιο button είναι hover
        self.button_clicked = None  # Ποιο button είναι clicked
        self.click_timer = 0  # Timer για click effect
        
    def handle_event(self, event):
        # Χειρίζεται events (mouse clicks) στο menu
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Αριστερό click
                mouse_pos = event.pos
                for i, rect in enumerate(self.button_rects):
                    if rect and rect.collidepoint(mouse_pos):
                        # Click effect
                        self.button_clicked = self.options[i]
                        self.click_timer = 10  # 10 frames click effect
                        return self.options[i]
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.button_clicked = None
        return None
        
    def draw(self):
        # Σχεδιάζει το menu στην οθόνη με mouse support - modern minimal style
        # Background (μόνο image, χωρίς overlay και default color)
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            # Fallback - μαύρο background αν δεν φορτώσει
            self.screen.fill((20, 20, 30))
        
        # Mouse position για hover effect
        mouse_pos = pygame.mouse.get_pos()
        self.button_rects = []
        
        # Update click timer
        if self.click_timer > 0:
            self.click_timer -= 1
        
        # Επιλογές ως κουμπιά - με images (προσαρμοσμένα μεγέθη)
        button_spacing = 30
        start_y = 250  # Πιο πάνω αφού δεν έχουμε τίτλο
        
        for i, option in enumerate(self.options):
            # Φόρτωση button image (ήδη scaled στο __init__)
            button_img = self.button_images.get(option)
            
            if button_img is None:
                # Fallback σε text αν δεν υπάρχει image
                text = self.font_medium.render(option, True, WHITE)
                text_width, text_height = text.get_size()
                button_width = text_width + 60
                button_height = text_height + 40
            else:
                button_width, button_height = button_img.get_size()
            
            # Δημιουργία button rectangle
            button_x = SCREEN_WIDTH // 2 - button_width // 2
            button_y = start_y + i * (button_height + button_spacing)
            
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            self.button_rects.append(button_rect)
            
            # Έλεγχος hover
            hover = button_rect.collidepoint(mouse_pos)
            clicked = (self.button_clicked == option and self.click_timer > 0)
            
            # Simple modern effects - χωρίς glow που δημιουργεί προβλήματα
            scale = 1.0
            
            if clicked:
                # Click effect - subtle scale down
                scale = 0.97
            elif hover:
                # Hover effect - subtle scale up
                scale = 1.03
            
            # Σχεδίαση button image με simple effects
            if button_img is not None:
                # Calculate scaled size (smooth animation)
                scaled_width = int(button_width * scale)
                scaled_height = int(button_height * scale)
                scaled_x = button_x + (button_width - scaled_width) // 2
                scaled_y = button_y + (button_height - scaled_height) // 2
                
                # Scale image smoothly
                scaled_img = pygame.transform.scale(button_img, (scaled_width, scaled_height))
                
                # Subtle brightness boost on hover/click
                if hover or clicked:
                    # Create subtle brightness overlay
                    brightness_surf = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                    brightness_value = 20 if hover else 30
                    brightness_surf.fill((brightness_value, brightness_value, brightness_value, 0))
                    scaled_img.blit(brightness_surf, (0, 0), special_flags=pygame.BLEND_ADD)
                
                # Draw button
                self.screen.blit(scaled_img, (scaled_x, scaled_y))
            else:
                # Fallback text rendering
                text_surface = self.font_medium.render(option, True, (255, 200, 0) if hover else WHITE)
                text_rect = text_surface.get_rect(center=button_rect.center)
                self.screen.blit(text_surface, text_rect)