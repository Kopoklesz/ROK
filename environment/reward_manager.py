"""
Reward Manager - Jutalom számítás és detektálás
"""
import time
import numpy as np
from typing import Dict, Optional, Tuple

from config.settings import REWARD_WEIGHTS, DEBUG_MODE


class RewardManager:
    """Központi reward számítás"""
    
    def __init__(self, image_manager):
        self.image_mgr = image_manager
        
        # Állapot tracking
        self.prev_state = None
        self.prev_screenshot = None
        self.last_action_time = time.time()
        self.prev_power = 0
        self.prev_queue_count = 0
        
        # Reward weights (config-ból)
        self.rewards = REWARD_WEIGHTS.copy()
        
        # Statisztikák
        self.total_rewards = 0.0
        self.reward_breakdown = {key: 0.0 for key in self.rewards}
    
    def calculate_reward(self, current_state: Dict, action: Dict) -> Tuple[float, Dict]:
        """
        Teljes reward számítás
        
        Args:
            current_state: Jelenlegi állapot dict
            action: Végrehajtott akció dict
            
        Returns:
            (reward_value, breakdown_dict)
        """
        total_reward = 0.0
        breakdown = {}
        
        # Első futás inicializálás
        if self.prev_state is None:
            self.prev_state = current_state
            self.prev_screenshot = current_state.get('screenshot')
            return 0.0, {}
        
        # ===== POZITÍV REWARD-OK =====
        
        # 1. Barakk / épület megnyitása
        if self._detect_building_opened(current_state):
            reward = self.rewards['barracks_opened']
            total_reward += reward
            breakdown['barracks_opened'] = reward
        
        # 2. Train menü megnyitása
        if self._detect_train_menu_opened(current_state):
            reward = self.rewards['train_menu_opened']
            total_reward += reward
            breakdown['train_menu_opened'] = reward
        
        # 3. Tier választás
        if self._detect_tier_selected(self.prev_state, current_state):
            reward = self.rewards['tier_selected']
            total_reward += reward
            breakdown['tier_selected'] = reward
        
        # 4. Mennyiség beállítás
        if self._detect_quantity_changed(self.prev_state, current_state):
            reward = self.rewards['quantity_set']
            total_reward += reward
            breakdown['quantity_set'] = reward
        
        # 5. Train gomb kattintás
        if self._detect_train_button_clicked(self.prev_state, current_state):
            reward = self.rewards['train_button_clicked']
            total_reward += reward
            breakdown['train_button_clicked'] = reward
        
        # 6. FŐ JUTALOM - Képzés elindult
        if self._detect_training_started(self.prev_state, current_state):
            reward = self.rewards['training_started']
            total_reward += reward
            breakdown['training_started'] = reward
        
        # 7. Power növekedés
        power_increase = self._detect_power_increase(current_state)
        if power_increase > 0:
            reward = self.rewards['power_increased'] * (power_increase / 1000.0)
            total_reward += reward
            breakdown['power_increased'] = reward
        
        # ===== NEGATÍV REWARD-OK =====
        
        # 8. Felesleges kattintás (nincs változás)
        if action and action.get('type') == 'click':
            if not self._detect_state_changed(self.prev_state, current_state):
                reward = self.rewards['wasted_click']
                total_reward += reward
                breakdown['wasted_click'] = reward
        
        # 9. Túl hosszú inaktivitás
        if self._detect_idle_too_long():
            reward = self.rewards['idle_too_long']
            total_reward += reward
            breakdown['idle_too_long'] = reward
        
        # 10. Foglalt queue-ba próbált képezni
        if self._detect_queue_busy_attempt(action, current_state):
            reward = self.rewards['queue_busy_attempt']
            total_reward += reward
            breakdown['queue_busy_attempt'] = reward
        
        # 11. Erőforrás kifogyás
        if self._detect_resource_depleted(current_state):
            reward = self.rewards['resource_depleted']
            total_reward += reward
            breakdown['resource_depleted'] = reward
        
        # Statisztika frissítés
        self.total_rewards += total_reward
        for key, value in breakdown.items():
            self.reward_breakdown[key] += value
        
        # Log
        if DEBUG_MODE and breakdown:
            self._log_reward(total_reward, breakdown)
        
        # Állapot mentés
        self.prev_state = current_state
        self.prev_screenshot = current_state.get('screenshot')
        self.last_action_time = time.time()
        
        return total_reward, breakdown
    
    # ===== DETEKTOROK =====
    
    def _detect_building_opened(self, state: Dict) -> bool:
        """Épület menü megnyitása"""
        # Keresés menü header-re
        coords = self.image_mgr.find_template('ui/train_menu_header.png')
        return coords is not None
    
    def _detect_train_menu_opened(self, state: Dict) -> bool:
        """Train lista megnyitása"""
        # Tier ikonok láthatók?
        tier_count = 0
        for tier in ['t1', 't2', 't3', 't4', 't5']:
            if self.image_mgr.find_template(f'tiers/tier_{tier}.png'):
                tier_count += 1
        
        return tier_count >= 2
    
    def _detect_tier_selected(self, prev_state: Dict, curr_state: Dict) -> bool:
        """Tier kiválasztás detektálás"""
        # Quantity slider megjelent?
        slider = self.image_mgr.find_template('ui/quantity_slider.png')
        train_btn = self.image_mgr.find_template('ui/train_button.png')
        
        return slider is not None or train_btn is not None
    
    def _detect_quantity_changed(self, prev_state: Dict, curr_state: Dict) -> bool:
        """Mennyiség változás (OCR alapú)"""
        # TODO: Implementálni OCR-rel a quantity mező olvasását
        # Egyenlőre egyszerűsített verzió
        return False
    
    def _detect_train_button_clicked(self, prev_state: Dict, curr_state: Dict) -> bool:
        """Train gomb kattintás"""
        # Train gomb eltűnt?
        prev_btn = self.image_mgr.find_template('ui/train_button.png', 
                                               prev_state.get('screenshot'))
        curr_btn = self.image_mgr.find_template('ui/train_button.png',
                                               curr_state.get('screenshot'))
        
        if prev_btn and not curr_btn:
            return True
        
        # Confirm popup megjelent?
        confirm = self.image_mgr.find_template('ui/confirm_button.png')
        return confirm is not None
    
    def _detect_training_started(self, prev_state: Dict, curr_state: Dict) -> bool:
        """
        FŐ JUTALOM - Képzés sikeresen elindult
        """
        # Zzzz ikon megjelent
        zzzz = self.image_mgr.find_template('ui/zzzz_icon.png')
        if zzzz:
            return True
        
        # Training progress bar
        progress = self.image_mgr.find_template('ui/training_progress.png')
        if progress:
            return True
        
        return False
    
    def _detect_power_increase(self, state: Dict) -> int:
        """
        Power növekedés detektálás (OCR)
        
        Returns:
            Növekedés mértéke (int)
        """
        # TODO: Implementálni OCR-rel
        # Egyenlőre dummy
        return 0
    
    def _detect_state_changed(self, prev_state: Dict, curr_state: Dict) -> bool:
        """
        Állapot változás detektálás (képernyő diff)
        """
        prev_screen = prev_state.get('screenshot')
        curr_screen = curr_state.get('screenshot')
        
        if prev_screen is None or curr_screen is None:
            return False
        
        diff = self.image_mgr.compare_screenshots(prev_screen, curr_screen)
        
        # Threshold: ha változás > 1% pixel
        threshold = prev_screen.size * 0.01
        return diff > threshold
    
    def _detect_idle_too_long(self, max_idle: float = 30.0) -> bool:
        """Túl hosszú inaktivitás"""
        idle_time = time.time() - self.last_action_time
        return idle_time > max_idle
    
    def _detect_queue_busy_attempt(self, action: Dict, state: Dict) -> bool:
        """
        Próbált képezni foglalt queue mellett
        """
        if not action or action.get('name') != 'click_train_button':
            return False
        
        # Zzzz ikon látható (queue busy)
        zzzz = self.image_mgr.find_template('ui/zzzz_icon.png')
        return zzzz is not None
    
    def _detect_resource_depleted(self, state: Dict) -> bool:
        """
        Erőforrás kifogyott
        """
        # TODO: Implementálni OCR-rel az erőforrás értékek olvasását
        # Egyenlőre dummy
        return False
    
    def _log_reward(self, total: float, breakdown: Dict):
        """Reward log kiírása"""
        print(f"\n{'='*60}")
        print(f"🎁 REWARD: {total:+.3f}")
        print(f"{'='*60}")
        for key, value in breakdown.items():
            emoji = "✅" if value > 0 else "❌"
            print(f"  {emoji} {key:.<40} {value:+.3f}")
        print(f"{'='*60}\n")
    
    def get_statistics(self) -> Dict:
        """Reward statisztikák"""
        return {
            'total_rewards': self.total_rewards,
            'breakdown': self.reward_breakdown.copy()
        }
    
    def reset(self):
        """Reward manager reset"""
        self.prev_state = None
        self.prev_screenshot = None
        self.last_action_time = time.time()
        self.total_rewards = 0.0
        self.reward_breakdown = {key: 0.0 for key in self.rewards}


if __name__ == "__main__":
    # Teszt
    from core.window_manager import WindowManager
    from core.image_manager import ImageManager
    
    wm = WindowManager()
    wm.find_window("BlueStacks")
    
    im = ImageManager(wm)
    rm = RewardManager(im)
    
    # Dummy state
    state1 = {'screenshot': im.screenshot()}
    state2 = {'screenshot': im.screenshot()}
    
    action = {'type': 'click', 'name': 'test'}
    
    reward, breakdown = rm.calculate_reward(state2, action)
    print(f"Reward: {reward}, Breakdown: {breakdown}")