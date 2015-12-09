import echonest.remix.audio as audio
import echonest.remix.action as action
import echonest.remix.modify as modify
import dirac
import json
import itertools
from pyechonest import config
import random
import librosa
import numpy as np
import scipy.spatial.distance as dst
import matplotlib.pyplot as plt

config.ECHO_NEST_API_KEY = "O63DZS2LNNEWUO9GC"


# This is a dict of dicts storing how well key1 mashes out into key2
MASHABILITY_DICT = {}

# This is the number of beats we wish to transition, should be a multiple of 4
# Mix in and mix out points have to be set accordingly
MIX_LENGTH = 32
NUM_SONGS = 4

class Song(object):
	def __init__(self, name, fname, mix_in, mix_out, unary_factor, song_id, bpm):
		self.name = name
		self.file = fname
		self.mix_in = mix_in
		self.mix_out = mix_out
		self.unary_factor = unary_factor
		self.song_id = song_id
		self.bpm = bpm
		print "About to try to load"
		self.AudioFile = audio.LocalAudioFile("mp3/" + fname)
		print "Done loading"

	def __repr__(self):
		return self.name
		
def get_mash_pairs(songs):
	mash_dict = {}
	for song1 in songs:
		for song2 in songs:
			if song1 != song2 and abs(song1.bpm - song2.bpm) < 30:
				mash_dict[(song1, song2)] = mashability(song1, song2)
	print mash_dict
	return mash_dict

# takes a list of two song id and returns a number between zero and 1
def mashability(song1, song2):
	"""
	Returns how well song1 transitions into song2 using cosine matrix similarity
	and FFT semitone bin approximation matrices
	"""
	sample_length = MIX_LENGTH #beats per sample
	beats1 = song1.AudioFile.analysis.beats[song1.mix_out:song1.mix_out + sample_length]
	beats2 = song2.AudioFile.analysis.beats[song1.mix_in:song1.mix_in + sample_length]
	data1 = audio.getpieces(song1.AudioFile, beats1)
	data2 = audio.getpieces(song2.AudioFile, beats2)
	data1.encode("temp1.mp3")
	data2.encode("temp2.mp3")
	y1, sr1 = librosa.load("temp1.mp3")
	y2, sr2 = librosa.load("temp2.mp3")
	S1 = np.abs(librosa.stft(y1, n_fft = 4096))
	chroma1 = librosa.feature.chroma_stft(S=S1, sr=sr1)
	S2 = np.abs(librosa.stft(y2, n_fft = 4096))
	chroma2 = librosa.feature.chroma_stft(S=S2, sr=sr2)
	im = librosa.display.specshow(chroma1,x_axis = "time",y_axis = "chroma")
	im2 = librosa.display.specshow(chroma2,x_axis = "time",y_axis = "chroma")
	# plt.show()
	orthogonal_arr = []
	for i in range(min(chroma1.shape[1],chroma2.shape[1])):
		orthogonal_arr.append(dst.cosine(chroma1[:,i],chroma2[:,i]))
	return sum(orthogonal_arr)/len(orthogonal_arr)


def get_unary_list(songs):
	"""
	Takes in a list of songs, and returns a dict where their ID is mapped to their unary value
	"""
	ret = {}
	for song in songs:
		ret[song.song_id] = song.unary_factor
	return ret

def makeTransition(inData, outData, inSong, outSong):
	"""
	Takes two arrays of AudioQuantum objects and returns a single AudioData object
	with a linear crossfade and a beatmatch
	"""
	# The number of beats has to be the same
	assert(len(inData) == len(outData))

	# If the tempos are the same then it is easy
	if inSong.bpm == outSong.bpm:
		mixInSeg = audio.getpieces(
			inSong.AudioFile,
			inData
		)
		mixOutSeg = audio.getpieces(
			outSong.AudioFile,
			outData
		)
		mixInSeg.encode("outfiles/Mixinseg.mp3")
		mixOutSeg.encode("outfiles/MixOutseg.mp3")
		transition_length = 60.0/128.0 * MIX_LENGTH 
		transitionSeg = action.Crossfade([mixOutSeg, mixInSeg], [0.0, 0.0], transition_length, mode="exponential").render()
		return transitionSeg

	# Else we iterate over each one
	else:
		transitionTime = 0
		tempoDiff = inSong.bpm - outSong.bpm
		marginalInc = float(tempoDiff) / float(MIX_LENGTH)
		inCollect = []
		outCollect = []
		# Rather than a linear slowdown, it is a step function where each beat slows down by marginalInc
		for i in range(MIX_LENGTH):
			inAudio = inData[i].render()
			outAudio = outData[i].render()
			# We scale the in and out beats so that they are at the same temp
			inScaled = dirac.timeScale(inAudio.data, inSong.bpm / (outSong.bpm + i * marginalInc))
			outScaled = dirac.timeScale(outAudio.data, outSong.bpm / (outSong.bpm + i * marginalInc))
			transitionTime += 60 / (outSong.bpm + i * marginalInc)
			ts = audio.AudioData(ndarray=inScaled, shape=inScaled.shape, 
				sampleRate=inSong.AudioFile.sampleRate, numChannels=inScaled.shape[1])
			ts2 = audio.AudioData(ndarray=outScaled, shape=outScaled.shape, 
				sampleRate=outSong.AudioFile.sampleRate, numChannels=outScaled.shape[1])
			inCollect.append(ts)
			outCollect.append(ts2)
		# Collect the audio and crossfade it
		mixInSeg = audio.assemble(inCollect, numChannels=2)
		mixOutSeg = audio.assemble(outCollect, numChannels=2)
		mixInSeg.encode("outfiles/Mixinseg.mp3")
		mixOutSeg.encode("outfiles/MixOutseg.mp3")
		transitionSeg = action.Crossfade([mixOutSeg, mixInSeg], [0.0, 0.0], transitionTime, mode="exponential").render()
		return transitionSeg

def renderList(songList, outFile):
	"""
	Takes a list of songs and outputs them to outFile
	Has to beatmatch and cross fade
	Assumes songList >= 2
	"""
	mixOutSeg = None
	currAudio = None
	prevSong = None
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
			mixInSeg = currBeats[currSong.mix_in:currSong.mix_in+MIX_LENGTH]
			transitionSeg = makeTransition(mixInSeg, mixOutSeg, currSong, prevSong)
			transitionSeg.encode("outfiles/transition.mp3")
			mainSeg = audio.getpieces(
							currSong.AudioFile,
							currBeats[currSong.mix_in+MIX_LENGTH:currSong.mix_out])
			currAudio = audio.assemble([currAudio, transitionSeg, mainSeg])
		mixOutSeg = currBeats[currSong.mix_out:currSong.mix_out+MIX_LENGTH]
		prevSong = currSong

	# currAudio = audio.assemble([currAudio, mixOutSeg])
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
	# for song1 in songs:
	# 	new_dict = {}
	# 	for song2 in songs:
	# 		# Don't consider songs that differ too greatly 
	# 		if song1 != song2 and abs(song1.bpm - song2.bpm) < 30:
	# 			new_dict[song2] = mashability(song1, song2)
	# 	MASHABILITY_DICT[song1] = new_dict

	from csp import generateMix
	# Use a CSP to solve generate a list of songs
	mixList = generateMix(songs, NUM_SONGS, get_mash_pairs(songs), get_unary_list(songs))

	#print([song.name for song in mixList])
	# Actually render the list to a file
	#renderList(songs, "outfiles/MixOut.mp3")
	renderList(mixList, "outfiles/MixOut.mp3")

if __name__ == "__main__":
	main()


