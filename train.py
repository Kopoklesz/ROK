"""
Training Script - Agent tréningje
"""
import time
from pathlib import Path
from datetime import datetime

from environment.rok_env import ROKEnvironment
from agent.dqn_agent import DQNAgent
from utils.logger import TrainingLogger
from utils.visualizer import TrainingVisualizer

from config.settings import (
    NUM_EPISODES,
    TARGET_UPDATE_FREQUENCY,
    SAVE_FREQUENCY,
    MODELS_DIR
)


class Trainer:
    """
    Training Manager
    """
    
    def __init__(self, use_dueling=False, resume_from=None):
        """
        Args:
            use_dueling: Dueling DQN használata
            resume_from: Model fájl path (folytatás)
        """
        print("="*60)
        print("🎮 ROK RL AGENT - TRAINING")
        print("="*60)
        
        # Environment
        self.env = ROKEnvironment()
        
        # Agent
        self.agent = DQNAgent(use_dueling=use_dueling)
        
        # Resume
        if resume_from:
            self.agent.load(resume_from)
        
        # Logger & Visualizer
        self.logger = TrainingLogger()
        self.visualizer = TrainingVisualizer()
        
        print(f"\n✅ Trainer inicializálva")
        print(f"   Episodes: {NUM_EPISODES}")
        print(f"   Epsilon: {self.agent.epsilon:.3f}")
        print(f"   Memory size: {len(self.agent.memory)}")
    
    def train(self, num_episodes=None):
        """
        Főprogram - Training loop
        """
        if num_episodes is None:
            num_episodes = NUM_EPISODES
        
        print(f"\n🚀 Training kezdés: {num_episodes} epizód\n")
        
        start_episode = self.agent.episodes_trained
        
        for episode in range(start_episode, start_episode + num_episodes):
            episode_start_time = time.time()
            
            # Reset environment
            state = self.env.reset()
            episode_reward = 0.0
            episode_loss = []
            
            done = False
            step = 0
            
            while not done:
                # Action selection
                action = self.agent.select_action(state, training=True)
                
                # Environment step
                next_state, reward, done, info = self.env.step(action)
                
                # Store transition
                self.agent.store_transition(state, action, reward, next_state, done)
                
                # Train
                loss = self.agent.train_step()
                if loss is not None:
                    episode_loss.append(loss)
                
                # Update state
                state = next_state
                episode_reward += reward
                step += 1
            
            # Episode vége
            episode_duration = time.time() - episode_start_time
            avg_loss = sum(episode_loss) / len(episode_loss) if episode_loss else 0.0
            
            # Statistics
            stats = self.env.get_episode_statistics()
            
            # Log
            self.logger.log_episode(
                episode=episode + 1,
                steps=step,
                reward=episode_reward,
                epsilon=self.agent.epsilon,
                loss=avg_loss,
                duration=episode_duration,
                info=stats
            )
            
            # Visualizer
            self.visualizer.add_episode_data(
                episode + 1,
                episode_reward,
                avg_loss,
                self.agent.epsilon
            )
            
            # Target network update
            if (episode + 1) % TARGET_UPDATE_FREQUENCY == 0:
                self.agent.update_target_network()
            
            # Model mentés
            if (episode + 1) % SAVE_FREQUENCY == 0:
                self.agent.episodes_trained = episode + 1
                self.agent.save()
                self.visualizer.plot(save_path=MODELS_DIR / f"training_plot_ep{episode+1}.png")
            
            # Progress
            self._print_progress(episode + 1, start_episode + num_episodes, stats)
        
        # Training vége
        print("\n" + "="*60)
        print("✅ TRAINING BEFEJEZVE")
        print("="*60)
        
        # Végső mentés
        self.agent.episodes_trained = start_episode + num_episodes
        self.agent.save(MODELS_DIR / "dqn_agent_final.pth")
        
        # Végső plot
        self.visualizer.plot(save_path=MODELS_DIR / "training_plot_final.png")
        
        # Statistics summary
        self.logger.print_summary()
        
        # Environment bezárás
        self.env.close()
    
    def _print_progress(self, current_episode, total_episodes, stats):
        """
        Progress bar kiírása
        """
        progress = current_episode / total_episodes * 100
        reward = stats.get('total_reward', 0)
        steps = stats.get('steps', 0)
        
        print(f"Episode {current_episode}/{total_episodes} ({progress:.1f}%) | "
              f"Steps: {steps:3d} | Reward: {reward:+7.2f} | "
              f"ε: {self.agent.epsilon:.3f}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ROK RL Agent Training')
    parser.add_argument('--episodes', type=int, default=NUM_EPISODES,
                       help=f'Epizódok száma (default: {NUM_EPISODES})')
    parser.add_argument('--dueling', action='store_true',
                       help='Dueling DQN használata')
    parser.add_argument('--resume', type=str, default=None,
                       help='Model fájl path (folytatás)')
    
    args = parser.parse_args()
    
    # Training
    trainer = Trainer(use_dueling=args.dueling, resume_from=args.resume)
    trainer.train(num_episodes=args.episodes)


if __name__ == "__main__":
    main()