import echonest.remix.audio as audio
import echonest.remix.action as action
import echonest.remix.modify as modify
import dirac
from pyechonest import config
config.ECHO_NEST_API_KEY = "O63DZS2LNNEWUO9GC"

#reload(audio)
audio_file = audio.LocalAudioFile("mp3/Calibria.mp3")

beats = audio_file.analysis.beats[128:159]


collect = []
for beat in beats:
	beat_audio = beat.render()
	scaled_beat = dirac.timeScale(beat_audio.data, 1.2)
	ts = audio.AudioData(ndarray=scaled_beat, shape=scaled_beat.shape, 
                sampleRate=audio_file.sampleRate, numChannels=scaled_beat.shape[1])
	collect.append(ts)
print collect
out = audio.assemble(collect, numChannels=2)


# audio_file2 = audio.LocalAudioFile("mp3/Bastille.mp3")
# beats2 = audio_file2.analysis.beats[128:159]


# data1 = audio.getpieces(audio_file, beats)
# # print type(data1)
# # print isinstance(data1, audio.AudioData)
# #out = modify.Modify().shiftTempo(data1, 1)
# data2 = audio.getpieces(audio_file2, beats2)
# out = action.Crossfade([data1, data2], [0.0, 0.0], 30).render()


# data1.encode("Testing1.mp3")
# data2.encode("Testing2.mp3")
# out = audio.mix(data1, data2)
# out.encode("Mixed.mp3")
out.encode("outfiles/Mixed.mp3")