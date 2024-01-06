#region imports
from AlgorithmImports import *
#endregion
import torch
import torch.nn as nn
import numpy as np
import torch.optim as optim

### Library classes are snippets of code/classes you can reuse between projects. They are
### added to projects on compile.
###
### To import this class use the following import with your values subbed in for the {} sections:
### from {libraryProjectName} import {libraryFileName}
### 
### Example using your newly imported library from 'Library.py' like so:
###
### from {libraryProjectName} import Library
### x = Library.Add(1,1)
### print(x)
###

class MLPClassifierPyTorch(nn.Module):
    def __init__(self, input_size, num_classes=3, weights=None, biases=None):
        super(MLPClassifierPyTorch, self).__init__()
        self.fc1 = nn.Linear(input_size, 150)
        self.fc2 = nn.Linear(150, 150)
        self.fc3 = nn.Linear(150, 50)
        self.fc4 = nn.Linear(50, 10)
        self.fc5 = nn.Linear(10, 50)
        self.fc6 = nn.Linear(50, 150)
        self.fc7 = nn.Linear(150, num_classes) 
        if weights is not None and biases is not None:
            self.init_weights(weights, biases)

    def init_weights(self, weights, biases):
        layers = [self.fc1, self.fc2, self.fc3, self.fc4, self.fc5, self.fc6, self.fc7]

        for i, layer in enumerate(layers):
            layer.weight.data = torch.from_numpy(weights[i].T).float()
            layer.bias.data = torch.from_numpy(biases[i]).float()

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        x = torch.relu(self.fc4(x))
        x = torch.relu(self.fc5(x))
        x = torch.relu(self.fc6(x))
        x = self.fc7(x)  # No activation here, CrossEntropyLoss will apply softmax
        return x


def loadclf2(self):
    file_name2 = self.ObjectStore.GetFilePath("3_0_5_pytorch_clf.pt")
    clf2= torch.load(file_name2)
    return clf2
