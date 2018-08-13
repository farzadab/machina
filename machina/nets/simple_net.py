import torch
import torch.nn as nn
from torch.nn.init import kaiming_uniform_, uniform_
import torch.nn.functional as F

def mini_weight_init(m):
    if m.__class__.__name__ == 'Linear':
        m.weight.data.copy_(uniform_(m.weight.data, -3e-3, 3e-3))
        m.bias.data.fill_(0)

def weight_init(m):
    if m.__class__.__name__ == 'Linear':
        m.weight.data.copy_(kaiming_uniform_(m.weight.data))
        m.bias.data.fill_(0)

class PolNet(nn.Module):
    def __init__(self, ob_space, ac_space, h1=200, h2=100):
        nn.Module.__init__(self)
        self.fc1 = nn.Linear(ob_space.shape[0], h1)
        self.fc2 = nn.Linear(h1, h2)
        self.mean_layer = nn.Linear(h2, ac_space.shape[0])
        self.log_std_param = nn.Parameter(torch.randn(ac_space.shape[0])*1e-10 - 1)

        self.fc1.apply(weight_init)
        self.fc2.apply(weight_init)
        self.mean_layer.apply(mini_weight_init)

    def forward(self, ob):
        h = F.relu(self.fc1(ob))
        h = F.relu(self.fc2(h))
        mean = F.tanh(self.mean_layer(h))
        return mean, self.log_std_param

class MixturePolNet(nn.Module):
    def __init__(self, ob_space, ac_space, mixture, h1=200, h2=100):
        nn.Module.__init__(self)
        self.fc1 = nn.Linear(ob_space.shape[0], h1)
        self.fc2 = nn.Linear(h1, h2)
        self.mean_layer = nn.Linear(h2, ac_space.shape[0]*mixture + mixture)
        self.log_std_param = nn.Parameter(torch.randn(mixture, ac_space.shape[0])*1e-10 - 1)

        self.fc1.apply(weight_init)
        self.fc2.apply(weight_init)
        self.mean_layer.apply(mini_weight_init)
        self.ac_space = ac_space
        self.mixture = mixture

    def forward(self, ob):
        h = F.relu(self.fc1(ob))
        h = F.relu(self.fc2(h))
        out = F.tanh(self.mean_layer(h))
        out = out.contiguous()
        mean = out[:, :self.ac_space.shape[0]*self.mixture]
        mean = mean.contiguous()
        mean = mean.view(-1, self.mixture, self.ac_space.shape[0])
        pi = out[:, self.ac_space.shape[0]*self.mixture:]
        pi = F.softmax(pi, dim=1)
        return pi, mean, self.log_std_param


class DeterministicPolNet(nn.Module):
    def __init__(self, ob_space, ac_space, h1=200, h2=100):
        nn.Module.__init__(self)
        self.fc1 = nn.Linear(ob_space.shape[0], h1)
        self.fc2 = nn.Linear(h1,h2)
        self.mean_layer = nn.Linear(h2, ac_space.shape[0])

        self.fc1.apply(weight_init)
        self.fc2.apply(weight_init)
        self.mean_layer.apply(mini_weight_init)

    def forward(self, ob):
        h = F.relu(self.fc1(ob))
        h = F.relu(self.fc2(h))
        mean = F.tanh(self.mean_layer(h))
        return mean



class VNet(nn.Module):
    def __init__(self, ob_space, h1=200, h2=100):
        nn.Module.__init__(self)
        self.fc1 = nn.Linear(ob_space.shape[0], h1)
        self.fc2 = nn.Linear(h1, h2)
        self.output_layer = nn.Linear(h2, 1)
        self.apply(weight_init)

    def forward(self, ob):
        h = F.relu(self.fc1(ob))
        h = F.relu(self.fc2(h))
        return self.output_layer(h)

class QNet(nn.Module):
    def __init__(self, ob_space, ac_space, h1=300, h2=400):
        nn.Module.__init__(self)
        self.fc1 = nn.Linear(ob_space.shape[0], h1)
        self.fc2 = nn.Linear(ac_space.shape[0] + h1, h2)
        self.output_layer = nn.Linear(h2, 1)
        self.fc1.apply(weight_init)
        self.fc2.apply(weight_init)
        self.output_layer.apply(mini_weight_init)

    def forward(self, ob, ac):
        h = F.relu(self.fc1(ob))
        h = torch.cat([h, ac], dim=1)
        h = F.relu(self.fc2(h))
        return self.output_layer(h)