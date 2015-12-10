from main import Song

# threshold values for unary factor and mashability
# Lower values are stricter cutoffs
MIX_THRESHOLD = 0.07
UNARY_THRESHOLD = 0

# returns the next best song in the domain
def get_best_next_song(mix, domain, mashPairs, unaryVals,v):
	for i in domain[v]:
		# if all constraints satisfied return the next song
		if not(i in mix[:v] or mashPairs[(mix[v-1],i)] > MIX_THRESHOLD or unaryVals[i.song_id] < UNARY_THRESHOLD):
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
		if unaryVals[i.song_id] > factor:
			factor = unaryVals[i.song_id]
			result = i
	return result

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
	

# Given a song id list, all mash pairs, unary vals, and the number
# of mixes to generate, returns the mix with all song ids as a list
def generateMix (songList, numMixes, mashPairs, unaryVals):
	domain = {}
	for i in range(numMixes):
		domain[i] = songList
	mix = [-1 for j in range(numMixes)]
	return backTrack (mix, domain, mashPairs, unaryVals)

