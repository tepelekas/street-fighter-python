class RoundManager:
    # Κλάση που διαχειρίζεται τους γύρους, το countdown και το best of 3 (ποιος κερδίζει το ματς)
    
    def __init__(self):
        # Αρχικοποίηση round manager (γύρος, νίκες, timers, κατάσταση)
        self.round_num = 1  # Τρέχων γύρος
        self.wins_p1 = 0  # Νίκες Player 1
        self.wins_p2 = 0  # Νίκες Player 2
        # Καταστάσεις: COUNTDOWN, FIGHT, ROUND_END, MATCH_END
        self.state = "COUNTDOWN"
        self.countdown_timer = 180  # 3 δευτερόλεπτα σε frames (60 FPS)
        self.countdown_text = "3"  # Το κείμενο που εμφανίζεται
        self.round_end_timer = 180  # Timer για το τέλος του round
        self.winner = None  # Νικητής του round ("P1" ή "P2")
        
    def update(self, fighter1, fighter2):
        # Ενημέρωση round manager κάθε frame με βάση την ζωή των fighters
        if self.state == "COUNTDOWN":
            # Κατάσταση countdown - εμφανίζει "3 2 1 FIGHT!"
            self.countdown_timer -= 1
            if self.countdown_timer > 120:
                self.countdown_text = "3"
            elif self.countdown_timer > 60:
                self.countdown_text = "2"
            elif self.countdown_timer > 30:
                self.countdown_text = "1"
            elif self.countdown_timer > 0:
                self.countdown_text = "FIGHT!"  # "FIGHT!" στα αγγλικά
            else:
                self.countdown_text = ""
                self.state = "FIGHT"  # Ξεκινάει ο αγώνας
                
        elif self.state == "FIGHT":
            # Κατάσταση αγώνα - ελέγχει για KO
            if fighter1.hp <= 0 and fighter1.is_dead:
                # Player 1 έχασε
                self.wins_p2 += 1
                self.winner = "P2"
                self.state = "ROUND_END"
                self.round_end_timer = 180
            elif fighter2.hp <= 0 and fighter2.is_dead:
                # Player 2 έχασε
                self.wins_p1 += 1
                self.winner = "P1"
                self.state = "ROUND_END"
                self.round_end_timer = 180
                
        elif self.state == "ROUND_END":
            # Κατάσταση τέλους round - εμφανίζει KO
            self.round_end_timer -= 1
            if self.round_end_timer <= 0:
                # Έλεγχος αν τελείωσε το match (best of 3)
                if self.wins_p1 >= 2 or self.wins_p2 >= 2:
                    # Κάποιος έχει 2 νίκες - τέλος match
                    self.state = "MATCH_END"
                else:
                    # Επόμενος γύρος
                    self.round_num += 1
                    self.state = "COUNTDOWN"
                    self.countdown_timer = 180
                    # Επαναφορά fighters
                    fighter1.reset_state()
                    fighter2.reset_state()
                    # Reset dead state
                    fighter1.is_dead = False
                    fighter2.is_dead = False
                    # Επαναφορά θέσεων - θα γίνει από το Game.reset_fighter_positions()
                    
    def reset(self):
        # Επαναφορά round manager στην αρχική κατάσταση όταν ξεκινάει νέο match
        self.round_num = 1
        self.wins_p1 = 0
        self.wins_p2 = 0
        self.state = "COUNTDOWN"
        self.countdown_timer = 180
        self.countdown_text = "3"
        self.winner = None