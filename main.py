import echonest.remix.audio as audio
import echonest.remix.action as action
import echonest.remix.modify as modify
import dirac
import json
import itertools


# This is a dict of dicts storing how well key1 mashes out into key2
MASHABILITY_DICT = {}

# This is the number of beats we wish to transition, should be a multiple of 4
# Mix in and mix out points have to be set accordingly
MIX_LENGTH = 32

class Song(object):
	def __init__(self, name, fname, mix_in, mix_out, unary_factor, song_id, bpm):
		self.name = name
		self.file = fname
		self.mix_in = mix_in
		self.mix_out = mix_out
		self.unary_factor = unary_factor
		self.song_id = song_id
		self.bpm = bpm
		self.AudioFile = audio.LocalAudioFile("mp3/" + fname)

def mashability(song1, song2):
	"""
	Returns how well song1 transitions into song2 using cosine matrix similarity
	and FFT semitone bin approximation matrices
	"""
	# Need to implement
	return 1


def renderList(songList, outFile):
	"""
	Takes a list of songs and outputs them to outFile
	Has to beatmatch and cross fade
	Assumes songList >= 2
	"""
	mixOutSeg = None
	currAudio = None
	for i in range(len(songList)):
		currSong = songList[i]
		currBeats = currSong.AudioFile.analysis.beats
		# This happens on the first iteration, nothing to mix in so just play until mix out
		if not mixOutSeg:
			currAudio = audio.getpieces(
							currSong.AudioFile,
							currBeats[currSong.mix_in:currSong.mix_out]
			)
		else:
			mixInSeg = audio.getpieces(
							currSong.AudioFile,
							currBeats[currSong.mix_in:currSong.mix_in+MIX_LENGTH])
			transition_length = 60.0/128.0 * MIX_LENGTH 
			mixInSeg.encode("Mixinseg.mp3")
			mixOutSeg.encode("MixOutseg.mp3")
			print transition_length
			transitionSeg = action.Crossfade([mixOutSeg, mixInSeg], [0.0, 0.0], transition_length).render()
			transitionSeg.encode("transition.mp3")
			#return
			mainSeg = audio.getpieces(
							currSong.AudioFile,
							currBeats[currSong.mix_in+MIX_LENGTH:currSong.mix_out])
			currAudio = audio.assemble([currAudio, transitionSeg, mainSeg])

		mixOutSeg = audio.getpieces(
						currSong.AudioFile,
						currBeats[currSong.mix_out:currSong.mix_out+MIX_LENGTH])
	#currAudio = audio.assemble([currAudio, mixOutSeg])
	currAudio.encode(outFile)


def main():
	# First parse our song data
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
			bpm=song['BPM']
		)
		songs.append(new_song)

	# Determine all pairwise mashabilities, update the dict
	for song1 in songs:
		new_dict = {}
		for song2 in songs:
			if song1 != song2:
				new_dict[song2] = mashability(song1, song2)
		MASHABILITY_DICT[song1] = new_dict

	from csp import genMix
	# Use a CSP to solve generate a list of songs
	mixList = genMix(songs, MASHABILITY_DICT)

	# Actually render the list to a file
	renderList(mixList, "MixOut.mp3")

if __name__ == "__main__":
    main()


