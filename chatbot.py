import random
import json
import torch
from model import NeuralNet
# Import fungsi preprocessing teks
from nltk_utils import bag_of_words, tokenize


# Menentukan apakah program menggunakan GPU (CUDA) atau CPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Membaca file intents.json yang berisi intent, pattern, dan response chatbot
with open('intents.json', encoding='utf-8') as f:
    intents = json.load(f)['intents']


# Memuat data hasil training model (bobot dan metadata)
data = torch.load("data.pth", map_location=device)


# Mengambil parameter model dari data training
input_size = data["input_size"]      # Jumlah fitur input
hidden_size = data["hidden_size"]    # Jumlah neuron di hidden layer
output_size = data["output_size"]    # Jumlah kelas / intent
all_words = data['all_words']        # Semua kosakata yang digunakan saat training
tags = data['tags']                  # Label intent
model_state = data["model_state"]    # Bobot model hasil training


# Membuat model Neural Network
model = NeuralNet(input_size, hidden_size, output_size).to(device)

# Memasukkan bobot hasil training ke model
model.load_state_dict(model_state)

# Mengubah model ke mode evaluasi (inference)
model.eval()


def get_chatbot_response(msg):
    """
    Fungsi untuk memproses pesan user dan mengembalikan
    respons chatbot berdasarkan model neural network
    """

    # Memecah kalimat user menjadi kata-kata
    sentence = tokenize(msg)

    # Mengubah kalimat menjadi vektor Bag of Words
    X = bag_of_words(sentence, all_words)

    # Mengubah ke tensor PyTorch dan menyesuaikan bentuk input
    X = torch.from_numpy(X.reshape(1, -1)).to(device)

    # Melakukan prediksi menggunakan model
    output = model(X)

    # Mengambil index intent dengan skor tertinggi
    _, predicted = torch.max(output, dim=1)

    # Mengambil nama tag intent berdasarkan hasil prediksi
    tag = tags[predicted.item()]

    # Menghitung probabilitas (confidence) menggunakan softmax
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]

    # Jika tingkat keyakinan model di atas 75%
    if prob.item() > 0.75:
        # Cari intent yang sesuai dengan tag hasil prediksi
        for intent in intents:
            if intent["tag"] == tag:
                # Mengembalikan jawaban secara acak
                return random.choice(intent["responses"])

    # Jika confidence rendah, kembalikan jawaban default
    return "Maaf, saya belum mengerti 😅"