from main import Song, get_mash_pairs
import echonest.remix.audio as audio
from pyechonest import config
import json
import matplotlib.pyplot as plt
import numpy as np
config.ECHO_NEST_API_KEY = "O63DZS2LNNEWUO9GC"

key_dict = {
	'C': 0,
	'a' : 0,
	'G': 1,
	'e' : 1,
	'D': 2,
	'b' : 2,
	'A': 3,
	'f#' : 3,
	'E': 4,
	'c#' : 4,
	'B': 5,
	'g#' : 5,
	'F#': 6,
	'd#' : 6,
	'C#': 7,
	'a#' : 7,
	'G#': 8,
	'f' : 8,
	'D#': 9,
	'c' : 9,
	'A#': 10,
	'g' : 10,
	'F' : 11,
	'd' : 11,
}

def keyDistance(key1, key2):
	"""
	Takes two keys (strings) and returns their circular distance on the wheel of fifths
	"""
	lowKey = min(key_dict[key1], key_dict[key2])
	highKey = max(key_dict[key1], key_dict[key2])
	return (min(abs(highKey-lowKey), abs(lowKey + 12 - highKey)))

with open('songs.json') as data_file:
	data = json.load(data_file)

songs = []
for song in data:
	new_song = Song(
		name=song['Name'],
		fname=song['File'],
		mix_in=song['MixIn'],
		mix_out=song['MixOut'],
		unary_factor=song['Unary'],
		song_id=song['SongId'],
		bpm=song['BPM'],
		key=song['Key']
	)
	songs.append(new_song)
mash_dict = get_mash_pairs(songs)
graph_data_x = []
graph_data_y = []
for (song1, song2) in mash_dict:
	graph_data_x.append(keyDistance(song1.key, song2.key))
	graph_data_y.append(mash_dict[(song1, song2)])
print graph_data_x
print graph_data_y
m, b = np.polyfit(graph_data_x,graph_data_y, 1)
best_fit_x = range(7)
best_fit_y = []
for x in best_fit_x:
	best_fit_y.append(m*x + b)
plt.scatter(graph_data_x, graph_data_y)
plt.plot(best_fit_x, best_fit_y, '-')
plt.xlabel('Key Distance')
plt.ylabel('Un-Mashability')
plt.title('Mashability Correlated with Key')
plt.show()




