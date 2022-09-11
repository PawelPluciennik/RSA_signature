import os

import sounddevice as sd
import numpy as np
import PySimpleGUI as sg
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from scipy.io.wavfile import write


def dec2bin(number):
    return bin(number).replace("0b", "").zfill(8)


def generate_number():
    fs = 44100  # Częstotliwość próbkowania
    seconds = 5  # Czas trwania nagrania

    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Pauza aż nagranie się nie skończy nagrywać
    write('output.mp3', fs, myrecording)  # Zapisanie pliku do MP3

    file = open('output.mp3', "rb")  # Otwarcie pliku

    ints_from_file = []
    file_contents = file.read()

    for b in file_contents:  # Zapisanie wszystkich wartości do tablicy
        ints_from_file.append(b)

    merged_byte = []

    for number in ints_from_file:
        temp = dec2bin(number)  # Zamiana wartości decymalnych na binarne
        merged_byte.append(
            1 & (int(temp[-1]) ^ int(temp[-2]) ^ int(temp[-3])))  # Post processing z wykorzystaniem XORa oraz ANDa

    num = np.packbits(np.array(merged_byte))  # "Spakowanie" binarnych wartości do tablicy
    array_sum = 0
    for n in num:  # Zsumowanie tablicy
        array_sum += n
        if (n > 128):
            array_sum += 1

    random_number = int(str(array_sum)[-3:])  # Obcięcie pierwszych 2 (lub 3 jeśli 0 jest pierwszą liczbą) liczb z sumy

    file.close()  # Zamknięcie pliku

    if random_number < 100:  # Wygenerowanie liczby z przedzału od 101 do ok 400 w celu szybszego generowania klucza
        random_number += 100
    if random_number > 400:
        return int(random_number/3)

    return random_number  # Zwrócenie wygenerowanej liczby


random_number = generate_number()


def random(x):  # Funkcja z sztucznym argumentem ze względu na możlowość jej wywołania (callable)
    return os.urandom(random_number)  # Zwraca losową liczbę na podstawie wcześniej wygenerowanej losowej liczby


layout = [[sg.Text('Wprowadź wiadomość.')],  # Użycie prostego GUI
          [sg.InputText()],
          [sg.Submit('Dalej')]]

window = sg.Window('Okienko', layout)

event, values = window.read()
window.close()

message = values[0]
hash = hashlib.sha224(message.encode('ascii')).hexdigest()
print('Wylosowana liczba: ', random_number)
key = RSA.generate(1024, random)  # Wygenerowanie pary kluczy

encryptor = PKCS1_OAEP.new(key.public_key())  # Stworzenie enkryptora
encrypted_message = encryptor.encrypt(hash.encode('ascii'))  # Enkrypcja wiadomości

layout = [[sg.Text('Klucz prywatny')],
          [sg.InputText(key.export_key().decode('ascii'))],  # Możliwość edycji klucza prywatnego
          [sg.Submit('Dalej')]]

window = sg.Window('Okienko', layout)

event, values = window.read()
window.close()

text_input_private_key = values[0]  # Zczytanie edytowanego klucza do zmiennej

print('Wprowadzony klucz:\n', text_input_private_key, '\nOreginalny klucz:\n', key.export_key().decode('ascii'))
if text_input_private_key != key.export_key().decode('ascii'):  # Porównanie klucza prywatnego z edytowanym i wyświetlenie odpowiednich wiadomości
    sg.popup('UWAGA!\nKlucz prywanty uległ zmianie!')
else:
    sg.popup('ZGODNOŚĆ!\nKlucze się zgadzją.')
    layout = [[sg.Text('Edytuj wiadomość')],
              [sg.InputText(message)],  # Możliwość edycji wiadomosci
              [sg.Submit('Dalej')]]

    window = sg.Window('Okienko', layout)

    event, values = window.read()
    window.close()

    edited_message = values[0]

    decryptor = PKCS1_OAEP.new(key)  # Stworzenie dekryptora
    decrypted_message = decryptor.decrypt(encrypted_message)  # Dekrypcja wiadomośći
    if decrypted_message == hashlib.sha224(edited_message.encode('ascii')).hexdigest().encode('ascii'):
        sg.popup('SHA się zgadzają! Nikt nie ingerował w treść wiadomośći.')
    else:
        sg.popup('UWAGA! SHA się nie zgadzają! Ktoś ingerował w treść wiadomośći!')
    print("\nSHA oryginalnej wiadomości:", decrypted_message, "\n", "SHA edytowanej wiadomości:", hashlib.sha224(edited_message.encode('ascii')).hexdigest().encode('ascii'))




