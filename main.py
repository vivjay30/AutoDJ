import echonest.remix.audio as audio
import echonest.remix.action as action
import echonest.remix.modify as modify
import dirac
import json
import itertools

# minimum threshold value for unary factor and mashability
THRESHOLD = 0.2

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
		
def get_mash_pairs(N_list):
    mash_dict = {}
    all_pairs = list(itertools.combinations(N_list, 2))
    for song_pair in all_pairs:
        rand_mash = mashability(song_pair[0], song_pair[1])
        mash_dict[song_pair] = rand_mash
        mash_dict[(song_pair[1],song_pair[0])] = rand_mash
    return mash_dict


# takes a list of two song id and returns a number between zero and 1
def mashability (song1_id, song2_id):
    return round(random.random(),2)

    
def get_unary_list(N):
    return [mashability(1, 2) for i in range(N)]

# returns the next best song in the domain
def get_best_next_song(mix, domain, mashPairs, unaryVals,v):
    for i in domain[v]:
            
        # if all constraints satisfied return the next song
        if not(i in mix[:v] or mashPairs[(mix[v-1],i)] < THRESHOLD or unaryVals[i] < THRESHOLD):
            return i
    return -1

# pick the next unassigned variable
def pickUnassignedVariable(mix):
    for i in range(0, len(mix)):
        if mix[i] == -1:
            return i

# pick the first best song in the mix
def pickFirstSong(domain, unaryVals):
    factor = float("-inf")
    result = 0
    for i in domain[0]:
         if unaryVals[i] > factor:
             factor = unaryVals[i]
             result = i
    return result
    

# Given a song id list, all mash pairs, unary vals, and the number
# of mixes to generate, returns the mix with all song ids as a list
def generateMix (songList, numMixes, mashPairs, unaryVals):
    domain = {}
    for i in range(numMixes):
        domain[i] = songList
    mix = [-1 for j in range(numMixes)]
    return backTrack (mix, domain, mashPairs, unaryVals)



#backtracking algorithm with forward searching for our csp
def backTrack (mix, domain, mashPairs, unaryVals):
    # all slots have been assigned with song ids
    if mix[len(mix) - 1] != -1:
        return mix

    else:
        # pick the next unassigned variable
        v = pickUnassignedVariable(mix)

        #no possible assignments
        if len(domain[v]) == 0: 
            return False

        # put the best song in the first slot and backtrack           
        if v == 0:
            mix[v] = pickFirstSong(domain, unaryVals)
            return backTrack(mix, domain, mashPairs, unaryVals)
            
        # get the next best song given the current assignment           
        i = get_best_next_song(mix, domain, mashPairs, unaryVals, v)

        #if no value meets constraint
        if i == -1:
            # prune the domain to not have the previous song
            new_domain = domain[v-1][:]
            new_domain.remove(mix[v-1])
            domain[v-1] = new_domain

            # backtrack on the same variable with the updated
            # domain
            mix[v-1] = -1
            return backTrack(mix, domain, mashPairs, unaryVals)
        else:
            # assign a song id to the slot and backtrack
            mix[v] = i
            return backTrack(mix, domain, mashPairs, unaryVals)

    return False
 


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

	#from csp import genMix
	# Use a CSP to solve generate a list of songs
	#mixList = genMix(songs, MASHABILITY_DICT)

	# Actually render the list to a file
	renderList(mixList, "MixOut.mp3")

if __name__ == "__main__":
    main()


