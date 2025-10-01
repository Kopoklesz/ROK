"""
DQN Agent - Deep Q-Learning Agent
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from pathlib import Path

from agent.network import DQN, DuelingDQN
from agent.replay_buffer import ReplayBuffer

from config.settings import (
    STATE_SHAPE,
    ACTION_SPACE_SIZE,
    LEARNING_RATE,
    GAMMA,
    BATCH_SIZE,
    MEMORY_SIZE,
    EPSILON_START,
    EPSILON_END,
    EPSILON_DECAY,
    MODELS_DIR
)


class DQNAgent:
    """
    Deep Q-Network Agent
    """
    
    def __init__(self, use_dueling=False):
        """
        Args:
            use_dueling: Dueling DQN használata (advanced)
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🖥️ Device: {self.device}")
        
        # Hyperparameters
        self.gamma = GAMMA
        self.batch_size = BATCH_SIZE
        self.epsilon = EPSILON_START
        self.epsilon_min = EPSILON_END
        self.epsilon_decay = EPSILON_DECAY
        
        # Networks
        if use_dueling:
            self.policy_net = DuelingDQN(
                input_shape=(STATE_SHAPE[2], STATE_SHAPE[0], STATE_SHAPE[1]),
                n_actions=ACTION_SPACE_SIZE
            ).to(self.device)
            self.target_net = DuelingDQN(
                input_shape=(STATE_SHAPE[2], STATE_SHAPE[0], STATE_SHAPE[1]),
                n_actions=ACTION_SPACE_SIZE
            ).to(self.device)
        else:
            self.policy_net = DQN(
                input_shape=(STATE_SHAPE[2], STATE_SHAPE[0], STATE_SHAPE[1]),
                n_actions=ACTION_SPACE_SIZE
            ).to(self.device)
            self.target_net = DQN(
                input_shape=(STATE_SHAPE[2], STATE_SHAPE[0], STATE_SHAPE[1]),
                n_actions=ACTION_SPACE_SIZE
            ).to(self.device)
        
        # Target network szinkronizálás
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=LEARNING_RATE)
        
        # Replay buffer
        self.memory = ReplayBuffer(capacity=MEMORY_SIZE)
        
        # Statisztikák
        self.training_steps = 0
        self.episodes_trained = 0
    
    def select_action(self, state, training=True):
        """
        Epsilon-greedy action selection
        
        Args:
            state: Állapot (numpy array)
            training: Training mode (exploration engedélyezve)
            
        Returns:
            action (int)
        """
        # Exploration
        if training and np.random.rand() < self.epsilon:
            return np.random.randint(0, ACTION_SPACE_SIZE)
        
        # Exploitation
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            # (height, width, channels) → (channels, height, width)
            state_tensor = state_tensor.permute(0, 3, 1, 2)
            
            q_values = self.policy_net(state_tensor)
            action = q_values.argmax(dim=1).item()
        
        return action
    
    def store_transition(self, state, action, reward, next_state, done):
        """
        Tapasztalat tárolása
        """
        self.memory.push(state, action, reward, next_state, done)
    
    def train_step(self):
        """
        Egy training iteráció
        
        Returns:
            loss érték vagy None
        """
        if len(self.memory) < self.batch_size:
            return None
        
        # Batch sampling
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        # Device-ra
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        
        # Reshape: (batch, height, width, channels) → (batch, channels, height, width)
        states = states.permute(0, 3, 1, 2)
        next_states = next_states.permute(0, 3, 1, 2)
        
        # Current Q values
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze()
        
        # Target Q values
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Loss
        loss = nn.MSELoss()(current_q_values, target_q_values)
        
        # Backpropagation
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping (stabilitás)
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=10)
        
        self.optimizer.step()
        
        # Epsilon decay
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        self.training_steps += 1
        
        return loss.item()
    
    def update_target_network(self):
        """
        Target network frissítése
        """
        self.target_net.load_state_dict(self.policy_net.state_dict())
        print("🔄 Target network frissítve")
    
    def save(self, filepath=None):
        """
        Model mentése
        """
        if filepath is None:
            filepath = MODELS_DIR / f"dqn_agent_ep{self.episodes_trained}.pth"
        
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_steps': self.training_steps,
            'episodes_trained': self.episodes_trained
        }, filepath)
        
        print(f"💾 Model mentve: {filepath}")
    
    def load(self, filepath):
        """
        Model betöltése
        """
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_min)
        self.training_steps = checkpoint.get('training_steps', 0)
        self.episodes_trained = checkpoint.get('episodes_trained', 0)
        
        print(f"✅ Model betöltve: {filepath}")
        print(f"   Epsilon: {self.epsilon:.3f}, Steps: {self.training_steps}, Episodes: {self.episodes_trained}")
    
    def set_training_mode(self, mode=True):
        """
        Training/Evaluation mode váltás
        """
        if mode:
            self.policy_net.train()
        else:
            self.policy_net.eval()


if __name__ == "__main__":
    # Teszt
    print("🤖 DQN Agent teszt\n")
    
    agent = DQNAgent(use_dueling=False)
    
    # Dummy state
    dummy_state = np.random.rand(84, 84, 3)
    
    # Action selection
    action = agent.select_action(dummy_state, training=True)
    print(f"Selected action: {action}")
    
    # Store transition
    next_state = np.random.rand(84, 84, 3)
    agent.store_transition(dummy_state, action, 0.5, next_state, False)
    
    print(f"Memory size: {len(agent.memory)}")
    
    # Training (ha van elég tapasztalat)
    for _ in range(100):
        agent.store_transition(dummy_state, action, np.random.rand(), next_state, False)
    
    loss = agent.train_step()
    print(f"Training loss: {loss:.4f}")