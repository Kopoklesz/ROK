"""
Training vizualizáció
"""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


class TrainingVisualizer:
    """
    Training grafikonok
    """
    
    def __init__(self):
        self.episodes = []
        self.rewards = []
        self.losses = []
        self.epsilons = []
    
    def add_episode_data(self, episode, reward, loss, epsilon):
        """
        Epizód adatok hozzáadása
        """
        self.episodes.append(episode)
        self.rewards.append(reward)
        self.losses.append(loss)
        self.epsilons.append(epsilon)
    
    def plot(self, save_path=None, show=False):
        """
        Grafikonok létrehozása
        """
        if not self.episodes:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('ROK RL Agent - Training Progress', fontsize=16)
        
        # 1. Episode Rewards
        ax1 = axes[0, 0]
        ax1.plot(self.episodes, self.rewards, alpha=0.6, label='Episode Reward')
        ax1.plot(self.episodes, self._moving_average(self.rewards, window=10), 
                linewidth=2, label='Moving Avg (10)')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Reward')
        ax1.set_title('Episode Rewards')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Loss
        ax2 = axes[0, 1]
        if self.losses:
            ax2.plot(self.episodes, self.losses, alpha=0.6, color='orange', label='Loss')
            ax2.plot(self.episodes, self._moving_average(self.losses, window=10),
                    linewidth=2, color='red', label='Moving Avg (10)')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Loss')
        ax2.set_title('Training Loss')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Epsilon Decay
        ax3 = axes[1, 0]
        ax3.plot(self.episodes, self.epsilons, color='green', linewidth=2)
        ax3.set_xlabel('Episode')
        ax3.set_ylabel('Epsilon')
        ax3.set_title('Exploration Rate (Epsilon)')
        ax3.grid(True, alpha=0.3)
        
        # 4. Cumulative Reward
        ax4 = axes[1, 1]
        cumulative_reward = np.cumsum(self.rewards)
        ax4.plot(self.episodes, cumulative_reward, color='purple', linewidth=2)
        ax4.set_xlabel('Episode')
        ax4.set_ylabel('Cumulative Reward')
        ax4.set_title('Cumulative Reward Over Time')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Mentés
        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"📊 Grafikon mentve: {save_path}")
        
        # Megjelenítés
        if show:
            plt.show()
        else:
            plt.close()
    
    @staticmethod
    def _moving_average(data, window=10):
        """Mozgó átlag számítás"""
        if len(data) < window:
            return data
        
        cumsum = np.cumsum(np.insert(data, 0, 0))
        return (cumsum[window:] - cumsum[:-window]) / window