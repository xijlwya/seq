
"""
the code here was used to create those dictionaries of chords
"""
chord_names = {
	'min'		:(0, 3, 7),
	'maj'		:(0, 4, 7),
	'dim'		:(0, 3, 6),
}

scale_names = {
	'lydian'	:(0, 2, 4, 5, 7, 9, 10),
	'ionian'	:(0, 2, 4, 5, 7, 9, 11),
	'mixolydian':(0, 2, 4, 5, 7, 9, 10),
	'dorian'	:(0, 2, 3, 5, 7, 9, 10),
	'aeolian'	:(0, 2, 3, 5, 7, 8, 10),
	'phrygian'	:(0, 1, 3, 5, 7, 8, 10),
	'locrian'	:(0, 1, 3, 5, 6, 8, 10),
	'major'		:(0, 2, 4, 5, 7, 9, 11), #same as ionian
	'minor'		:(0, 2, 3, 5, 7, 8, 10), #same as aeolian
}

scale_chords = {
	'lydian':(
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 6),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 7),
		(0, 4, 7),
	),
	'ionian':(
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 7),
		(0, 4, 7),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 6),
	),
	'mixolydian':(
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 6),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 7),
		(0, 4, 7),
	),
	'dorian':(
		(0, 3, 7),
		(0, 3, 7),
		(0, 4, 7),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 6),
		(0, 4, 7),
	),
	'aeolian':(
		(0, 3, 7),
		(0, 3, 6),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 7),
		(0, 4, 7),
		(0, 4, 7),
	),
	'phrygian':(
		(0, 3, 7),
		(0, 4, 7),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 6),
		(0, 4, 7),
		(0, 3, 7),
	),
	'locrian':(
		(0, 3, 6),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 7),
		(0, 4, 7),
		(0, 4, 7),
		(0, 3, 7),
	),
	'major':(
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 7),
		(0, 4, 7),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 6),
	),
	'minor':(
		(0, 3, 7),
		(0, 3, 6),
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 7),
		(0, 4, 7),
		(0, 4, 7),
	),
}

= {
	'lydian':(
		(0, 4, 7),
		(2, 5, 9),
		(4, 7, 10),
		(0, 5, 9),
		(2, 7, 10),
		(0, 4, 9),
		(2, 5, 10),
	),
	'ionian':(
		(0, 4, 7),
		(2, 5, 9),
		(4, 7, 11),
		(0, 5, 9),
		(2, 7, 11),
		(0, 4, 9),
		(2, 5, 11),
	),
	'mixolydian':(
		(0, 4, 7),
		(2, 5, 9),
		(4, 7, 10),
		(0, 5, 9),
		(2, 7, 10),
		(0, 4, 9),
		(2, 5, 10),
	),
	'dorian':(
		(0, 3, 7),
		(2, 5, 9),
		(3, 7, 10),
		(0, 5, 9),
		(2, 7, 10),
		(0, 3, 9),
		(2, 5, 10),
	),
	'aeolian':(
		(0, 3, 7),
		(2, 5, 8),
		(3, 7, 10),
		(0, 5, 8),
		(2, 7, 10),
		(0, 3, 8),
		(2, 5, 10),
	),
	'phrygian':(
		(0, 3, 7),
		(1, 5, 8),
		(3, 7, 10),
		(0, 5, 8),
		(1, 7, 10),
		(0, 3, 8),
		(1, 5, 10),
	),
	'locrian':(
		(0, 3, 6),
		(1, 5, 8),
		(3, 6, 10),
		(0, 5, 8),
		(1, 6, 10),
		(0, 3, 8),
		(1, 5, 10),
	),
	'major':(
		(0, 4, 7),
		(2, 5, 9),
		(4, 7, 11),
		(0, 5, 9),
		(2, 7, 11),
		(0, 4, 9),
		(2, 5, 11),
	),
	'minor':(
		(0, 3, 7),
		(2, 5, 8),
		(3, 7, 10),
		(0, 5, 8),
		(2, 7, 10),
		(0, 3, 8),
		(2, 5, 10),
	),
}

def _make_scale_chords():
	#this code was used to compute the scale_chords dict
	scale_chords = {}
	for name, scale in scale_names.items():
		work_scale = list(scale)
		for note in scale:
			work_scale.append(note+12)
		chord_list = []
		for i, step in enumerate(work_scale):
			if i <= 6:
				chord = (
					0,
					work_scale[i+2]-work_scale[i],
					work_scale[i+4]-work_scale[i]
				)
				chord_list.append(chord)

		scale_chords[name] = tuple(chord_list)

	return scale_chords

	print('scale_chords = {')
	for key in scale_chords.keys():
		print('\t\''+str(key)+'\':(')
		for chord in scale_chords[key]:
			print('\t\t'+str(chord)+',')
		print('\t),')
	print('}')

def _make_absolute_chords():
	abs_chords = {}
	for name, chords in scale_chords.items():
		#'lydian', 	[(0, 4, 7), (0, 3, 7),(0, 3, 6),(0, 4, 7),(0, 3, 7),(0, 3, 7),(0, 4, 7),]
		chord_list = []
		for i, note in enumerate(scale_names[name]):
			#(0, 2, 4, 5, 7, 9, 10),
			chord = chords[i]
			#(0, 4, 7)
			abs_chord = []
			for semitone in chord:
				#0
				abs_chord.append((note+semitone)%12)
			chord_list.append(tuple(sorted(abs_chord)))
		abs_chords[name] = tuple(chord_list)

	return abs_chords

def _print_dict(d):
	print(' = {')
	for key in d.keys():
		print('\t\''+str(key)+'\':(')
		for chord in d[key]:
			print('\t\t'+str(chord)+',')
		print('\t),')
	print('}')

_print_dict(_make_absolute_chords())
