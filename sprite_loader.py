# Sprite Loader - φορτώνει και διαχειρίζεται sprites/animations για τους fighters
import pygame
import os

class SpriteLoader:
    # Κλάση που φορτώνει και κρατάει τα sprites για όλα τα animations (idle, walking, attack κτλ.)
    
    def __init__(self, sprite_path):
        # Αρχικοποίηση sprite loader με path προς τον φάκελο sprites (π.χ. "sprites/player1")
        self.sprite_path = sprite_path
        self.sprites = {
            'idle': [],
            'walking': [],
            'attacking': [],
            'jumping': [],
            'shield': [],
            'hurt': [],
            'dead': []
        }
        self.load_sprites()
    
    def load_sprites(self):
        # Φορτώνει όλα τα sprites από τους φακέλους για κάθε animation
        animations = ['idle', 'walking', 'attacking', 'jumping', 'shield', 'hurt', 'dead']
        
        for anim in animations:
            anim_path = os.path.join(self.sprite_path, anim)
            if os.path.exists(anim_path):
                # Φόρτωση frames με σωστή σειρά (sort by number in filename)
                frames = []
                frame_files = [f for f in os.listdir(anim_path) if f.endswith('.png')]
                # Sort by number in filename (e.g., idle_01.png, idle_02.png)
                frame_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 999)
                
                for frame_file in frame_files:
                    frame_path = os.path.join(anim_path, frame_file)
                    sprite = pygame.image.load(frame_path).convert_alpha()
                    frames.append(sprite)
                self.sprites[anim] = frames
            else:
                # Αν δεν υπάρχουν sprites, χρησιμοποιούμε empty list
                self.sprites[anim] = []
    
    def get_sprite(self, animation, frame_index, direction=1):
        # Επιστρέφει το σωστό sprite για animation/frame και κατεύθυνση (1 δεξιά, -1 αριστερά)
        if animation not in self.sprites:
            return None
        
        frames = self.sprites[animation]
        if not frames:
            return None
        
        # Wrap frame index
        actual_frame = frame_index % len(frames) if frames else 0
        sprite = frames[actual_frame].copy()  # Copy για να μην αλλάξει το original
        
        # Flip αν είναι αριστερά
        if direction == -1:
            sprite = pygame.transform.flip(sprite, True, False)
        
        return sprite
    
    def has_sprites(self, animation):
        # Επιστρέφει True αν υπάρχουν φορτωμένα sprites για τη συγκεκριμένη animation
        return animation in self.sprites and len(self.sprites[animation]) > 0