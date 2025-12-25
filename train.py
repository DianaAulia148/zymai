import numpy as np
import random
import json

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from nltk_utils import bag_of_words, tokenize, stem
from model import NeuralNet

# ===================== LOAD DATASET =====================
# Membaca file intents.json yang berisi pola kalimat dan intent
with open('intents.json', 'r') as f:
    intents = json.load(f)

all_words = []  # Menyimpan semua kata
tags = []       # Menyimpan semua label intent
xy = []         # Menyimpan pasangan (kata, tag)

# Loop setiap intent dalam dataset
for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)  # Menyimpan tag intent

    for pattern in intent['patterns']:
        w = tokenize(pattern)     # Memecah kalimat menjadi kata
        all_words.extend(w)       # Menambahkan kata ke vocabulary
        xy.append((w, tag))       # Menyimpan pasangan kata dan tag

# ===================== PREPROCESSING =====================
ignore_words = ['?', '.', '!']  # Tanda baca yang diabaikan
# Stemming dan lowercase
all_words = [stem(w) for w in all_words if w not in ignore_words]

# Menghapus duplikasi dan mengurutkan
all_words = sorted(set(all_words))
tags = sorted(set(tags))

# Menampilkan informasi dataset
print(len(xy), "patterns")
print(len(tags), "tags:", tags)
print(len(all_words), "unique stemmed words:", all_words)

# ===================== DATA TRAINING =====================
X_train = []  # Fitur
y_train = []  # Label

for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence, all_words)  # Bag of Words
    X_train.append(bag)

    label = tags.index(tag)  # Label berupa index kelas
    y_train.append(label)

# Konversi ke array NumPy
X_train = np.array(X_train)
y_train = np.array(y_train)

# ===================== HYPERPARAMETER =====================
num_epochs = 1000       # Jumlah epoch training
batch_size = 8          # Ukuran batch
learning_rate = 0.001   # Learning rate

input_size = len(X_train[0])  # Jumlah fitur
hidden_size = 8               # Neuron hidden layer
output_size = len(tags)       # Jumlah kelas intent

print(input_size, output_size)

# ===================== CUSTOM DATASET =====================
class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    # Mengambil satu data berdasarkan index
    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    # Mengembalikan jumlah data
    def __len__(self):
        return self.n_samples

dataset = ChatDataset()

# ===================== DATALOADER =====================
# Membagi data ke batch dan mengacak data
train_loader = DataLoader(
    dataset=dataset,
    batch_size=batch_size,
    shuffle=True,
    num_workers=0
)

# ===================== DEVICE =====================
# Menggunakan GPU jika tersedia
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ===================== MODEL =====================
# Inisialisasi model neural network
model = NeuralNet(input_size, hidden_size, output_size).to(device)

# ===================== LOSS & OPTIMIZER =====================
criterion = nn.CrossEntropyLoss()  # Loss klasifikasi multi-kelas
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

# ===================== TRAINING =====================
for epoch in range(num_epochs):
    for (words, labels) in train_loader:
        words = words.to(device)
        labels = labels.to(dtype=torch.long).to(device)

        outputs = model(words)           # Forward pass
        loss = criterion(outputs, labels)  # Hitung loss

        optimizer.zero_grad()  # Reset gradien
        loss.backward()        # Backpropagation
        optimizer.step()       # Update bobot

    # Menampilkan loss setiap 100 epoch
    if (epoch + 1) % 100 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

print(f'final loss: {loss.item():.4f}')

# ===================== SAVE MODEL =====================
# Menyimpan model dan metadata
data = {
    "model_state": model.state_dict(),  # Bobot model
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,             # Vocabulary
    "tags": tags                        # Label intent
}

FILE = "data.pth"
torch.save(data, FILE)  # Simpan ke file

print(f'Training selesai. File disimpan sebagai {FILE}')