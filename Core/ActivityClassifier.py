import os
import sys
import torch
import random
import pickle
import pandas as pd
import numpy as np
from tqdm import tqdm
from torch.optim import lr_scheduler
from torch.utils.data import Dataset, DataLoader
from .utilities.fast_tools import fast_personwise_normalize
from .utilities.transforms import RandomNoise
from .Nets import *


class KeypointsDataset(Dataset):
    def __init__(self, X, Y, seq_len, transform=None):    
        self.size = len(X) // seq_len # сколько "троек" будет
        self.human_shape = X[0].shape # потенциально это можно удалить и сразу кидать X[0]
        X = np.expand_dims(X, 1) # размерность под "тройки"
        X = X[:self.size*seq_len].reshape(-1, seq_len, *self.human_shape)
        Y = Y[:self.size*seq_len][::seq_len]
        # ------------
        self.X = X
        self.Y = torch.LongTensor(Y)
        self.transform = transform
            
    def __len__(self):
        return self.size
        
    def __getitem__(self, idx):
        # Возможно, стоит тут кастовать torch.Tensor
        X = self.X[idx]        
        if self.transform:
            X = self.transform(X)
        return (torch.FloatTensor(X), self.Y[idx])


class ActivityClassifier():
    def __init__(self, 
                 num_of_classes, 
                 input_size=50, 
                 seq_length=3, 
                 hidden_layer_size=512, 
                 weights_path=None,
                 device=None):
        self.seq_length = seq_length

        if device:
            self.device = device
        else:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.net = FullyEncodedGura(seq_length=seq_length,
                                    input_size=input_size,
                                    hidden_layer_size=hidden_layer_size, 
                                    out_features=input_size,
                                    output_size=num_of_classes,
                                    device=self.device)
        if weights_path:
            self.net.load_state_dict(torch.load(weights_path, weights_only=True))
        self.net = self.net.to(self.device)

    
    def setNet(self, net, seq_length, verbose=True):
        self.net = net.to(self.device)
        self.net.device = self.device
        self.seq_length = seq_length
        if verbose:
            print(self.net.__class__.__name__)

    
    def saveWeights(self, out_path):
        torch.save(self.net.state_dict(), out_path)
        return 0

    
    def loadWeights(self, weights_path):
        self.net.load_state_dict(torch.load(weights_path, weights_only=True))
        self.net = self.net.to(self.device)

    
    def predictAction(self, points, threshold=0.5, transform=None):
        if transform:
            pass # TBC
        data = torch.FloatTensor(points)
        data = data.to(self.device)
        self.net.eval()
        return self.net.predict(data).cpu() # > theshold

        
    def trainEpoch(self, loader, loss_func, optimizer):
            self.net.train()
            correct = loss_sum = 0
            for data, mark in loader:  
                output = self.net(data.to(self.device))  
                loss = loss_func(output, mark.to(self.device))
                loss_sum += loss                
                pred = output.argmax(dim=1)
                correct += pred.eq(mark.to(self.device)).sum()                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            acc = 100.0 * correct / len(loader.dataset)
            loss = loss_sum / len(loader)
            return acc.cpu().detach().item(), loss.cpu().detach().item()

    
    def validEpoch(self, loader, loss_func):
            self.net.eval()
            correct = loss_sum = 0
            for data, mark in loader:
                output = self.net(data.to(self.device))
                loss = loss_func(output, mark.to(self.device))
                loss_sum += loss
                pred = output.argmax(dim=1)
                correct += pred.eq(mark.to(self.device)).sum()
            acc = 100.0 * correct / len(loader.dataset)
            loss = loss_sum / len(loader)
            return acc.cpu().detach().item(), loss.cpu().detach().item()

    
    def trainNet(self,
                 train_path,
                 val_path,
                 epochs=5,
                 batch_size=850,
                 patience=5,
                 checkpoint_dir='./Weights',
                 prefix='best_weight',
                 verbose=True,
                 **kwargs):
        loss_function = kwargs.get('loss_func', torch.nn.CrossEntropyLoss)()
        optimizer = kwargs.get('optim', torch.optim.Adam)(self.net.parameters(), **kwargs.get('optim_args'))

        if kwargs.get('scheduler'):
            scheduler = kwargs['scheduler'](optimizer, **kwargs.get('scheduler_args'))
        else:
            scheduler = None
            
        X, Y = self.getDataFromCSV(train_path)
        vX, vY = self.getDataFromCSV(val_path)
        
        history = {'train_accs': [], 'train_losses': [], 'val_accs':[], 'val_losses': []}
        history['epochs'] = epochs
        history['batch_size'] = batch_size
        history['patience'] = patience
        history['loss_function'] = str(loss_function)
        history['optimizer'] = str(optimizer)
        history['scheduler'] = str(scheduler)
        history['net_info'] = str(self.net)
        history['seq_length'] = self.seq_length

        one_file_mode = kwargs.get('one_file_mode', False)
        if one_file_mode:
            full_dataset = KeypointsDataset(X, Y, self.seq_length, kwargs.get('transform'))
            dataset, val_dataset = torch.utils.data.random_split(full_dataset, [0.8, 0.2])
        else:
            dataset = KeypointsDataset(X, Y, self.seq_length, kwargs.get('transform'))
            val_dataset = KeypointsDataset(vX, vY, self.seq_length, kwargs.get('val_transform'))
            
        train_loader = DataLoader(dataset=dataset, batch_size=batch_size)#, shuffle=True)
        val_loader = DataLoader(dataset=val_dataset, batch_size=batch_size) 

        no_improvements = 0
        
        min_val_loss = kwargs.get('min_val_loss', np.inf)
        max_val_acc = kwargs.get('max_val_acc', 0)
        acc_diff_eps = kwargs.get('acc_diff_eps', 1)
        loss_diff_eps = kwargs.get('loss_diff_eps', 0.5)
        
        loss_function = loss_function.to(self.device)     
            
        postfix = 'VL-_TR-'
        
        for epoch in range(epochs):
            train_acc, train_loss = self.trainEpoch(train_loader, loss_function, optimizer)
            val_acc, val_loss = self.validEpoch(val_loader, loss_function)
            history['train_accs'].append(train_acc)
            history['train_losses'].append(train_loss)
            history['val_accs'].append(val_acc)
            history['val_losses'].append(val_loss)
            result = f'EP: {epoch}\t|TR ACC/LOSS: {train_acc:.4f}/{train_loss:.4f}|VL ACC/LOSS: {val_acc:.4f}/{val_loss:.4f}'

            if val_loss < min_val_loss:
                min_val_loss = val_loss
                history['best_epoch'] = epoch
                history['best_val_loss'] = min_val_loss
                postfix = f'VL{round(val_acc, 2)}_TR{round(train_acc, 2)}'
                no_improvements = self.saveWeights(f'{checkpoint_dir}/best_weights.pt')
                result += ' ♂'
            else:
                no_improvements += 1
            
            # На всякий случай сохраняем историю, чтобы не потерять
            history_path = f'{checkpoint_dir}/history.pkl'
            with open(history_path, 'wb') as file:
                pickle.dump(history, file)

            if verbose:
                print(result)
            
            if no_improvements == patience:
                print('Ранний останов!!1')
                break

            if scheduler:
                scheduler.step()
        try:
            net_name = self.net.__class__.__name__
            os.rename(src=f'{checkpoint_dir}/best_weights.pt', 
                      dst=f'{checkpoint_dir}/{prefix}_{net_name}_{postfix}.pt')
            
            os.rename(src=f'{checkpoint_dir}/history.pkl',
                      dst=f'{checkpoint_dir}/{prefix}_{net_name}_{postfix}.pkl') 
        except FileExistsError:
            print('Файл уже существует, ничего не буду делать')
        return history 

    
    def getDataFromCSV(self, in_path, normalize=True):
        raw_data = pd.read_csv(in_path)   
        num_of_classes = raw_data['Class'].nunique()
        X = raw_data.iloc[:, :-1].to_numpy() # -1 - отпиливаем классы
        Y = raw_data['Class'].to_numpy() # а вот классы
        X = np.reshape(X,(-1, X.shape[1] // 2, 2)) # пытаемся получить пары координат
        if normalize:
            for i in range(len(X)):
                X[i] = fast_personwise_normalize(X[i])[1] # возвращает rect и person, берем person
        return X, Y
