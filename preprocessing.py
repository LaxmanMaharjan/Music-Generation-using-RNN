import os
import music21 as m21

path = '/home/LaxmanMaharjan/Project/Music Generation using C-RNN GAN/Music Generation/Dataset'

ACCEPTABLE_DURATIONS = [
    0.25,
    0.5,
    0.75,
    1.0,
    1.5,
    2,
    3,
    4

]

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
            break
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

    """
    print("loading songs")
    #songs = load_songs(path)
    songs = []
    songs.append(m21.converter.parse(dataset_path))
    i = 0 
    for i, song in enumerate(songs):
        #filter out songs that have non acceptable durations
        if not has_acceptable_duration(song,ACCEPTABLE_DURATIONS):
            continue

        # transposing the song
        song = transpose(song) 

        # Encode song in Time series representation
        encoded_song = encode_song(song)

        # save songs to text file
        save_path = os.path.join('Encoded_Dataset', str(i))
        with open(save_path,'w') as file:
            file.write(encoded_song)


if __name__ == '__main__':
    
    preprocess('./child01.mid')
