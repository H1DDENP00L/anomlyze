import sys
import torch
import torch.nn as nn
import Core.utilities.config as cfg


class Goomba(nn.Module):
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__()
        self.input_size = input_size
        self.seq_length = seq_length
        self.device = device        
        self.num_layers = num_layers
        self.hidden_layer_size = hidden_layer_size    
        self.rel = nn.ReLU()        
        self.linear1 = nn.Linear(self.input_size*self.seq_length, hidden_layer_size)
        self.linear2 = nn.Linear(hidden_layer_size, output_size)
        self.softmax = nn.Softmax(dim=1)

    
    def forward(self, input_seq): # BxCxL    
        out = self.linear1(input_seq.reshape(len(input_seq), self.input_size*self.seq_length))
        out = self.rel(out)
        return self.linear2(out)


    def predict(self, input_seq):
        return self.softmax(self.forward(input_seq))


class SimpleGura(nn.Module):
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__()
        self.seq_length = seq_length
        self.device = device        
        self.num_layers = num_layers
        self.hidden_layer_size = hidden_layer_size
        self.lstm = nn.LSTM(input_size,
                            hidden_layer_size,
                            num_layers=num_layers,
                            batch_first=batch_first)        
        nn.init.xavier_normal_(self.lstm.weight_ih_l0, gain=1.0)
        nn.init.xavier_normal_(self.lstm.weight_hh_l0, gain=1.0)        
        self.rel = nn.ReLU()        
        self.linear = nn.Linear(hidden_layer_size*self.seq_length,
                                output_size)        
        self.softmax = nn.Softmax(dim=1)

    
    def forward(self, input_seq): # BxCxL     
        self.rebuildСell(len(input_seq))
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        return self.linear(lstm_out.reshape(len(input_seq), self.hidden_layer_size*self.seq_length))

    
    def predict(self, input_seq):
        return self.softmax(self.forward(input_seq))

    
    def rebuildСell(self, seq_length):
        '''Эта штука нужна для тренировки, чтобы обнулять память между примерами'''
        self.hidden_cell = (torch.zeros(self.num_layers,
                                        seq_length,
                                        self.hidden_layer_size).to(self.device), # h_0
                            torch.zeros(self.num_layers, 
                                        seq_length, 
                                        self.hidden_layer_size).to(self.device)) # c_0


class DropoutGura(SimpleGura):
    '''+Дропаут'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True,
                 dropout_p=0.7,
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length, hidden_layer_size, num_layers, output_size, batch_first, device)
        self.drop = nn.Dropout(p=dropout_p)

    
    def forward(self, input_seq): # BxCxL     
        self.rebuildСell(len(input_seq))            
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        lstm_out = self.drop(lstm_out)
        return self.linear(lstm_out.reshape(len(input_seq), self.hidden_layer_size*self.seq_length))


class NormGura(SimpleGura):
    '''+Батч-нормализация'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length, hidden_layer_size, num_layers, output_size, batch_first, device)
        self.bthnorm = nn.BatchNorm1d(num_features=self.seq_length,
                                      eps=0.001,
                                      momentum=0.99)

    
    def forward(self, input_seq): # BxCxL     
        self.rebuildСell(len(input_seq))            
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        lstm_out = self.bthnorm(lstm_out)
        return self.linear(lstm_out.view(len(input_seq), self.hidden_layer_size*self.seq_length))


