"""
ROK Environment - RL környezet a játékhoz
"""
import time
import numpy as np
import cv2
from typing import Dict, Tuple, Optional

from core.window_manager import WindowManager
from core.image_manager import ImageManager
from core.action_executor import ActionExecutor
from environment.reward_manager import RewardManager

from config.settings import (
    GAME_WINDOW_TITLE,
    STATE_SHAPE,
    ACTION_SPACE_SIZE,
    MAX_STEPS_PER_EPISODE,
    ACTIONS,
    DEBUG_MODE
)


class ROKEnvironment:
    """
    Rise of Kingdoms RL Environment
    
    Gymnasium-kompatibilis interfész
    """
    
    def __init__(self):
        print("🎮 ROK Environment inicializálása...")
        
        # Core komponensek
        self.window_mgr = WindowManager(GAME_WINDOW_TITLE)
        self.image_mgr = ImageManager(self.window_mgr)
        self.action_exec = ActionExecutor(self.window_mgr, self.image_mgr)
        self.reward_mgr = RewardManager(self.image_mgr)
        
        # Állapot tracking
        self.current_step = 0
        self.episode_reward = 0.0
        self.episode_count = 0
        
        # Action space
        self.action_space_size = ACTION_SPACE_SIZE
        self.actions_dict = ACTIONS
        
        # Játék ablak inicializálás
        if not self._initialize_game_window():
            raise RuntimeError("❌ Nem található a játék ablak!")
        
        print("✅ Environment inicializálva")
    
    def reset(self) -> np.ndarray:
        """
        Environment újraindítása
        
        Returns:
            Initial state (preprocessed screenshot)
        """
        print(f"\n🔄 Episode #{self.episode_count + 1} reset")
        
        # Ablak fókusz
        self.window_mgr.focus_window()
        time.sleep(0.5)
        
        # Emergency escape (biztos ami biztos)
        self.action_exec.emergency_escape()
        time.sleep(0.5)
        
        # Reset tracking változók
        self.current_step = 0
        self.episode_reward = 0.0
        self.reward_mgr.reset()
        
        # Kezdő állapot
        state = self.get_state()
        
        self.episode_count += 1
        
        return state['processed_screenshot']
    
    def step(self, action_id: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Egy lépés végrehajtása
        
        Args:
            action_id: Akció azonosító (0 - ACTION_SPACE_SIZE)
            
        Returns:
            (next_state, reward, done, info)
        """
        self.current_step += 1
        
        # Akció végrehajtása
        action_success = self._execute_action(action_id)
        
        # Várakozás UI frissülésre
        time.sleep(0.5)
        
        # Új állapot
        next_state = self.get_state()
        
        # Reward számítás
        action_dict = self.actions_dict.get(action_id, {})
        reward, reward_breakdown = self.reward_mgr.calculate_reward(
            next_state, 
            action_dict
        )
        
        self.episode_reward += reward
        
        # Terminálás feltételek
        done = self._check_done()
        
        # Info dict
        info = {
            'step': self.current_step,
            'episode_reward': self.episode_reward,
            'reward_breakdown': reward_breakdown,
            'action_success': action_success,
            'action_name': action_dict.get('name', 'unknown')
        }
        
        if DEBUG_MODE:
            self._log_step(action_id, reward, info)
        
        return next_state['processed_screenshot'], reward, done, info
    
    def get_state(self) -> Dict:
        """
        Teljes állapot lekérdezése
        
        Returns:
            Dict with raw and processed state
        """
        # Screenshot
        raw_screenshot = self.image_mgr.screenshot()
        
        # Preprocessing (resize + normalize)
        processed = self._preprocess_screenshot(raw_screenshot)
        
        # OCR adatok (opcionális, ha az agent használni akarja)
        ocr_data = self._extract_ocr_data(raw_screenshot)
        
        return {
            'screenshot': raw_screenshot,
            'processed_screenshot': processed,
            'ocr_data': ocr_data,
            'timestamp': time.time()
        }
    
    def _execute_action(self, action_id: int) -> bool:
        """
        Akció végrehajtása ID alapján
        
        Returns:
            bool: Sikeres volt-e
        """
        if action_id not in self.actions_dict:
            print(f"⚠️ Érvénytelen akció ID: {action_id}")
            return False
        
        action = self.actions_dict[action_id]
        action_type = action.get('name', '')
        
        if DEBUG_MODE:
            print(f"🎬 Akció #{action_id}: {action_type}")
        
        # Wait akció
        if action_type == 'wait':
            duration = action.get('duration', 1.0)
            self.action_exec.wait(duration)
            return True
        
        # Navigate akció
        if action_type.startswith('navigate_'):
            target = action.get('target')
            return self.action_exec.navigate_to_building(target)
        
        # Template-based click
        if 'template' in action:
            template = action['template']
            return self.action_exec.click_template(template)
        
        # Quantity set
        if action_type.startswith('set_quantity_'):
            quantity = action.get('value', 1)
            return self.action_exec.set_training_quantity(quantity)
        
        # Key press
        if 'key' in action:
            key = action['key']
            return self.action_exec.press_key(key)
        
        # Fix koordináta kattintás
        if 'coords' in action:
            coords = action['coords']
            return self.action_exec.click(coords)
        
        print(f"⚠️ Nem implementált akció típus: {action_type}")
        return False
    
    def _preprocess_screenshot(self, screenshot: np.ndarray) -> np.ndarray:
        """
        Screenshot előfeldolgozás neurális hálóhoz
        
        Returns:
            (84, 84, 3) normalized array
        """
        if screenshot is None:
            return np.zeros(STATE_SHAPE, dtype=np.float32)
        
        # Resize
        resized = cv2.resize(screenshot, (STATE_SHAPE[1], STATE_SHAPE[0]))
        
        # Normalize (0-1)
        normalized = resized.astype(np.float32) / 255.0
        
        return normalized
    
    def _extract_ocr_data(self, screenshot: np.ndarray) -> Dict:
        """
        OCR adatok kiolvasása (opcionális)
        
        Returns:
            Dict with extracted data
        """
        # TODO: Implementálni valódi OCR-t
        # Egyenlőre placeholder
        return {
            'power': 0,
            'food': 0,
            'wood': 0,
            'gold': 0,
            'stone': 0,
            'queue_count': 0
        }
    
    def _check_done(self) -> bool:
        """
        Epizód vége feltételek
        """
        # Max lépésszám
        if self.current_step >= MAX_STEPS_PER_EPISODE:
            print(f"⏱️ Max lépésszám elérve ({MAX_STEPS_PER_EPISODE})")
            return True
        
        # Negatív reward threshold (túl rossz döntések)
        if self.episode_reward < -10.0:
            print(f"❌ Túl negatív reward: {self.episode_reward:.2f}")
            return True
        
        return False
    
    def _initialize_game_window(self) -> bool:
        """Játék ablak inicializálás"""
        print("🔍 Játék ablak keresése...")
        
        if self.window_mgr.find_window():
            self.window_mgr.focus_window()
            time.sleep(0.5)
            return True
        
        return False
    
    def _log_step(self, action_id: int, reward: float, info: Dict):
        """Lépés logolása"""
        action_name = info.get('action_name', 'unknown')
        print(f"Step {self.current_step}: Action={action_name} (#{action_id}), "
              f"Reward={reward:+.3f}, Total={self.episode_reward:.3f}")
    
    def render(self):
        """
        Vizuális megjelenítés (opcionális)
        """
        # Megjelenítés matplotlib-tal vagy OpenCV ablakban
        screenshot = self.image_mgr.screenshot()
        if screenshot is not None:
            cv2.imshow("ROK Environment", screenshot)
            cv2.waitKey(1)
    
    def close(self):
        """Environment lezárása"""
        cv2.destroyAllWindows()
        print("👋 Environment bezárva")
    
    def get_episode_statistics(self) -> Dict:
        """Epizód statisztikák"""
        return {
            'episode': self.episode_count,
            'steps': self.current_step,
            'total_reward': self.episode_reward,
            'reward_breakdown': self.reward_mgr.get_statistics()
        }


if __name__ == "__main__":
    # Teszt
    env = ROKEnvironment()
    
    print("\n🧪 Environment teszt - Random akciók")
    state = env.reset()
    
    for i in range(10):
        # Random akció
        action = np.random.randint(0, env.action_space_size)
        next_state, reward, done, info = env.step(action)
        
        print(f"Step {i+1}: Reward={reward:.3f}, Done={done}")
        
        if done:
            break
    
    stats = env.get_episode_statistics()
    print(f"\n📊 Epizód vége: {stats}")
    
    env.close()