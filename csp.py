from main import Song

def genMix(songList, mashabilityDict):
	"""
	Generates a good mix using both unary and binary constraints
	ARGS:
		songList-> A list of song objects (see main.py)
		mashabilityDict-> A dict of dicts. song1 to song2 is mashabilityDict[song1][song2]
	RET: 
		A list of songs to be played in that order
	"""

	# Right now just return all songs in order
	return songList