class MegaGura(SimpleGura):
    '''Неповторимый оригинал'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length, hidden_layer_size, num_layers, output_size, batch_first, device)    
        self.bthnorm = nn.BatchNorm1d(num_features=self.seq_length,
                                      eps=0.001,
                                      momentum=0.99)      
        self.drop = nn.Dropout(p=0.7)


    def forward(self, input_seq): # BxCxL     
        self.rebuildСell(len(input_seq))            
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        lstm_out = self.bthnorm(lstm_out)
        lstm_out = self.drop(lstm_out)
        return self.linear(lstm_out.view(len(input_seq), self.hidden_layer_size*self.seq_length))


class CustomWeightGura(SimpleGura):
    '''Попытка сжать входные точки из (25, 2) в (25)'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__(input_size // 2,
                         seq_length, hidden_layer_size, num_layers, output_size, batch_first, device)
        self.weight = nn.parameter.Parameter(torch.FloatTensor(input_size // 2, 2))
        self.bias = nn.parameter.Parameter(torch.rand(2))
        nn.init.xavier_normal_(self.weight.data, gain=1.0)       


    def forward(self, input_seq): # BxCxL     
        mul = input_seq * self.weight + self.bias
        ftrs = mul[:,:,:,0] + mul[:,:,:,1] # (ppl_count, time_step, pts_count)
        self.rebuildСell(len(input_seq))
        lstm_out, self.hidden_cell = self.lstm(ftrs, self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        return self.linear(lstm_out.reshape(len(input_seq), self.hidden_layer_size*self.seq_length))


class PointsConvGura(SimpleGura):
    '''Попытка свернуть входные точки (шта?)'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM,
                 seq_length=3,
                 hidden_layer_size=512,
                 num_layers=1,
                 output_size=5,
                 out_channels=3,
                 batch_first=True,
                 device=None):
        super().__init__(input_size // 2 * out_channels // seq_length,
                         seq_length, hidden_layer_size, num_layers, output_size, batch_first, device)
        self.conv = nn.Conv2d(in_channels=seq_length, out_channels=out_channels, kernel_size=(1, 2))


    def forward(self, input_seq): # BxCxL     
        ftrs = self.conv(input_seq)
        
        self.rebuildСell(len(input_seq))
        lstm_out, self.hidden_cell = self.lstm(ftrs.view(len(input_seq), self.seq_length, -1), 
                                               self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        return self.linear(lstm_out.reshape(len(input_seq), self.hidden_layer_size*self.seq_length))


class FullyEncodedGura(SimpleGura):
    '''Попытка накинуть полносвязный слой в начало'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM,
                 seq_length=3,
                 hidden_layer_size=512,
                 num_layers=1,
                 output_size=5,
                 out_features=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM,
                 batch_first=True,
                 device=None):
        super().__init__(out_features,
                         seq_length, hidden_layer_size, num_layers, output_size, batch_first, device)
        self.encoder = nn.Linear(input_size, out_features)


    def forward(self, input_seq): # BxCxL     
        ftrs = self.encoder(input_seq.view((len(input_seq), self.seq_length, -1)))
        self.rebuildСell(len(input_seq))
        lstm_out, self.hidden_cell = self.lstm(ftrs, self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        return self.linear(lstm_out.reshape(len(input_seq), self.hidden_layer_size*self.seq_length))


class DamboBimboGoomba(SimpleGura):
    '''На вход влетает нарисованный точками и линиями скелет человека'''
    def __init__(self, 
                 input_size=512,
                 seq_length=3,
                 hidden_layer_size=512,
                 num_layers=1,
                 output_size=5,
                 batch_first=True,
                 device=None):
        super().__init__(input_size,
                         seq_length, hidden_layer_size, num_layers, output_size, batch_first, device)
        self.Biba = nn.Conv2d(in_channels=1, 
                              out_channels=4, 
                              kernel_size=3,
                              stride=3)
        self.Boba = nn.Conv2d(in_channels=4, 
                              out_channels=8, 
                              kernel_size=3,
                              stride=3)


    def forward(self, input_seq): # BxCxL  
        aa = input_seq.unsqueeze(2)
        batch_size, timesteps, C, H, W = aa.size()
        Segs = self.Boba(self.Biba(aa.view(batch_size * timesteps, C, H, W)))
        self.rebuildСell(len(input_seq))
        lstm_out, self.hidden_cell = self.lstm(Segs.view(batch_size, timesteps, -1),
                                               self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        return self.linear(lstm_out.reshape(len(input_seq), self.hidden_layer_size*self.seq_length))


class MotionGura(SimpleGura):
    '''На вход подается разность скелетов'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length-1,
                         hidden_layer_size, num_layers, output_size, batch_first, device)
        self.tanh = nn.Tanh()


    def forward(self, input_seq): # BxCxL   
        self.rebuildСell(len(input_seq))   
        input_seq = self.tanh(input_seq)
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)
        lstm_out = self.rel(lstm_out)
        return self.linear(lstm_out.reshape(len(input_seq), self.hidden_layer_size*self.seq_length))


class HiddenGura(SimpleGura):
    '''Предсказание делается на основе скрытого состояния LSTM + 1 FC слой'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length,
                         hidden_layer_size, num_layers, output_size, batch_first, device)
        self.linear = nn.Linear(hidden_layer_size, hidden_layer_size // 2)  
        self.linear2 = nn.Linear(hidden_layer_size // 2, output_size)  


    def forward(self, input_seq): # BxCxL   
        self.rebuildСell(len(input_seq))   
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)

        h_n = self.rel(self.hidden_cell[0])[0]
        # Short tail
        h_n = self.linear(h_n.reshape(len(input_seq), self.hidden_layer_size))
        return self.linear2(h_n)


class HiddenDropoutGura(DropoutGura):
    '''Предсказание делается на основе скрытого состояния LSTM + 1 FC слой + Dropout'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True,
                 dropout_p=0.7,
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length, hidden_layer_size, num_layers, output_size, batch_first, dropout_p, device)
        self.drop = nn.Dropout(p=dropout_p)
        self.linear = nn.Linear(hidden_layer_size, hidden_layer_size // 2)  
        self.linear2 = nn.Linear(hidden_layer_size // 2, output_size)  


    def forward(self, input_seq): # BxCxL   
        self.rebuildСell(len(input_seq))   
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)

        h_n = self.rel(self.hidden_cell[0])[0]
        h_n = self.drop(h_n)
        # Short tail
        h_n = self.linear(h_n.reshape(len(input_seq), self.hidden_layer_size))
        return self.linear2(h_n)


class HiddenNormGura(NormGura):
    '''Предсказание делается на основе скрытого состояния LSTM + 1 FC слой + Dropout'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length,
                         hidden_layer_size, num_layers, output_size, batch_first, device)
        self.linear = nn.Linear(hidden_layer_size, hidden_layer_size // 2)  
        self.linear2 = nn.Linear(hidden_layer_size // 2, output_size)  
        self.bthnorm = nn.BatchNorm1d(num_features=hidden_layer_size,
                                      eps=0.001,
                                      momentum=0.99)


    def forward(self, input_seq): # BxCxL   
        self.rebuildСell(len(input_seq))   
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)

        h_n = self.rel(self.hidden_cell[0])[0]
        # Short tail
        h_n = self.bthnorm(h_n)
        h_n = self.linear(h_n.reshape(len(input_seq), self.hidden_layer_size))
        return self.linear2(h_n)


class FatHiddenGura(HiddenGura):
    '''Предсказание делается на основе скрытого состояния LSTM + 2 FC слоя'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length,
                         hidden_layer_size, num_layers, output_size, batch_first, device)
        self.linear2 = nn.Linear(hidden_layer_size // 2, hidden_layer_size // 4) 
        self.linear3 = nn.Linear(hidden_layer_size // 4, output_size)  


    def forward(self, input_seq): # BxCxL   
        self.rebuildСell(len(input_seq))   
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)
        h_n = self.rel(self.hidden_cell[0])[0]
        # Fat tail
        h_n = self.linear(h_n.reshape(len(input_seq), self.hidden_layer_size))
        h_n = self.linear2(h_n)
        return self.linear3(h_n)


class CellGura(SimpleGura):
    '''Предсказание делается на основе ячейки LSTM + 1 FC слой'''
    def __init__(self, 
                 input_size=cfg.BODY_POINTS_NUM*cfg.BODY_POINTS_DIM, 
                 seq_length=3, 
                 hidden_layer_size=512,
                 num_layers=1, 
                 output_size=5, 
                 batch_first=True, 
                 device=torch.device('cpu')):
        super().__init__(input_size, seq_length,
                         hidden_layer_size, num_layers, output_size, batch_first, device)
        self.linear = nn.Linear(hidden_layer_size, hidden_layer_size // 2)  
        self.linear2 = nn.Linear(hidden_layer_size // 2, output_size)  


    def forward(self, input_seq): # BxCxL   
        self.rebuildСell(len(input_seq))   
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), len(input_seq[0]), -1),
                                               self.hidden_cell)
        с_n = self.rel(self.hidden_cell[1])[0]
        # Short tail
        с_n = self.linear(с_n.reshape(len(input_seq), self.hidden_layer_size))
        return self.linear2(с_n)
