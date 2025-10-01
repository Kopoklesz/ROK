"""
Logging utility
"""
import json
from datetime import datetime
from pathlib import Path
from config.settings import LOGS_DIR


class TrainingLogger:
    """
    Training adatok logolása
    """
    
    def __init__(self):
        self.episodes_data = []
        self.log_file = LOGS_DIR / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"📝 Logger inicializálva: {self.log_file}")
    
    def log_episode(self, episode, steps, reward, epsilon, loss, duration, info=None):
        """
        Epizód adatok logolása
        """
        data = {
            'episode': episode,
            'steps': steps,
            'reward': reward,
            'epsilon': epsilon,
            'loss': loss,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        if info:
            data['info'] = info
        
        self.episodes_data.append(data)
        
        # Folyamatos mentés
        self._save_to_file()
    
    def _save_to_file(self):
        """JSON file mentés"""
        with open(self.log_file, 'w') as f:
            json.dump(self.episodes_data, f, indent=2)
    
    def print_summary(self):
        """Training összefoglaló"""
        if not self.episodes_data:
            return
        
        total_episodes = len(self.episodes_data)
        total_steps = sum(ep['steps'] for ep in self.episodes_data)
        avg_reward = sum(ep['reward'] for ep in self.episodes_data) / total_episodes
        max_reward = max(ep['reward'] for ep in self.episodes_data)
        min_reward = min(ep['reward'] for ep in self.episodes_data)
        
        print("\n" + "="*60)
        print("📊 TRAINING ÖSSZEFOGLALÓ")
        print("="*60)
        print(f"Összes epizód:    {total_episodes}")
        print(f"Összes lépés:     {total_steps}")
        print(f"Átlag reward:     {avg_reward:+.2f}")
        print(f"Max reward:       {max_reward:+.2f}")
        print(f"Min reward:       {min_reward:+.2f}")
        print(f"Log fájl:         {self.log_file}")
        print("="*60 + "\n")


class ConsoleLogger:
    """
    Színes console log
    """
    
    @staticmethod
    def info(msg):
        print(f"ℹ️  {msg}")
    
    @staticmethod
    def success(msg):
        print(f"✅ {msg}")
    
    @staticmethod
    def warning(msg):
        print(f"⚠️  {msg}")
    
    @staticmethod
    def error(msg):
        print(f"❌ {msg}")
    
    @staticmethod
    def debug(msg):
        print(f"🐛 {msg}")