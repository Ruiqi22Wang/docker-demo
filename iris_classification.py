import numpy as np
import copy
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn.metrics import accuracy_score, precision_score, recall_score
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils import data
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader


iris = load_iris() #load data from sklearn
X,y = iris.data, iris.target
train_X, val_X, train_y, val_y = train_test_split(X, y, test_size=0.20) #no train-test-val since dataset is too small
transformer = preprocessing.Normalizer().fit(train_X)
train_X = transformer.transform(train_X) # normalize the input 
val_X = transformer.transform(val_X)


class ToTensor(object):

    '''Convert ndarrays in sample to Tensors.'''

    def __call__(self, sample):
        data, target = sample['data'], sample['target']
        return {'data': torch.from_numpy(data),
                'target': torch.from_numpy(target)}


class iris_dataset(Dataset):

    '''Get the equivelant of torch.utils.data.Dataset
       This is not necessary for iris dataset, but will be helpful for big data and complicate preprocessing'''

    def __init__(self, source_data, source_target, transform=None):
        self.data = source_data
        self.target = source_target
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        sample = {'data': self.data[idx], 'target': self.target[idx: (idx+1)]}
        
        if self.transform:
            sample = self.transform(sample)
            
        return sample


batch_size = 10

train_set = iris_dataset(source_data = train_X, source_target = train_y, transform = ToTensor())
train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=0)
val_set = iris_dataset(source_data = val_X, source_target = val_y, transform = ToTensor())
val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=True, num_workers=0)


class iris_NN(torch.nn.Module):
    
    '''network architecture for iris classification'''
    
    def __init__(self):
        super().__init__()
        self.l1 = torch.nn.Linear(4, 100)
        self.l2 = torch.nn.Linear(100, 100)
        self.l3 = torch.nn.Linear(100, 3)
        self.softmax=torch.nn.Softmax(dim=1)
        self.relu=torch.nn.ReLU()
        self.dropout = torch.nn.Dropout(p=0.1, inplace=False)
    
    def forward(self, x):
        out = self.relu(self.l1(x))
        out = self.dropout(out)
        out = self.relu(self.l2(out))
        out = self.dropout(out)
        out = self.softmax(self.l3(out))
        return out     


def train(model, device, train_loader, criterion, optimizer, epoch):

    model.train()
    train_loss = 0
    correct = 0

    for batch_idx, batch in enumerate(train_loader):
        data = batch['data'].to(device)
        target = batch['target'].squeeze().to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        train_loss += loss.item() * batch_size
        pred = output.argmax(dim=1, keepdim=True)
        correct += pred.eq(target.view_as(pred)).sum().item()

    train_loss = train_loss / len(train_loader.dataset)
    train_acc = 100. * correct / len(train_loader.dataset)

    print('Train({}): Loss: {:.4f}, Accuracy: {:.4f}%'.format(epoch, train_loss, train_acc))
    return train_loss, train_acc

def test(model, device, test_loader, criterion, epoch, file):

    model.eval()
    val_loss = 0
    correct = 0

    with torch.no_grad():
        for batch in test_loader:
            data = batch['data'].to(device)
            target = batch['target'].squeeze().to(device)
            output = model(data)
            val_loss += criterion(output, target).item() * batch_size
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()

    val_loss = val_loss / len(test_loader.dataset)
    val_acc = 100. * correct / len(test_loader.dataset)

    print('Validation({}): Loss: {:.4f}, Accuracy: {:.4f}%'.format(epoch, val_loss, val_acc))
    return val_loss, val_acc


#define main
    
seed = 29
torch.manual_seed(29)
torch.cuda.manual_seed(29)
device = 'cuda.0' if torch.cuda.is_available() else 'cpu'
device = torch.device(device)
n_epochs = 500
lr = 0.01

model = iris_NN().double().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(),lr=lr) 

best_acc = 0.0
best_epoch = None
for epoch in range(n_epochs):
    train_loss, train_acc = train(model, device, train_loader, criterion, optimizer, epoch, f)
    val_loss, val_acc = test(model, device, test_loader, criterion, epoch, f)
    if best_acc < val_acc:
        best_acc = val_acc
        best_epoch = epoch
        parameters = copy.deepcopy(model.state_dict())
    
print('Best Epoch: {}, Best Accuracy: {}'.format(best_epoch, best_acc))
print('Model_state_dict: {}'.format(parameters))


best_model = iris_NN().double()
best_model.load_state_dict(parameters) #load the model with the best parameters