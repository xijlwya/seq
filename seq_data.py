NOTE_NAMES = {
	'c':60,
	'd':62,
	'e':64,
	'f':65,
	'g':67,
	'a':69,
	'b':71
	}

CHORD_NAMES = {
	'min'		:(0, 3, 7),
	'maj'		:(0, 4, 7),
	'min7'		:(0, 3, 7, 10),
	'7'			:(0, 4, 7, 10),
	'minmaj7'	:(0, 3, 7, 11),
	'maj7'		:(0, 4, 7, 11),
	'dim'		:(0, 3, 6),
	'dim7'		:(0, 3, 6, 9),
	'dimmin7'	:(0, 3, 6, 10),
	'sus2'		:(0, 2, 7),
	'7sus2'		:(0, 2, 7, 10),
	'sus4'		:(0, 5, 7),
	'7sus4'		:(0, 5,	7, 10),
	'6'			:(0, 4, 7, 9),
	'min6'		:(0, 3, 7, 9),
	'b5'		:(0, 4, 6),
	'9'			:(0, 4, 7, 11, 14),
	'min9'		:(0, 3, 7, 10, 14),
	'11'		:(0, 4, 7, 11, 14, 17),
	'min11'		:(0, 3, 7, 10, 14, 17),
	'aug'		:(0, 4, 8),
	'#5'		:(0, 4, 8),
	'augmaj7'	:(0, 4, 8, 11),
	'aug7'		:(0, 4, 8, 10),
}

SCALE_NAMES = {
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

ROMAN_NUM = {
	'i':	0,
	'ii':	1,
	'iii':	2,
	'iv':	3,
	'v':	4,
	'vi':	5,
	'vii':	6,
}

ROMAN_PRIOLIST = ['iii','ii','iv','i','vii','vi','v']

SCALE_CHORDS_REL = {
	'lydian':(
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 6), #dim
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
		(0, 3, 6), #dim
	),
	'mixolydian':(
		(0, 4, 7),
		(0, 3, 7),
		(0, 3, 6), #dim
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
		(0, 3, 6), #dim
		(0, 4, 7),
	),
	'aeolian':(
		(0, 3, 7),
		(0, 3, 6), #dim
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
		(0, 3, 6), #dim
		(0, 4, 7),
		(0, 3, 7),
	),
	'locrian':(
		(0, 3, 6), #dim
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

SCALE_CHORDS_ABS = {
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

# --- CONSTANTS ---
PPQN = 24
