#!/usr/bin/env python
# Βοηθητικές κλάσεις για τον έλεγχο του CPU opponent
# KeyState: προσομοιώνει το pygame.key.get_pressed() για τον CPU
# CPUController: AI που κινεί τον CPU (επίθεση, άμυνα, άλμα, κίνηση)

import pygame
import random


class KeyState:
    # Μικρή κλάση που μιμείται το pygame.key.get_pressed() για να δίνουμε fake πλήκτρα στον CPU
    
    def __init__(self):
        # Αρχικοποίηση με κενό dictionary για τα πλήκτρα που είναι "πατημένα"
        self.keys = {}
        
    def __getitem__(self, key):
        # Επιτρέπει πρόσβαση τύπου keys[key] και επιστρέφει True/False αν είναι πατημένο
        return self.keys.get(key, False)
        
    def set_key(self, key, value):
        # Ορίζει αν ένα συγκεκριμένο pygame key (π.χ. K_LEFT) θεωρείται πατημένο ή όχι
        self.keys[key] = value


class CPUController:
    # Κλάση AI που αποφασίζει κινήσεις για τον CPU (πλησιάζει, επιτίθεται, αμύνεται, πηδά)
    
    def __init__(self, fighter, opponent, difficulty="normal"):
        # Αρχικοποίηση CPU controller με τον fighter του CPU, τον αντίπαλο και το επίπεδο δυσκολίας
        self.fighter = fighter
        self.opponent = opponent
        # Επίπεδο δυσκολίας: "easy", "normal", "hard"
        self.difficulty = difficulty
        self.action_timer = 0  # Timer για το πόσο θα κρατήσει η τρέχουσα ενέργεια
        self.current_action = None  # Η τρέχουσα ενέργεια
        self.attack_cooldown = 0  # Cooldown για attacks
        self.attack_windup = 0    # Μικρή καθυστέρηση πριν πατήσει το attack
        self.defend_cooldown = 0  # Cooldown για defend (shield)
        self.jump_cooldown = 0  # Cooldown για jump
        self.last_action = None  # Προηγούμενη ενέργεια

    def _difficulty_scale(self, easy_value, normal_value, hard_value):
        # Βοηθητική συνάρτηση: διαλέγει τιμή ανάλογα με το difficulty (easy/normal/hard)
        if self.difficulty == "easy":
            return easy_value
        if self.difficulty == "hard":
            return hard_value
        return normal_value
        
    def update(self):
        # Κύρια συνάρτηση AI: καλείται κάθε frame και παράγει τα "εικονικά" πλήκτρα του CPU
        self.action_timer -= 1
        self.attack_cooldown = max(0, self.attack_cooldown - 1)
        self.defend_cooldown = max(0, self.defend_cooldown - 1)
        self.jump_cooldown = max(0, self.jump_cooldown - 1)

        # Αν ο CPU fighter είναι νεκρός ή σε hit-stun/hurt, δεν στέλνουμε καθόλου inputs
        # ώστε να φαίνεται καθαρά το KO / hurt animation και να μην μπορεί να κάνει spam.
        if self.fighter.is_dead:
            return KeyState()

        if self.fighter.is_hurt or self.fighter.hit_stun > 0:
            # Καθαρίζουμε το current_action ώστε μετά το stun να διαλέξει κάτι νέο
            self.current_action = None
            self.action_timer = 0
            self.attack_windup = 0
            return KeyState()
        
        # Υπολογισμός απόστασης από τον αντίπαλο
        distance = abs(self.fighter.rect.centerx - self.opponent.rect.centerx)
        vertical_distance = abs(self.fighter.rect.centery - self.opponent.rect.centery)
        
        # Έλεγχος αν ο αντίπαλος επιτίθεται (για defend/shield)
        opponent_attacking = self.opponent.is_attacking
        opponent_hitbox = self.opponent.attack_hitbox()
        should_defend = False
        
        # Defend αν ο αντίπαλος επιτίθεται και είναι κοντά (ανάλογα με το difficulty)
        defend_reaction_distance = self._difficulty_scale(60, 80, 110)
        if opponent_attacking and opponent_hitbox and self.defend_cooldown == 0:
            # Αν το hitbox είναι πολύ κοντά στον CPU
            if distance < defend_reaction_distance and opponent_hitbox.colliderect(self.fighter.rect.inflate(20, 0)):
                defend_chance = self._difficulty_scale(0.3, 0.55, 0.85)
                if random.random() < defend_chance:
                    should_defend = True
                    # Cooldown ώστε να μην κάνει συνεχώς perfect block
                    self.defend_cooldown = self._difficulty_scale(120, 90, 60)
        
        # Αν έληξε ο timer, αποφασίζει νέα ενέργεια
        if self.action_timer <= 0:
            # Priority 1: Defend αν χρειάζεται
            if should_defend:
                self.current_action = 'shield'
                self.action_timer = self._difficulty_scale(15, 20, 25)
                self.last_action = 'shield'
            # Priority 2: Jump αν ο αντίπαλος είναι στον αέρα ή αν είναι πολύ κοντά
            elif (self.opponent.is_jumping or not self.opponent.on_ground or vertical_distance > 80) and \
                    self.jump_cooldown == 0 and random.random() < self._difficulty_scale(0.2, 0.35, 0.5):
                self.current_action = 'jump'
                self.action_timer = 10
                self.jump_cooldown = self._difficulty_scale(120, 90, 70)
                self.last_action = 'jump'
            # Priority 3: Attack αν είναι κοντά (πιο επιθετικός)
            elif distance < self._difficulty_scale(120, 150, 180) and \
                    self.attack_cooldown == 0 and \
                    random.random() < self._difficulty_scale(0.4, 0.7, 0.9):
                self.current_action = 'attack'
                self.action_timer = 30
                self.attack_cooldown = self._difficulty_scale(55, 40, 30)
                # Μικρό windup πριν την επίθεση για να προλαβαίνει ο παίκτης να δει το χτύπημα
                self.attack_windup = self._difficulty_scale(10, 6, 3)
                self.last_action = 'attack'
            # Priority 4: Move προς τον αντίπαλο (πιο γρήγορα)
            elif distance > self._difficulty_scale(140, 120, 100):
                if self.fighter.rect.centerx < self.opponent.rect.centerx:
                    self.current_action = 'move_right'
                else:
                    self.current_action = 'move_left'
                self.action_timer = random.randint(15, 30)
                self.last_action = 'move'
            # Priority 5: Back off αν είναι πολύ κοντά (πιο συχνά)
            elif distance < self._difficulty_scale(70, 90, 110) and \
                    random.random() < self._difficulty_scale(0.3, 0.5, 0.65):
                if self.fighter.rect.centerx < self.opponent.rect.centerx:
                    self.current_action = 'move_left'
                else:
                    self.current_action = 'move_right'
                self.action_timer = random.randint(10, 20)
                self.last_action = 'back_off'
            # Priority 6: Attack combo - πολλαπλές επιθέσεις
            elif distance < self._difficulty_scale(80, 100, 130) and \
                    self.attack_cooldown == 0 and \
                    random.random() < self._difficulty_scale(0.25, 0.5, 0.7):
                self.current_action = 'attack'
                self.action_timer = 30
                self.attack_cooldown = 35
                self.last_action = 'attack'
            # Default: Move προς τον αντίπαλο
            else:
                if self.fighter.rect.centerx < self.opponent.rect.centerx:
                    self.current_action = 'move_right'
                else:
                    self.current_action = 'move_left'
                self.action_timer = random.randint(15, 30)
                self.last_action = 'move'
                
        # Δημιουργία fake key state για τον CPU
        fake_keys = KeyState()
        
        # Εκτέλεση της τρέχουσας ενέργειας
        # Σημείωση: Ο έλεγχος για cooldown γίνεται ΜΟΝΟ στη φάση απόφασης πιο πάνω.
        # Για το attack έχουμε και μικρό "windup" πριν πατηθεί το πλήκτρο, ώστε να μην
        # είναι instant και να προλαβαίνει ο παίκτης να αντιδράσει.
        if self.current_action == 'attack':
            if self.attack_windup > 0:
                self.attack_windup -= 1
            else:
                fake_keys.set_key(pygame.K_RCTRL, True)  # Attack
        elif self.current_action == 'shield':
            fake_keys.set_key(pygame.K_DOWN, True)  # Defend / shield
        elif self.current_action == 'jump':
            fake_keys.set_key(pygame.K_UP, True)  # Jump
        elif self.current_action == 'move_left':
            fake_keys.set_key(pygame.K_LEFT, True)  # Κίνηση αριστερά
        elif self.current_action == 'move_right':
            fake_keys.set_key(pygame.K_RIGHT, True)  # Κίνηση δεξιά
            
        return fake_keys