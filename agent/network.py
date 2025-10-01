"""
Neural Network Architecture - Deep Q-Network
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class DQN(nn.Module):
    """
    Deep Q-Network - Convolutional Neural Network
    
    Input: (batch, 3, 84, 84) képernyő screenshot
    Output: (batch, action_space_size) Q-values
    """
    
    def __init__(self, input_shape=(3, 84, 84), n_actions=20):
        super(DQN, self).__init__()
        
        self.input_shape = input_shape
        self.n_actions = n_actions
        
        # Convolutional layers
        self.conv1 = nn.Conv2d(input_shape[0], 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)
        
        # Fully connected layers méretének kiszámítása
        conv_out_size = self._get_conv_output_size(input_shape)
        
        self.fc1 = nn.Linear(conv_out_size, 512)
        self.fc2 = nn.Linear(512, n_actions)
    
    def forward(self, x):
        """
        Forward pass
        
        Args:
            x: (batch, channels, height, width)
        
        Returns:
            Q-values (batch, n_actions)
        """
        # Convolutional layers
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        
        # Flatten
        x = x.view(x.size(0), -1)
        
        # Fully connected
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        
        return x
    
    def _get_conv_output_size(self, shape):
        """
        Conv layers output méretének kiszámítása
        """
        dummy_input = torch.zeros(1, *shape)
        x = F.relu(self.conv1(dummy_input))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        return int(np.prod(x.size()))


class DuelingDQN(nn.Module):
    """
    Dueling DQN Architecture - Advanced version
    
    Külön értékeli:
    - State value V(s)
    - Action advantages A(s, a)
    
    Q(s, a) = V(s) + (A(s, a) - mean(A(s, a)))
    """
    
    def __init__(self, input_shape=(3, 84, 84), n_actions=20):
        super(DuelingDQN, self).__init__()
        
        self.input_shape = input_shape
        self.n_actions = n_actions
        
        # Convolutional feature extractor
        self.conv1 = nn.Conv2d(input_shape[0], 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)
        
        conv_out_size = self._get_conv_output_size(input_shape)
        
        # Value stream
        self.value_fc1 = nn.Linear(conv_out_size, 512)
        self.value_fc2 = nn.Linear(512, 1)
        
        # Advantage stream
        self.advantage_fc1 = nn.Linear(conv_out_size, 512)
        self.advantage_fc2 = nn.Linear(512, n_actions)
    
    def forward(self, x):
        """
        Forward pass
        """
        # Feature extraction
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = x.view(x.size(0), -1)
        
        # Value stream
        value = F.relu(self.value_fc1(x))
        value = self.value_fc2(value)
        
        # Advantage stream
        advantage = F.relu(self.advantage_fc1(x))
        advantage = self.advantage_fc2(advantage)
        
        # Combine: Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        
        return q_values
    
    def _get_conv_output_size(self, shape):
        dummy_input = torch.zeros(1, *shape)
        x = F.relu(self.conv1(dummy_input))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        return int(np.prod(x.size()))


import numpy as np

if __name__ == "__main__":
    # Teszt
    print("🧠 Neural Network teszt\n")
    
    # Standard DQN
    model = DQN(input_shape=(3, 84, 84), n_actions=20)
    print(f"Standard DQN paraméterek: {sum(p.numel() for p in model.parameters()):,}")
    
    # Dummy input
    dummy_input = torch.randn(4, 3, 84, 84)  # batch=4
    output = model(dummy_input)
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Q-values sample: {output[0][:5]}\n")
    
    # Dueling DQN
    dueling_model = DuelingDQN(input_shape=(3, 84, 84), n_actions=20)
    print(f"Dueling DQN paraméterek: {sum(p.numel() for p in dueling_model.parameters()):,}")
    
    output_dueling = dueling_model(dummy_input)
    print(f"Dueling output shape: {output_dueling.shape}")
    print(f"Dueling Q-values sample: {output_dueling[0][:5]}")