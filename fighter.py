# Κλάση Fighter - Αντιπροσωπεύει έναν παίκτη στο παιχνίδι
# Χειρίζεται την κίνηση, επιθέσεις, ζωή, και όλες τις καταστάσεις του fighter

import pygame
import os
from constants import WHITE, YELLOW, BLACK, SCREEN_HEIGHT

# Try to import sprite loader
try:
    from sprite_loader import SpriteLoader
    SPRITE_LOADER_AVAILABLE = True
except ImportError:
    SPRITE_LOADER_AVAILABLE = False

class Fighter:
    # Κλάση που αντιπροσωπεύει έναν παίκτη/fighter
    # Χειρίζεται όλες τις λειτουργίες του fighter (κίνηση, επιθέσεις, ζωή, κτλ)
    
    def __init__(self, x, y, name, color, sprite_path=None):
        # Αρχικοποίηση του fighter
        # Δημιουργία rectangle για collision detection (sprite-based)
        # Μεγαλύτερο rect για να ταιριάζει με τα scaled sprites
        self.rect = pygame.Rect(x, y, 60, 110)
        self.collision_rect = pygame.Rect(x, y, 60, 110)  # Dedicated collision rect
        # Βασικό ύψος/πλάτος (για να τα επαναφέρουμε μετά από shield κλπ.)
        self.base_height = self.rect.height
        self.name = name
        self.hp = 100  # Health points (ζωή)
        self.max_hp = 100  # Μέγιστη ζωή
        self.dir = 1  # Κατεύθυνση: 1 = δεξιά, -1 = αριστερά (πάντα face to face με αντίπαλο)
        self.speed = 5  # Ταχύτητα κίνησης
        self.color = color  # Χρώμα του fighter
        self.is_walking_backward = False  # Αν περπατάει προς τα πίσω (μακριά από αντίπαλο)
        
        # Sprite loader - φορτώνει από assets/sprites/
        self.sprite_loader = None
        if SPRITE_LOADER_AVAILABLE and sprite_path:
            # Convert path σε assets/sprites/
            if sprite_path.startswith("sprites/"):
                sprite_path = sprite_path.replace("sprites/", "assets/sprites/")
            elif not sprite_path.startswith("assets/"):
                sprite_path = f"assets/sprites/{sprite_path}"
            
            if os.path.exists(sprite_path):
                self.sprite_loader = SpriteLoader(sprite_path)

        # Καταστάσεις (states) του fighter
        self.is_attacking = False  # Αν επιτίθεται αυτή τη στιγμή
        self.attack_cooldown = 0  # Χρόνος αναμονής πριν την επόμενη επίθεση
        self.attack_timer = 0  # Timer για attack animation (όταν φτάσει 0, τελειώνει το attack)
        self.is_jumping = False  # Αν είναι στον αέρα
        self.jump_velocity = 0  # Ταχύτητα άλματος
        self.is_shielding = False  # Αν είναι σε θέση shield (αλλάχθηκε από ducking)
        self.invulnerable = False  # Αν είναι προστατευμένος από ζημιά
        self.invulnerable_timer = 0  # Χρόνος που απομένει invulnerability
        self.is_hurt = False  # Αν είναι hurt state
        self.hurt_timer = 0  # Timer για hurt animation
        self.is_dead = False  # Αν είναι dead (KO)
        self.dead_timer = 0  # Timer για dead animation
        self.hit_stun = 0  # Hit stun delay - δεν μπορεί να κάνει action
        self.is_dodging = False  # Αν κάνει dodge (πραγματική αποφυγή)
        self.dodge_cooldown = 0  # Cooldown για dodge
        self.dodge_timer = 0  # Timer για dodge animation
        
        # Animation
        self.animation_frame = 0  # Τρέχον frame animation
        self.walking = False  # Αν περπατάει
        
        # Double hit για Player 2 (με σπαθί - 2 διαδοχικά hits)
        self.is_player2 = (name == "Player 2")  # Έλεγχος αν είναι Player 2
        self.double_hit_active = False  # Αν είναι ενεργό το double hit
        self.double_hit_count = 0  # Μετρητής hits (0, 1, 2)
        self.double_hit_delay = 0  # Delay μεταξύ των hits
        
        # Φυσική (physics)
        self.velocity_y = 0  # Κατακόρυφη ταχύτητα
        # Λίγο πιο έντονο άλμα για να περνάει καθαρά πάνω από τον αντίπαλο
        self.gravity = 0.8  # Βαρύτητα
        self.on_ground = True  # Αν βρίσκεται στο έδαφος
        
    def take_damage(self, amount):
        # Μειώνει την ζωή του fighter
        # Αν δεν είναι invulnerable, δέχεται ζημιά
        if not self.invulnerable and not self.is_dead:
            self.hp -= amount
            if self.hp <= 0:
                self.hp = 0
                # Επιτρέπουμε το attack animation να ολοκληρωθεί πριν γίνει dead
                # Αν είναι attacking, περιμένουμε να τελειώσει το attack_timer
                if not self.is_attacking or self.attack_timer <= 0:
                    self.is_dead = True
                    # Υπολογισμός dead animation duration (μια φορά, όχι loop)
                    dead_frames = 3  # Default
                    if self.sprite_loader:
                        dead_frames = len(self.sprite_loader.sprites.get('dead', []))
                        if dead_frames == 0:
                            dead_frames = 3  # Fallback
                    frames_per_frame = 20  # Κάθε frame κρατάει 20 animation frames
                    total_dead_duration = dead_frames * frames_per_frame
                    self.dead_timer = total_dead_duration  # Timer = total duration για μια φορά animation
                    self.animation_frame = 0  # Reset animation frame για dead animation
                    if self.is_attacking:
                        self.is_attacking = False  # Τερματίζουμε το attack όταν γίνει dead
                        self.attack_timer = 0
            else:
                # Hurt state με hit stun (μια φορά, όχι loop)
                # Κάθε φορά που τρώμε χτύπημα, διακόπτονται οι ενέργειες (attack / walk / shield)
                # ώστε να φαίνεται καθαρά το hurt animation και να μην μπορεί να γίνει spam.
                # Ακύρωση τρέχοντος attack (αν υπάρχει)
                if self.is_attacking:
                    self.is_attacking = False
                    self.attack_timer = 0
                    # Μικρό extra cooldown για να μην ξαναχτυπήσει αμέσως μετά το hurt
                    if self.attack_cooldown < 25:
                        self.attack_cooldown = 25
                # Σταματάμε κίνηση και ασπίδα
                self.walking = False
                self.is_shielding = False
                
                if not self.is_hurt:  # Μόνο αν δεν είναι ήδη hurt
                    self.is_hurt = True
                    self.hurt_timer = 22  # Λίγο μεγαλύτερο hurt animation
                    self.hit_stun = 18   # 18 frames hit stun (δεν μπορεί να κάνει action)
            
            # Μετά την ζημιά, γίνεται προσωρινά invulnerable
            self.invulnerable = True
            self.invulnerable_timer = 30  # 30 frames invulnerability
            
    def attack_hitbox(self):
        # Δημιουργεί το hitbox της επίθεσης
        # Επιστρέφει hitbox μόνο όταν το attack animation είναι στο σωστό frame (hit frame)
        if self.is_attacking and self.attack_timer > 0:
            # Υπολογισμός attack frames
            attack_frames = 4  # Default
            if self.sprite_loader:
                attack_frames = len(self.sprite_loader.sprites.get('attacking', []))
                if attack_frames == 0:
                    attack_frames = 4  # Fallback
            
            frames_per_frame = 6  # Κάθε frame κρατάει 6 animation frames
            total_attack_duration = attack_frames * frames_per_frame
            elapsed_frames = total_attack_duration - self.attack_timer
            
            # Hit frame - στο μέσο του attack animation (όταν το punch είναι πιο μπροστά)
            # Χρησιμοποιούμε το 40-60% του attack animation για hit detection
            hit_start_frame = int(total_attack_duration * 0.4)
            hit_end_frame = int(total_attack_duration * 0.6)
            
            # Ελέγχος αν είμαστε στο hit frame
            # Για Player 2: double hit - 2 χτυπήματα διαδοχικά με καθαρό delay
            if self.is_player2:
                # Double hit: 
                # - πρώτο χτύπημα όταν «βγάζει» το σπαθί (π.χ. 30–40% του animation)
                # - δεύτερο χτύπημα όταν το «μαζεύει» (π.χ. 70–80% του animation)
                hit1_start = int(total_attack_duration * 0.30)
                hit1_end = int(total_attack_duration * 0.40)
                hit2_start = int(total_attack_duration * 0.70)
                hit2_end = int(total_attack_duration * 0.80)
                
                if (hit1_start <= elapsed_frames <= hit1_end) or (hit2_start <= elapsed_frames <= hit2_end):
                    hitbox_width = 50  # Πιο μεγάλο hitbox για sprite
                    hitbox_height = 70
                    # Το hitbox είναι μπροστά από τον fighter, ανάλογα με την κατεύθυνση
                    hitbox_x = self.rect.right if self.dir == 1 else self.rect.left - hitbox_width
                    hitbox_y = self.rect.y + 15  # Πιο πάνω για sprite collision
                    return pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
            else:
                # Normal hit για Player 1
                if hit_start_frame <= elapsed_frames <= hit_end_frame:
                    hitbox_width = 50  # Πιο μεγάλο hitbox για sprite
                    hitbox_height = 70
                    # Το hitbox είναι μπροστά από τον fighter, ανάλογα με την κατεύθυνση
                    hitbox_x = self.rect.right if self.dir == 1 else self.rect.left - hitbox_width
                    hitbox_y = self.rect.y + 15  # Πιο πάνω για sprite collision
                    return pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
        return None
    
    def get_collision_rect(self):
        # Επιστρέφει το collision rectangle (sprite-based)
        # Update collision rect με βάση το rect και το μέγεθος του sprite
        # Λίγο μικρότερο από το ορατό sprite για πιο «δίκαιο» collision
        self.collision_rect.x = self.rect.x + 5  # Μικρό εσωτερικό offset
        self.collision_rect.y = self.rect.y + 5
        self.collision_rect.width = max(10, self.rect.width - 10)
        self.collision_rect.height = max(10, self.rect.height - 10)
        return self.collision_rect
        
    def update(self, keys, controls, arena_rect, opponent_rect=None, opponent_on_ground=None, platform_y=None):
        # Ενημερώνει την κατάσταση του fighter κάθε frame
        # Αν είναι dead, update timers αλλά συνεχίζουμε animation ΜΟΝΟ για το dead
        is_dead_state = self.is_dead
        if is_dead_state:
            # Υπολογισμός total dead animation duration
            dead_frames = 3  # Default
            if self.sprite_loader:
                dead_frames = len(self.sprite_loader.sprites.get('dead', []))
                if dead_frames == 0:
                    dead_frames = 3  # Fallback
            frames_per_frame = 20  # Κάθε frame κρατάει 20 animation frames
            total_dead_duration = dead_frames * frames_per_frame
            
            # Αν το dead_timer > 0, συνεχίζουμε animation (μια φορά)
            if self.dead_timer > 0:
                self.dead_timer -= 1
                # Ενημέρωση animation frame για dead animation (μια φορά, όχι loop)
                elapsed = total_dead_duration - self.dead_timer
                # Προστασία ώστε να μην γίνει αρνητικό
                if elapsed < 0:
                    elapsed = 0
                self.animation_frame = elapsed
            else:
                # Σταματάμε στο τελευταίο frame - stable image
                # Το animation_frame μένει στο τελευταίο frame (δεν κάνει loop)
                last_frame_index = (total_dead_duration - 1) // frames_per_frame
                self.animation_frame = last_frame_index * frames_per_frame  # Σταθερά στο τελευταίο frame
            
            # Απενεργοποίηση όλων των ενεργειών όταν είναι dead
            self.is_attacking = False
            self.attack_timer = 0
            self.walking = False
            self.is_jumping = False
            self.is_shielding = False
            self.is_dodging = False
            self.hit_stun = 0
        
        # Ενημέρωση invulnerability
        if self.invulnerable:
            self.invulnerable_timer -= 1
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                
        # Ενημέρωση hit stun
        if self.hit_stun > 0:
            self.hit_stun -= 1
            
        # Ενημέρωση hurt timer (μια φορά, όχι loop)
        if self.is_hurt:
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.is_hurt = False
                
        # Ενημέρωση dodge cooldown
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
            
        # Ενημέρωση dodge timer
        if self.is_dodging:
            self.dodge_timer -= 1
            if self.dodge_timer <= 0:
                self.is_dodging = False
                self.invulnerable = False
                
        # Ενημέρωση attack cooldown και attack timer
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # Attack timer - όταν φτάσει 0, τελειώνει το attack animation
        if self.attack_timer > 0:
            self.attack_timer -= 1
        else:
            if self.is_attacking:
                self.is_attacking = False
            # Αν το HP είναι 0 και τελείωσε το attack, γίνεται dead
            if self.hp <= 0 and not self.is_dead:
                self.is_dead = True
                # Υπολογισμός dead animation duration (ίδιος τρόπος παντού)
                dead_frames = 3  # Default
                if self.sprite_loader:
                    dead_frames = len(self.sprite_loader.sprites.get('dead', []))
                    if dead_frames == 0:
                        dead_frames = 3  # Fallback
                frames_per_frame = 20  # Κάθε frame κρατάει 20 animation frames
                total_dead_duration = dead_frames * frames_per_frame
                self.dead_timer = total_dead_duration
                self.animation_frame = 0  # Reset animation frame για dead animation
            
        # Βαρύτητα και άλμα - το sprite μεταφέρεται στον αέρα
        if not self.on_ground:
            # Αν είναι στον αέρα, εφαρμόζεται βαρύτητα
            self.velocity_y += self.gravity
            # Μετακίνηση στον αέρα (το rect.y αλλάζει)
            self.rect.y += self.velocity_y
            
            # Έλεγχος collision με το έδαφος (platform πιο κάτω)
            if platform_y is None:
                platform_y = SCREEN_HEIGHT - 20  # Fallback
            if self.rect.bottom >= platform_y:
                self.rect.bottom = platform_y
                self.on_ground = True
                self.velocity_y = 0
                self.is_jumping = False
        else:
            # Αν είναι στο έδαφος, το rect.bottom είναι πάντα στο platform_y
            if platform_y is None:
                platform_y = SCREEN_HEIGHT - 20  # Fallback
            # Πάντα θέτουμε το bottom στο platform_y όταν είναι στο έδαφος
            if not self.is_dodging:  # Μόνο αν δεν κάνει dodge
                self.rect.bottom = platform_y
            self.velocity_y = 0
            self.on_ground = True  # Βεβαιώνουμε ότι είναι στο έδαφος
            
        # Ανάγνωση inputs από τα πλήκτρα
        move_left = keys[controls['left']]
        move_right = keys[controls['right']]
        jump = keys[controls['jump']]
        duck = keys[controls['duck']]
        attack = keys[controls['attack']]
            
        # Shield (ασπίδα) - σταθερή στάση, χωρίς dash / μετακίνηση
        # Το ίδιο κουμπί (S / Arrow Down) τώρα κάνει μόνο shield, όχι dodge
        # ΔΕΝ επιτρέπεται να ξεκινήσει shield ενώ παίζει attack / hurt / dead animation.
        if (not is_dead_state and
            duck and
            self.on_ground and
            self.hit_stun == 0 and
            not self.is_attacking and  # Δεν βάζουμε ασπίδα πάνω σε επίθεση
            not self.is_hurt):         # Ούτε πάνω σε hurt
            # Shielding (shield) - προστατεύει από attacks
            if not self.is_shielding:
                # Μόνο όταν ξεκινάει το shield - αποθηκεύουμε το bottom για να μην μετακινηθεί
                old_bottom = self.rect.bottom
                self.is_shielding = True
                self.rect.height = int(self.base_height * 0.6)  # Μικρότερο ύψος όταν shield
                self.rect.bottom = old_bottom  # Διατηρούμε το ίδιο bottom για να μην μετακινηθεί
            self.invulnerable = True  # Shield - προστατεύει από attacks
            self.invulnerable_timer = 5  # Μικρό timer για να ανανεώνεται όσο κρατάμε το κουμπί
        else:
            # Όταν σταματάμε να πατάμε την ασπίδα, επανέρχεται στο κανονικό ύψος
            if self.is_shielding:
                old_bottom = self.rect.bottom
                self.is_shielding = False
                self.rect.height = self.base_height  # Κανονικό ύψος
                self.rect.bottom = old_bottom  # Διατηρούμε το ίδιο bottom
            else:
                self.is_shielding = False
                self.rect.height = self.base_height  # Κανονικό ύψος
            
        # Jumping (άλμα) - το sprite μεταφέρεται στον αέρα
        # Δεν επιτρέπεται άλμα όσο παίζει attack / hurt / dead animation.
        if (not is_dead_state and
            jump and
            self.on_ground and
            not self.is_shielding and
            self.hit_stun == 0 and
            not self.is_dodging and
            not self.is_attacking and
            not self.is_hurt):
            self.is_jumping = True
            self.on_ground = False
            # Βεβαιώνουμε ότι το rect.bottom είναι στο platform_y πριν το jump
            if platform_y is not None:
                self.rect.bottom = platform_y
            # Πιο δυνατό άλμα ώστε το sprite να περνάει πάνω από τον αντίπαλο
            self.velocity_y = -22  # Αρχική ταχύτητα προς τα πάνω
            # Το rect.y θα αλλάξει από το gravity update
            
        # Οριζόντια κίνηση με face-to-face logic (πάντα κοιτάνε ο ένας τον άλλο)
        if not is_dead_state and self.hit_stun == 0 and not self.is_dodging:
            # Προσδιορισμός direction βάσει θέσης αντίπαλου (face to face)
            if opponent_rect is not None:
                if self.rect.centerx < opponent_rect.centerx:
                    self.dir = 1  # Κοιτάει δεξιά (προς αντίπαλο)
                else:
                    self.dir = -1  # Κοιτάει αριστερά (προς αντίπαλο)
            
            # Κίνηση με backward walk logic + collision detection
            self.is_walking_backward = False
            new_x = self.rect.x  # Προσωρινή θέση για collision check
            
            if move_left and not self.is_attacking and not self.is_shielding:
                # Έλεγχος αν πηγαίνει προς ή μακριά από αντίπαλο
                if opponent_rect is not None:
                    # Αν κινείται αριστερά και ο αντίπαλος είναι αριστερά = πηγαίνει προς αντίπαλο (forward)
                    # Αν κινείται αριστερά και ο αντίπαλος είναι δεξιά = πηγαίνει μακριά (backward)
                    if self.rect.centerx < opponent_rect.centerx:
                        # Αντίπαλος είναι δεξιά, κινείται αριστερά = backward
                        self.is_walking_backward = True
                    # else: forward (αλλά dir = 1, οπότε θα κινηθεί προς αντίπαλο)
                
                # Collision check πριν την κίνηση
                new_x = self.rect.x - self.speed
                test_rect = pygame.Rect(new_x, self.rect.y, self.rect.width, self.rect.height)
                # Αν δεν υπάρχει collision με αντίπαλο (ή ο αντίπαλος είναι στον αέρα), κινείται
                if opponent_rect is None or not test_rect.colliderect(opponent_rect) or (opponent_on_ground is not None and not opponent_on_ground) or not self.on_ground:
                    self.rect.x = new_x
                    self.walking = True
                else:
                    self.walking = False
            elif move_right and not self.is_attacking and not self.is_shielding:
                # Έλεγχος αν πηγαίνει προς ή μακριά από αντίπαλο
                if opponent_rect is not None:
                    # Αν κινείται δεξιά και ο αντίπαλος είναι δεξιά = πηγαίνει μακριά (backward)
                    # Αν κινείται δεξιά και ο αντίπαλος είναι αριστερά = πηγαίνει προς αντίπαλο (forward)
                    if self.rect.centerx > opponent_rect.centerx:
                        # Αντίπαλος είναι αριστερά, κινείται δεξιά = backward
                        self.is_walking_backward = True
                    # else: forward
                
                # Collision check πριν την κίνηση
                new_x = self.rect.x + self.speed
                test_rect = pygame.Rect(new_x, self.rect.y, self.rect.width, self.rect.height)
                # Αν δεν υπάρχει collision με αντίπαλο (ή ο αντίπαλος είναι στον αέρα), κινείται
                if opponent_rect is None or not test_rect.colliderect(opponent_rect) or (opponent_on_ground is not None and not opponent_on_ground) or not self.on_ground:
                    self.rect.x = new_x
                    self.walking = True
                else:
                    self.walking = False
            else:
                self.walking = False
                self.is_walking_backward = False
        else:
            self.walking = False
            self.is_walking_backward = False
            
        # Animation frame update (για smooth animations)
        # Το dead animation frame update γίνεται στο dead state check παραπάνω
        # Όταν είναι dead, ΔΕΝ πειράζουμε εδώ το animation_frame για να μην κάνει μικρό loop στο τέλος
        if not is_dead_state:
            if self.is_dodging:
                # Dodge animation - χρησιμοποιεί shield animation
                self.animation_frame = (self.animation_frame + 1) % 20
            elif self.walking:
                # Walking animation - ίδια για forward και backward (το sprite flip θα το χειριστεί)
                self.animation_frame = (self.animation_frame + 1) % 40
            elif self.is_attacking:
                # Attack animation - αυξάνει το frame μέχρι να τελειώσει το attack_timer
                if self.attack_timer > 0:
                    self.animation_frame += 1
                else:
                    self.animation_frame = 0
            elif self.is_jumping or not self.on_ground:
                self.animation_frame = (self.animation_frame + 1) % 30
            elif self.is_shielding:
                self.animation_frame = (self.animation_frame + 1) % 20
            else:
                self.animation_frame = (self.animation_frame + 1) % 48
            
        # Επίθεση με cooldown για να μην γίνεται spam
        if not is_dead_state and attack and self.attack_cooldown == 0 and not self.is_jumping and not self.is_shielding and self.hit_stun == 0 and not self.is_dodging and not self.is_attacking:
            self.is_attacking = True
            self.attack_cooldown = 45  # 0.75 δευτερόλεπτα cooldown (45 frames)
            # Υπολογισμός attack_timer βάσει πλήθους attack frames (dynamic)
            attack_frames = 4  # Default
            if self.sprite_loader:
                attack_frames = len(self.sprite_loader.sprites.get('attacking', []))
                if attack_frames == 0:
                    attack_frames = 4  # Fallback
            frames_per_frame = 6  # Κάθε frame κρατάει 6 animation frames
            self.attack_timer = attack_frames * frames_per_frame  # Dynamic attack duration
            self.animation_frame = 0  # Reset animation frame για attack
            
        # Διατήρηση fighter μέσα στην πίστα
        if self.rect.left < arena_rect.left:
            self.rect.left = arena_rect.left
        if self.rect.right > arena_rect.right:
            self.rect.right = arena_rect.right
            
    def reset_state(self):
        # Επαναφέρει την κατάσταση του fighter για νέο round
        self.hp = 100
        self.is_attacking = False
        self.attack_cooldown = 0
        self.attack_timer = 0
        self.is_jumping = False
        self.is_shielding = False
        self.is_hurt = False
        self.is_dead = False
        self.is_dodging = False
        self.hurt_timer = 0
        self.dead_timer = 0
        self.hit_stun = 0
        self.dodge_cooldown = 0
        self.dodge_timer = 0
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.velocity_y = 0
        self.on_ground = True
        self.is_walking_backward = False
            
    def draw(self, screen, arena_rect=None):
        # Σχεδιάζει τον fighter στην οθόνη με sprites/animations
        if arena_rect is None:
            arena_rect = self.rect  # Fallback
        
        # Flash effect - ΜΟΝΟ για dodge, ΟΧΙ για hurt ή shield
        # Όταν είναι hurt ή shield, θέλουμε να φαίνεται το animation, όχι flash
        # Το flash είναι μόνο για dodge (is_dodging = True)
        # Αν είναι hurt (ακόμα και αν το hurt_timer τελείωσε) ή shield, δεν flash
        should_flash = (self.invulnerable and 
                       self.invulnerable_timer % 4 < 2 and 
                       not self.is_dead and 
                       not self.is_hurt and  # Όχι όταν είναι hurt
                       not self.is_shielding and  # Όχι όταν είναι shield
                       self.is_dodging)  # Μόνο για dodge
        
        if should_flash:
            # Flash effect - δεν σχεδιάζεται (κάνει blink) - μόνο για dodge
            pass
        else:
            # Προσδιορισμός κατάστασης για animation (priority order)
            animation_name = None
            if self.is_dead:
                animation_name = 'dead'
            elif self.is_dodging:
                animation_name = 'shield'  # Χρησιμοποιούμε shield animation για dodge
            elif self.is_hurt and self.hurt_timer > 0:
                animation_name = 'hurt'
            elif self.is_shielding:
                animation_name = 'shield'
            elif self.is_jumping or not self.on_ground:
                animation_name = 'jumping'
            elif self.is_attacking:
                animation_name = 'attacking'
            elif self.walking:
                animation_name = 'walking'
            else:
                animation_name = 'idle'
            
            # Προσπάθεια να χρησιμοποιήσουμε sprites
            if self.sprite_loader and self.sprite_loader.has_sprites(animation_name):
                self._draw_with_sprites(screen, animation_name, arena_rect)
            else:
                # Fallback σε procedural drawing
                if animation_name == 'dead':
                    self._draw_dead(screen)
                elif animation_name == 'hurt':
                    self._draw_hurt(screen)
                elif animation_name == 'shield':
                    self._draw_shield(screen)
                elif animation_name == 'jumping':
                    self._draw_jumping(screen)
                elif animation_name == 'attacking':
                    self._draw_attacking(screen)
                elif animation_name == 'walking':
                    self._draw_walking(screen)
                else:
                    self._draw_idle(screen)
            
        # Attack hitbox δεν εμφανίζεται (αφαιρέθηκε το κίτρινο outline)
    
    def _draw_with_sprites(self, screen, animation_name, arena_rect):
        # Σχεδιάζει τον fighter χρησιμοποιώντας sprites - dynamic frame calculation
        # Πρώτα παίρνουμε το πλήθος frames για αυτή την animation από τον sprite_loader
        total_frames = 0
        if self.sprite_loader:
            total_frames = len(self.sprite_loader.sprites.get(animation_name, []))
        
        # Αν δεν υπάρχουν frames, fallback
        if total_frames == 0:
            total_frames = 1  # Minimum 1 frame
        
        frame_index = 0
        
        if animation_name == 'idle':
            # Idle animation - loop
            frames_per_frame = 8  # Κάθε frame κρατάει 8 animation frames
            frame_index = (self.animation_frame // frames_per_frame) % total_frames
        elif animation_name == 'walking':
            # Walking animation - loop
            frames_per_frame = 5  # Κάθε frame κρατάει 5 animation frames
            frame_index = (self.animation_frame // frames_per_frame) % total_frames
        elif animation_name == 'attacking':
            # Attack animation - παίρνει όλα τα frames μια φορά
            frames_per_frame = 6  # Κάθε frame κρατάει 6 animation frames
            if self.attack_timer > 0:
                # Υπολογισμός frame index βάσει attack_timer
                # Υπολογισμός total attack duration (dynamic)
                attack_frames = len(self.sprite_loader.sprites.get('attacking', [])) if self.sprite_loader else 4
                if attack_frames == 0:
                    attack_frames = 4
                total_attack_duration = attack_frames * 6  # frames_per_frame = 6
                elapsed_frames = (total_attack_duration - self.attack_timer)
                frame_index = min(total_frames - 1, elapsed_frames // frames_per_frame)
            else:
                frame_index = 0
        elif animation_name == 'jumping':
            # Jump animation - βάσει jump progress
            if not self.on_ground:
                # Calculate based on velocity (going up or down)
                if self.velocity_y < 0:
                    # Going up - πρώτα μισό των frames
                    up_frames = total_frames // 2
                    # Προσαρμογή στο νέο πιο δυνατό άλμα (max ~22)
                    jump_progress = min(1.0, abs(self.velocity_y) / 22.0)
                    frame_index = min(up_frames - 1, int(jump_progress * up_frames))
                else:
                    # Going down - δεύτερο μισό των frames
                    up_frames = total_frames // 2
                    down_frames = total_frames - up_frames
                    jump_progress = min(1.0, self.velocity_y / 22.0)
                    frame_index = min(total_frames - 1, up_frames + int(jump_progress * down_frames))
            else:
                frame_index = 0
        elif animation_name == 'shield':
            # Shield animation - χρησιμοποιείται και για dodge
            if self.is_dodging:
                # Dodge animation - πιο γρήγορη
                frames_per_frame = 5
                frame_index = (self.animation_frame // frames_per_frame) % total_frames
            else:
                # Normal shield animation
                frames_per_frame = 10
                frame_index = (self.animation_frame // frames_per_frame) % total_frames
        elif animation_name == 'hurt':
            # Hurt animation - μια φορά, όχι loop
            # Χρησιμοποιούμε hurt_timer για να υπολογίσουμε το frame
            # Το hurt_timer ξεκινάει από 20 και μειώνεται
            if total_frames == 1:
                frame_index = 0
            elif total_frames == 2:
                # 2 frames: frame 0 για πρώτα 10 frames, frame 1 για τα υπόλοιπα
                frame_index = 0 if self.hurt_timer > 10 else 1
            else:  # 3+ frames
                # 3+ frames: κατανέμουμε τα frames σε 3 ομάδες
                frames_per_group = 20 // total_frames if total_frames > 0 else 1
                frame_index = min(total_frames - 1, (20 - self.hurt_timer) // max(1, frames_per_group))
        elif animation_name == 'dead':
            # Dead animation - μια φορά, σταματάει στο τελευταίο frame (stable image)
            frames_per_frame = 20  # Κάθε frame κρατάει 20 animation frames
            # Υπολογισμός frame index βάσει animation_frame (που δεν κάνει loop)
            calculated_frame = self.animation_frame // frames_per_frame
            # Αν το dead_timer == 0, είμαστε στο τελευταίο frame (stable)
            if self.dead_timer <= 0:
                frame_index = total_frames - 1  # Πάντα τελευταίο frame όταν σταμάτησε
            else:
                frame_index = min(total_frames - 1, calculated_frame)
        
        sprite = self.sprite_loader.get_sprite(animation_name, frame_index, self.dir)
        if sprite:
            # Scale sprite για μεγαλύτερο μέγεθος (2.7x - πιο μεγάλοι χαρακτήρες)
            sprite_width = int(sprite.get_width() * 2.7)
            sprite_height = int(sprite.get_height() * 2.7)
            sprite = pygame.transform.scale(sprite, (sprite_width, sprite_height))
            
            # Position sprite - χρησιμοποιούμε το rect.bottom που είναι ήδη στο platform_y
            sprite_rect = sprite.get_rect()
            sprite_rect.centerx = self.rect.centerx
            # Χρησιμοποιούμε πάντα το rect.bottom για positioning (είναι στο platform_y όταν on_ground)
            sprite_rect.bottom = self.rect.bottom
            screen.blit(sprite, sprite_rect)
    
    def _draw_idle(self, screen):
        # Σχεδιάζει idle animation
        # Σώμα
        body_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 20, 40, 60)
        pygame.draw.rect(screen, self.color, body_rect)
        # Κεφάλι
        head_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 5, 30, 25)
        pygame.draw.ellipse(screen, self.color, head_rect)
        # Μάτια
        eye_x = self.rect.centerx + (8 * self.dir)
        pygame.draw.circle(screen, WHITE, (eye_x, self.rect.y + 15), 4)
        pygame.draw.circle(screen, BLACK, (eye_x, self.rect.y + 15), 2)
        # Χέρια
        hand_y = self.rect.y + 35
        pygame.draw.circle(screen, self.color, (self.rect.x + 5, hand_y), 6)
        pygame.draw.circle(screen, self.color, (self.rect.right - 5, hand_y), 6)
        # Πόδια
        leg_y = self.rect.bottom - 20
        pygame.draw.rect(screen, self.color, (self.rect.x + 15, leg_y, 12, 20))
        pygame.draw.rect(screen, self.color, (self.rect.right - 27, leg_y, 12, 20))
    
    def _draw_walking(self, screen):
        # Σχεδιάζει walking animation
        frame_offset = int(self.animation_frame / 5) % 2  # 0 ή 1
        leg_offset = 5 if frame_offset == 0 else -5
        
        # Σώμα
        body_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 20, 40, 60)
        pygame.draw.rect(screen, self.color, body_rect)
        # Κεφάλι
        head_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 5, 30, 25)
        pygame.draw.ellipse(screen, self.color, head_rect)
        # Μάτια
        eye_x = self.rect.centerx + (8 * self.dir)
        pygame.draw.circle(screen, WHITE, (eye_x, self.rect.y + 15), 4)
        pygame.draw.circle(screen, BLACK, (eye_x, self.rect.y + 15), 2)
        # Χέρια (κουνιούνται)
        hand_y = self.rect.y + 35
        hand_offset = -3 if frame_offset == 0 else 3
        pygame.draw.circle(screen, self.color, (self.rect.x + 5, hand_y + hand_offset), 6)
        pygame.draw.circle(screen, self.color, (self.rect.right - 5, hand_y - hand_offset), 6)
        # Πόδια (κουνιούνται)
        leg_y = self.rect.bottom - 20
        pygame.draw.rect(screen, self.color, (self.rect.x + 15, leg_y + leg_offset, 12, 20))
        pygame.draw.rect(screen, self.color, (self.rect.right - 27, leg_y - leg_offset, 12, 20))
    
    def _draw_attacking(self, screen):
        # Σχεδιάζει attacking animation
        # Σώμα (λίγο προς τα εμπρός)
        body_x = self.rect.x + 10 + (5 * self.dir)
        body_rect = pygame.Rect(body_x, self.rect.y + 20, 40, 60)
        pygame.draw.rect(screen, self.color, body_rect)
        # Κεφάλι
        head_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 5, 30, 25)
        pygame.draw.ellipse(screen, self.color, head_rect)
        # Μάτια
        eye_x = self.rect.centerx + (8 * self.dir)
        pygame.draw.circle(screen, WHITE, (eye_x, self.rect.y + 15), 4)
        pygame.draw.circle(screen, BLACK, (eye_x, self.rect.y + 15), 2)
        # Χέρι που χτυπάει (επεκτείνεται)
        punch_x = self.rect.right if self.dir == 1 else self.rect.x - 20
        punch_y = self.rect.y + 40
        pygame.draw.rect(screen, self.color, (punch_x, punch_y, 20, 15))
        # Άλλο χέρι
        other_hand_x = self.rect.x + 5 if self.dir == 1 else self.rect.right - 5
        pygame.draw.circle(screen, self.color, (other_hand_x, self.rect.y + 35), 6)
        # Πόδια
        leg_y = self.rect.bottom - 20
        pygame.draw.rect(screen, self.color, (self.rect.x + 15, leg_y, 12, 20))
        pygame.draw.rect(screen, self.color, (self.rect.right - 27, leg_y, 12, 20))
    
    def _draw_jumping(self, screen):
        # Σχεδιάζει jumping animation
        # Σώμα (λίγο στριμμένο)
        body_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 20, 40, 50)
        pygame.draw.rect(screen, self.color, body_rect)
        # Κεφάλι
        head_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 5, 30, 25)
        pygame.draw.ellipse(screen, self.color, head_rect)
        # Μάτια
        eye_x = self.rect.centerx + (8 * self.dir)
        pygame.draw.circle(screen, WHITE, (eye_x, self.rect.y + 15), 4)
        pygame.draw.circle(screen, BLACK, (eye_x, self.rect.y + 15), 2)
        # Χέρια (ψηλά)
        pygame.draw.circle(screen, self.color, (self.rect.x + 5, self.rect.y + 30), 6)
        pygame.draw.circle(screen, self.color, (self.rect.right - 5, self.rect.y + 30), 6)
        # Πόδια (συγκρατημένα)
        leg_y = self.rect.bottom - 15
        pygame.draw.rect(screen, self.color, (self.rect.x + 15, leg_y, 12, 15))
        pygame.draw.rect(screen, self.color, (self.rect.right - 27, leg_y, 12, 15))
    
    def _draw_shield(self, screen):
        # Σχεδιάζει shield animation
        # Σώμα (μικρότερο)
        body_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 30, 40, 30)
        pygame.draw.rect(screen, self.color, body_rect)
        # Κεφάλι
        head_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 10, 30, 20)
        pygame.draw.ellipse(screen, self.color, head_rect)
        # Μάτια
        eye_x = self.rect.centerx + (8 * self.dir)
        pygame.draw.circle(screen, WHITE, (eye_x, self.rect.y + 20), 3)
        pygame.draw.circle(screen, BLACK, (eye_x, self.rect.y + 20), 2)
        # Χέρια (κάτω)
        pygame.draw.circle(screen, self.color, (self.rect.x + 5, self.rect.y + 45), 5)
        pygame.draw.circle(screen, self.color, (self.rect.right - 5, self.rect.y + 45), 5)
        # Πόδια (κάθισμα)
        leg_y = self.rect.bottom - 10
        pygame.draw.rect(screen, self.color, (self.rect.x + 10, leg_y, 15, 10))
        pygame.draw.rect(screen, self.color, (self.rect.right - 25, leg_y, 15, 10))