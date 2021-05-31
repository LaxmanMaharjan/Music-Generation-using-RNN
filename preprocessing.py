import os
import music21 as m21
import json
import torch
import numpy as np
import torch.nn.functional as F

path = '/home/LaxmanMaharjan/Project/Music Generation using C-RNN GAN/Music Generation/Dataset'

ACCEPTABLE_DURATIONS = [
    0.25, # 16th note
    0.5, # 8th note
    0.75, # Dotted 8th note
    1.0, # Quarter note
    1.5, # Dotted quarter note
    2, # Half note
    3, # Dotted Half note
    4 # Whole note

]
# SEQUENCE LENGTH is the fixed length sequence to pass in LSTM network
SEQUENCE_LENGTH = 64 
MAPPING_PATH = 'mapping.json'
ENCODED_FILE_PATH = 'Encoded_Path'
SINGLE_ENCODED_FILE_PATH = 'Single_Encoded_Dataset'

def has_acceptable_duration(song,acceptable_durations):
    ''' Check if the song is in Acceptable duration
    Args:
        song: song midi file
        acceptable_durations: Acceptable duration
    '''
    for note in song.flat.notesAndRests:
        if note.duration.quarterLength not in acceptable_durations:
            return False 
    return True

def load_songs(dataset_path):
    ''' Load all the midi files from the dataset_path.

    Args:
        dataset_path: It is datas et path
    Return:
        song: It is midi file
    '''
    songs = []
    for path, subdir, files in os.walk(dataset_path):
        for file in files:
            file_path = os.path.join(path, file)
            song = m21.converter.parse(os.path.join(file_path))
            songs.append(song)
            print(file)
            parts = song.getElementsByClass(m21.stream.Part)
            measure_part0 = parts[0].getElementsByClass(m21.stream.Measure)
            #key1 = measure_part0[0][4]
            
            key = song.analyze('key')
            print(song)
            print(key.tonic.name, key.mode)
        
    return songs

def transpose(song):
    """ Do transpose all songs to C major/ A minor key.
    
    Transposing is important because it is easy to analyze in only one key rather than analyzing in all possible 21 keys

    Args:
        song: song in midi file
    
    """
    key = song.analyze('key') # getting key of the song
    
    # getting interval for transposition e.g Bmaj -> Cmaj, Bmin -> Amin
    if key.mode == 'major':
        interval = m21.interval.Interval(key.tonic, m21.pitch.Pitch('C'))
        
    elif key.mode == 'minor':
        interval = m21.interval.Interval(key.tonic, m21.pitch.Pitch('A'))
        
        # Transposing song by calculating interval
    transposed_song = song.transpose(interval)

    return transposed_song

def encode_song(song, time_step = 0.25):
    """ Midi note number of c4 = 60, pitch = 60 C4 duration = 1.0 -> [60, '_', '_', '_'] '_' represent note

    Arg:
        song: midi file


    """
    encoded_song = []

    for event in song.flat.notesAndRests:

        # handle notes
        if isinstance(event, m21.note.Note):
            symbol = event.pitch.midi # midi number for pitch
        
        #handling Rest
        elif isinstance(event, m21.note.Rest):
            symbol = 'r'

        # convert the note/rest into time series notation
        # time_step = 0.25 because there will be 16 samples per bar
        # 4 samples per quarter note 
        # i.e 16th note
        steps = int(event.duration.quarterLength / time_step) 
        for step in range(steps):
            if step == 0:
                encoded_song.append(symbol)
            else:
                encoded_song.append('_')

        # cast encoded song to a str
    encoded_song = ' '.join(map(str,encoded_song))

    return encoded_song

def preprocess(dataset_path):
    """ Do dataset Preprocessing  
    
    This function does the preprocessing and the final output is encoded form of the song which is then saved into the File_ENCODED_PATH
    Args:
        dataset_path: path to dataset in midi format
    """
    print("loading songs")
    songs = load_songs(dataset_path)
    #songs = []
    #songs.append(m21.converter.parse(dataset_path))
    print(f'\n\nNumber of loaded songs:{len(songs)}')
    i = 0 
    for i, song in enumerate(songs):
        #filter out songs that have non acceptable durations
        if not has_acceptable_duration(song,ACCEPTABLE_DURATIONS):
            continue

        # transposing the song into C major/ A minor
        song = transpose(song) 

        # Encode song in Time series representation
        encoded_song = encode_song(song)

        # save songs to text file
        save_path = os.path.join(ENCODED_FILE_PATH, str(i))
        with open(save_path,'w') as file:
            file.write(encoded_song)
 
