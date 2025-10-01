"""
Experience Replay Buffer
"""
import random
import numpy as np
from collections import deque
import torch


class ReplayBuffer:
    """
    Experience Replay Buffer - múltbeli tapasztalatok tárolása
    """
    
    def __init__(self, capacity=10000):
        """
        Args:
            capacity: Maximum tárolható tapasztalatok száma
        """
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
    
    def push(self, state, action, reward, next_state, done):
        """
        Új tapasztalat hozzáadása
        
        Args:
            state: Állapot (numpy array)
            action: Akció (int)
            reward: Jutalom (float)
            next_state: Következő állapot (numpy array)
            done: Terminált-e (bool)
        """
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        """
        Random batch mintavételezés
        
        Args:
            batch_size: Batch méret
            
        Returns:
            (states, actions, rewards, next_states, dones) tuple of tensors
        """
        batch = random.sample(self.buffer, batch_size)
        
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Numpy arrays → Torch tensors
        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        """Buffer aktuális mérete"""
        return len(self.buffer)
    
    def clear(self):
        """Buffer törlése"""
        self.buffer.clear()
    
    def save(self, filepath):
        """Buffer mentése fájlba"""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump(list(self.buffer), f)
        print(f"✅ Replay buffer mentve: {filepath}")
    
    def load(self, filepath):
        """Buffer betöltése fájlból"""
        import pickle
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.buffer = deque(data, maxlen=self.capacity)
        print(f"✅ Replay buffer betöltve: {filepath} ({len(self)} tapasztalat)")


class PrioritizedReplayBuffer:
    """
    Prioritized Experience Replay - fontosabb tapasztalatok gyakrabban
    
    Advanced feature - később implementálható
    """
    
    def __init__(self, capacity=10000, alpha=0.6):
        """
        Args:
            capacity: Max méret
            alpha: Prioritás exponens (0=uniform, 1=full priority)
        """
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.position = 0
    
    def push(self, state, action, reward, next_state, done):
        """
        Új tapasztalat max prioritással
        """
        max_priority = self.priorities.max() if self.buffer else 1.0
        
        if len(self.buffer) < self.capacity:
            self.buffer.append((state, action, reward, next_state, done))
        else:
            self.buffer[self.position] = (state, action, reward, next_state, done)
        
        self.priorities[self.position] = max_priority
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size, beta=0.4):
        """
        Prioritás alapú mintavételezés
        
        Args:
            batch_size: Batch méret
            beta: Importance sampling exponens
            
        Returns:
            (batch, indices, weights) tuple
        """
        if len(self.buffer) == self.capacity:
            priorities = self.priorities
        else:
            priorities = self.priorities[:self.position]
        
        # Prioritás alapú valószínűségek
        probs = priorities ** self.alpha
        probs /= probs.sum()
        
        # Mintavételezés
        indices = np.random.choice(len(self.buffer), batch_size, p=probs)
        
        # Importance sampling weights
        weights = (len(self.buffer) * probs[indices]) ** (-beta)
        weights /= weights.max()
        
        # Batch készítés
        batch = [self.buffer[idx] for idx in indices]
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)
        weights = torch.FloatTensor(weights)
        
        return (states, actions, rewards, next_states, dones), indices, weights
    
    def update_priorities(self, indices, priorities):
        """
        Prioritások frissítése (TD-error alapján)
        """
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority
    
    def __len__(self):
        return len(self.buffer)


if __name__ == "__main__":
    # Teszt
    print("💾 Replay Buffer teszt\n")
    
    buffer = ReplayBuffer(capacity=100)
    
    # Dummy tapasztalatok
    for i in range(50):
        state = np.random.rand(3, 84, 84)
        action = random.randint(0, 19)
        reward = random.uniform(-1, 1)
        next_state = np.random.rand(3, 84, 84)
        done = random.choice([True, False])
        
        buffer.push(state, action, reward, next_state, done)
    
    print(f"Buffer méret: {len(buffer)}")
    
    # Batch sampling
    batch = buffer.sample(batch_size=8)
    states, actions, rewards, next_states, dones = batch
    
    print(f"Batch shapes:")
    print(f"  States: {states.shape}")
    print(f"  Actions: {actions.shape}")
    print(f"  Rewards: {rewards.shape}")
    print(f"  Next states: {next_states.shape}")
    print(f"  Dones: {dones.shape}")