def load(file_path):
    """ Load the encoded file
   
   This function is basically to load individual encoded file
    Args:
        file_path: path of the file
    Return:
        song: individual encoded file
     """
    with open(file_path, 'r') as file:
         song = file.read()
    return song

def create_single_file_dataset(dataset_path, file_dataset_path, sequence_length):
    """ Create a single file for encoded dataset
    
    Args:
        dataset_path: path of individual encoded files 
        file_dataset_path: path to save encoded file as a single file
    Return:
        songs: single string which contains all the encoded files
    """
    next_song_delimiter = '/ ' * sequence_length
    songs = ''

    # load encoded songs and add delimiters between songs
    for path, _, files in os.walk(dataset_path):
        for file in files:
            file_path = os.path.join(path, file)
            song = load(file_path)
            songs = songs + song + ' ' + next_song_delimiter

    songs = songs[:-1] # slicing off last space charater form songs string

    # save string that contains all the dataset in encoded form
    with open(file_dataset_path, 'w') as file:
        file.write(songs)

    return songs

def create_mapping(songs, mapping_path):
    """ map time series representation to integers
    
    This function creates a look-up table for each symbol in the encoded dataset in json file with save to MAPPING_PATH
    Args:
        songs: encoded all songs in single string

    """
    mappings = {}

    # indentify the vocabulary: it is all the symbols that we have inencoded dataset
    # songs is now list of all the symbols in the encoded dataset, split by default spilts in space
    songs = songs.split()

    vocabulary = list(set(songs)) # list of all unique symbols
    
    # create mappings
    for i,symbol in enumerate(vocabulary):
        mappings[symbol] = i # making lookup table for all the symbols

    # save vocabulary to a json file
    with open(mapping_path,'w') as file:
        json.dump(mappings, file, indent=4)

def convert_songs_to_int(songs):
    """ Convert single file with all encoded songs file to int
    
    Args:
        songs: single file with all encoded songs
    Return:
        int_songs: songs with int values instead of encoded symbols
    """
    int_songs = []
    # load mappings
    with open(MAPPING_PATH, 'r') as file:
        mappings = json.load(file)

    # cast songs which is in string to list split combined songs to individual song
    songs = songs.split()

    # map songs to int from mappings look up table
    for symbol in songs:
        int_songs.append(mappings[symbol])
    
    return int_songs

def generate_training_sequences(sequence_length):
    """ Generating sequential dataset to feed in LSTM network
    
    Args:
        sequence_length: length of sequence
    """
    # load songs and map them into int
    songs = load(SINGLE_ENCODED_FILE_PATH)
    int_songs = convert_songs_to_int(songs)

    # genertae the training sequences
    # consider if dataset has 100 symbols and 64 sequence length then the number of sequences generated = 100-64

    inputs = []
    targets = []

    num_sequences = len(int_songs) - sequence_length
    # generating input sequences for network
    for i in range(num_sequences):
        # sliding by one step in dataset to generate sequences
        inputs.append(int_songs[i:i+sequence_length])
        # target is next note or rest in the sequence just after sequence length
        targets.append(int_songs[i+sequence_length]) 

        # One-Hot Encoding the sequences of dataset
        # inputs: (number of sequences, sequence_length, vocabulary_size)
    vocabulary_size = len(set(int_songs))
    # inputs is torch.tensor type whose shape is (number of sequences, sequence_length, vocabulary_size)
    inputs = F.one_hot(torch.tensor(inputs), num_classes=vocabulary_size)
            
    return inputs, targets
        


def main():
    preprocess('./Child')
    
    songs = create_single_file_dataset(ENCODED_FILE_PATH, SINGLE_ENCODED_FILE_PATH, SEQUENCE_LENGTH)
    
    create_mapping(songs, MAPPING_PATH)
    
    return (generate_training_sequences(SEQUENCE_LENGTH))
    
if __name__ == '__main__':
    
    main()
    #songs=load_songs('./Test')
    #print(len(songs))
    #for song in songs:
        #print(song.analyze('key'))
        #key = song.analyze('key')
        
        #print(transpose(song))
