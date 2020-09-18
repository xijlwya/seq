import mido
import time
import random
import threading
import itertools
import json

from seq_data import *
#imports several note value dicts and CONSTANTS

class NoteList:
	'''a helper class to deal with sequences that represent musical notes

	This class provides classmethods to operate on lists of musical notes. It is
	bascially just a namespace and instantiating objects from it is depreciated.

	Methods
	¯¯¯¯¯¯¯
	@classmethod
	string_to_note(notes)
		converts strings like "a1" "b#4 bb2" to MIDI note values and returns a
		tuple containing the associated values

	@classmethod
	scale(rootnote, name, octaves=(4,))
		returns the notes of a scale with a given root note within the given
		octaves

	@classmethod
	chord(rootnote, scale, degree_w_mod)
		returns the chord corresponding to a degree in a scale with a given
		root note

	'''

	@classmethod
	def _string_to_note(cls, note):
		#helper method
		#expects a note string with chord notes separated by spaces
		#examples: 'c3 e3 g3', 'c1' ,'c#4 d5 gb6', 'd2'
		chord_list = []
		for n in note.split(' '):
			if n:
				note_value = NOTE_NAMES[n[0].lower()]
			else:
				break

			if len(n) > 2 and (n[1] == '#' or n[1] == 'b'):
				if n[1] == '#':
					note_value += 1
				elif n[1] == 'b':
					note_value -= 1
				note_value += 12*(int(n[2:])-4)
				#-4 because c4 is the middle c, MIDI note 60, see seq_data dicts
			elif len(n) == 2:
				note_value += 12*(int(n[1:])-4)
			chord_list.append(note_value)
		return tuple(chord_list)

	@classmethod
	def string_to_note(cls, notes):
		'''returns an integer or a list of interger tuples representing MIDI
		note values

		This method will determine whether it receives a list of strings or a
		single string and then proceed to translate those strings to musical
		notes

		Parameters
		¯¯¯¯¯¯¯¯¯¯
		notes: str or list
			either a single string denoting a musical note such as "a4" or "b#5"
			or a list of such strings
			in a list, multiple notes separated by spaces are used to denote
			chords, e.g. ["a4", "a4 c5 e5", "ab4", "a4 cb5 e5"]

		'''

		if isinstance(notes, list):
			note_list = []
			for string in notes:
				note_list.append(cls._string_to_note(string))
			return note_list #returns a list of tuples
		else:
			return cls._string_to_note(notes) #returns a tuple

	@classmethod
	def scale(cls, rootnote, name, octaves=(4,)):
		'''returns the notes of a scale with a given root note within the given
		octaves

		Example use: scale('g', 'lydian') would give all notes of g lydian
		above (and including) g4

		The notes are provided from lowest to highest within each octave

		Parameters
		¯¯¯¯¯¯¯¯¯¯
		rootnote: string
			the root note of the scale as a string but without an octave
			indicator, e.g. 'a#'

		name: string
			one of these names: 'lydian', 'ionian', 'mixolydian', 'dorian',
			'aeolian', 'phrygian', 'locrian', 'major', 'minor'
			there may be more in the future, see seq_data SCALE_NAMES dict

		octaves: iter
			an iterable providing integers between 0 and 9
			the sequence of integers is the sequence of octaves in the output
			sequence, e.g. [4,4,5,5] will output the fourth octave twice,
			followed by the fifth octave twice, all within a single list

		'''

		#this method will read octaves as an iterator, allowing for custom
		#sequences of octaves such as (4,5,4,3)
		base_notes = []
		octaves = list(octaves)
		#so the user can input e.g. octaves=3 to obtain a single octave
		for oct in octaves:
			base_notes.append(rootnote.lower() + str(oct))
		notes = []
		for root in base_notes:
			for note in cls._notes_of_scale(root, name.lower()):
				notes.append(note)
		return notes

	@classmethod
	def chord(cls, rootnote, scale, degree_w_mod):
		'''returns the notes of a chord degree of a given scale over a given
		root note

		The root note and scale are the same as in the scale function. The
		degree is supposed to be given as a roman numeral ranging from I to VII
		and a modifier can be added to that optionally, e.g. I7 or VIdim


		Parameters
		¯¯¯¯¯¯¯¯¯¯
		rootnote: string
			the root note of the scale as a string but without an octave
			indicator, e.g. 'a#'

		name: string
			one of these names: 'lydian', 'ionian', 'mixolydian', 'dorian',
			'aeolian', 'phrygian', 'locrian', 'major', 'minor'
			there may be more in the future, see seq_data SCALE_NAMES dict

		degree_w_mod: string
			a string consisting of a roman numeral and a chord modifier
			the numerals are lowercased internally, so the case does not matter
			the modifiers can be obtained from seq_data CHORD_NAMES dict
			e.g. 'vi7sus4'
		'''

		if not degree_w_mod.startswith(ROMAN_PRIO):
			raise ValueError(
				'"{deg}" is no applicable'
				' chord number'.format(deg=degree_w_mod))
		else:
			for rom in ROMAN_PRIO:
				if degree_w_mod.lower().startswith(rom):
					degree_num = ROMAN_NUM[rom]
					break
			mod = degree_w_mod[len(rom):].lower()

			resultchord = []
			root = cls.string_to_note(rootnote)[0]

			if mod:
			##TODO: the modifier will overwrite the diatonic chord:
			#if you put in 'VII7' it will always be a major chord with a minor
			#seven
				for semitone in CHORD_NAMES[mod]:
					resultchord.append(root + semitone)
			else:
				for semitone in SCALE_CHORDS_ABS[scale][degree_num]:
					resultchord.append(root + semitone)
			return tuple(resultchord)


	@classmethod
	def _base_note_string(cls, base_note_str):
		base_note = cls.string_to_note(base_note_str)
		if len(base_note) > 1:
			raise ValueError(
				base_note_str + \
				' invalid base note for a scale (probably a chord?)'
			)
		else:
			return base_note[0]

	@classmethod
	def _notes_of_scale(cls, base_note_str, scale):
		base_note = cls._base_note_string(base_note_str)
		scale_notes = SCALE_NAMES[scale]
		return [base_note + note for note in scale_notes]

	@classmethod
	def _chord_degree(cls, base_note_str, scale, degree):
		base_note = cls._base_note_string(base_note_str)
		deg = ROMAN_NUM[degree.lower()]
		notes = SCALE_CHORDS_ABS[scale][deg]
		return tuple(base_note + note for note in notes)

	@classmethod
	def tuplify(cls, seq):
		#convenience to provide sequences of ints like [60,64,60,67]
		for n, elem in enumerate(seq):
			if isinstance(elem, int):
				seq[n] = (elem, )


class Singleton(type):
	#copied from
	#https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = \
				super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]


class Timer(metaclass=Singleton):
	"""A timer that will regularily send MIDI clock messages

	A timer will continuously send MIDI clock messages to its receiver. It
	does so from a daemon thread so it is terminated ungraciously when the
	interpreter exits.

	The timer class is a singleton and it is accessed via Timer().

	Attributes
	¯¯¯¯¯¯¯¯¯¯
	tempo: int
		is the rate of the clock in bpm. That means that tempo*PPQN pulses are
		sent in one minute
		PPQN (abbr. for "pulses per quarter note") is a constant from
		seq_data.py

	Methods
	¯¯¯¯¯¯¯
	add_receiver(rec): mido.ports.BaseOutput
		adds rec to the list of ports that will receive MIDI clock messages from
		the timer

	remove_reciver(rec): mido.ports.BaseOutput
		removes rec from the list of receivers
		this will raise ValueError if rec is not in the list of receivers

	"""

	def __init__(self, tempo=120):
		self._running = False
		self.tempo = tempo
		self.receivers = []
		self._lock = threading.Lock()
		self.start()

	def _start(self):
		self._running = True
		delta_t = 0
		while self._running:
			t0 = time.perf_counter()
			if delta_t >= self._pulse_length:
				with self._lock:
					for r in self.receivers:
						try:
							r.send(mido.Message('clock'))
						except ValueError:
							self.receivers.remove(r)
							if len(self.receivers) == 0:
								self._running = False
				delta_t = 0
			delta_t += time.perf_counter() - t0

	def start(self):
		threading.Thread(target=self._start, daemon=True).start()

	@property
	def tempo(self):
		return self._tempo

	@tempo.setter
	def tempo(self, val):
		if 10 < val < 1000:
			self._tempo = val
			self._pulse_length = 60/(self.tempo*PPQN)
		else:
			raise ValueError('tempo out of bounds.')

	def add_receiver(self, rec):
		self.receivers.append(rec)

	def remove_receiver(self, rec):
		self.receivers.remove(rec)


class BaseSequencer(mido.ports.BaseOutput):
	"""A basic step sequencer which sends MIDI note messages

	This is a step sequencer which plays back sequences to a MIDI device. It
	plays those sequences one step at a time, where one step may contain
	multiple notes. All notes of a step will be sent simultaneously which
	allows to play chords.

	The Sequencer needs to receive MIDI clock messages from a clock source.
	Without a clock input, it will not advance. The clock defaults to the
	Timer class provided by the seq module.

	Attributes
	¯¯¯¯¯¯¯¯¯¯
	receiver: mido.ports.BaseOutput
		the receiver will receive the MIDI messages generated by the sequencer

	sequence: list
		a list of tuples which contain MIDI note numbers
		e.g. [(60,), (60, 62), (62,), (62, 64)]
		this will convert non-tuple intergers to 1-tuples so that [60,62]
		becomes [(60, ), (62, )] internally

	step: int
		an integer indicating how many steps the sequencer advances through the
		sequence at a time
		this may be negative and can be larger than the sequence length

	division: int
		an integer indicating how quickly the sequencer advances in regard to
		the clock
		a division of 16 indicates that the sequencer will advance 16 steps in
		a full measure (i.e. four quarter pulses)

	channel: int
		the MIDI channel the sequencer will be sending messages on
		possible values range from 1 to 16

	note_length: float
		a float that indicates how long it takes for a step to send a note off
		message, this is a relative value where 1.0 indicates a whole step and
		e.g. 0.5 half of a step
		values are restricted to 0.0 < note_length <= 1.0

	Methods
	¯¯¯¯¯¯¯
	@classmethod
	note_to_midi(notes, msg_type='note_on', channel=1, velocity=127)
		takes tuple of MIDI note values (i.e. integers between 0 and 127) and
		returns a list of corresponding note on messages

	stop()
		stops the sequencer and sends a "stop all sounds" message to the
		receiving device
		after calling this, the sequencer will not react to MIDI clock messages

	start()
		starts the sequencer
		after calling this, the sequencer will react to MIDI clock messages by
		sending MIDI note messages

	"""

	def __init__(
		self,
		sequence=[],
		receiver=None,
		division=16,
		channel=1,
		step=1
	):
		super().__init__()
		#for inheriting from BaseOutput
		#with this, self._lock (threading.Lock object) is available

		self._running = False
		self._pulses = 0
		self._cursor = 0
		Timer().add_receiver(self)
		#set up the sequencer to receive clock messages from the Timer

		self.receiver = receiver
		#receiver is supposed to be a mido port with a send(msg) method

		self.sequence = sequence
		self.step = step

		self.division = division
		#the musical note division,
		#e.g. 16 means 16th-notes; i.e. notes per measure

		self.channel = channel
		#MIDI channel the sequencer sends on

		self.note_length = 0.5
		#note length is the relative time a note takes of one step

	def _send(self, msg):
		#inherited from mido.ports.Baseport
		#here the Sequencer receives MIDI messages
		if self._running:
			if msg.type == 'clock':
				self._clock_callback()
			elif msg.type == 'sysex':
				self._sysex_callback(msg.data)

	def _sysex_callback(self, data):
		with self._lock:
			sent_dict = json.loads(bytes(data))
			for att, val in sent_dict.items():
				if hasattr(self, att):
					setattr(self, att, val)

	@classmethod
	def note_to_midi(cls, notes, msg_type='note_on', channel=1, velocity=127):
		"""
		Converts tuples of integers to a list of mido.Message
		"""
		message_list = []

		if notes:
		#note_to_midi receives notes=None or empty tuple
		#when a sequence skips a beat or is empty
			for note in notes:
				message_list.append(
					mido.Message(
						msg_type,
						note=note,
						channel=channel,
						velocity=velocity
					)
				)

		return message_list

	def _clock_callback(self):
		with self._lock:
		#self._lock is inherited from mido.ports.BaseOutput
		#TODO: has all of this to be locked? Can a subset be savely locked?
			if self._pulses == 0:
				self._current_step = self._advance()

				for note in self.note_to_midi(
					self._current_step,
					channel=self.channel
				):
					self.receiver.send(note)

				self._pulses += 1

			elif self._pulses == round(self._pulse_limit*self.note_length):
				for note in self.note_to_midi(
					self._current_step,
					msg_type='note_off',
					channel=self.channel
				):
					self.receiver.send(note)
				self._pulses = 0

			else:
				self._pulses += 1

	def stop(self):
		self._running = False
		self.receiver.reset()
		#mido method to send MIDI all note offs to port

	def start(self):
		self._running = True

	def _advance(self):
		if len(self.sequence) > 0:
			current = self.sequence[self._cursor]
			self._cursor += self.step
			self._cursor = self._cursor % len(self.sequence)
			return current

	@property
	def division(self):
		return self._division

	@division.setter
	def division(self, val):
		if 0 < val and round(PPQN*4/val) > 0:
			#TODO is this check sane??
			self._division = val
			self._pulse_limit = round(PPQN*4/self.division)
		else:
			raise ValueError('Note division out of bounds')

	@property
	def note_length(self):
		return self._note_length

	@note_length.setter
	def note_length(self, val):
		if 0 <= val <= 1.0 and round(self._pulse_limit*val) > 0:
			self._note_length = val
		else:
			raise ValueError('Invalid note length: '+str(val))

	@property
	def sequence(self):
		return self._sequence

	@sequence.setter
	def sequence(self, seq):
		if self._cursor >= len(seq):
			self._cursor = 0
		self._sequence = seq


class Arpeggiquencer(BaseSequencer):
	def __init__(
		self,
		sequence=['i','iii','v','vi'],
		receiver=None,
		division=16,
		channel=1,
		seq_length=16,
		num_beats=7,
		rootnote='a',
		scale='minor'
	):
		self._scale = scale
		#hack to make _reset_sequence() work in
		#rootnote.setter and scale.setter
		self._rootnote = rootnote #hack as above
		self.seq_length = seq_length
		self.num_beats = num_beats
		super().__init__([],receiver,division,channel,step=1)
		self.scale = scale #calls scale.setter
		self.rootnote = rootnote #calls rootnote.setter
		self.sequence = sequence

		"""
		How this will work in the future:

		class Arpeggiquencer
			has a notepool, containing all notes to generate patterns
			from
			a notepool may be a scale if chosen so, but has to be user generated
			then

			has an octave setting that determines which range of +-12 semitone
			transpositions can occur on the notepool

			has a rhythm, dictating what rhythm to play the notes in
			rhythm may be euclidian if chosen so

			has parts which consist of a notepool, rhythm and length
			length determines after how many steps the next part is queued
			each default to the previous part's values

			['i','v','i','vii'] is a shorthand for four parts, all with the same
			rhythm and length, but note pools according to the chord symbols

			['i7','vsus2','i','vii9'] should be possible too

			['cmin', 'gmin', 'cmin', 'bbmaj'] should be possible too

			if the user only specifies chords, the rhythm should still be
			changable, influencing the rhythm of all parts

			this should be the only class available to the user in here
			essentially dropping Arpeggiator

		"""

	@property
	def sequence(self):
		return self._sequence

	@sequence.setter
	def sequence(self, val):

		super(__class__, self.__class__).sequence.__set__(self, val)
		#see https://bugs.python.org/issue14965

		#TODO: somehow this calls the getter of BaseSequencer.sequence when
		#setting up the object via BaseSequencer.__init__
		#so BaseSequencer.__init__ accesses self.sequencer which is redeirected
		#here, because it wants to set up the initial sequence then, this super
		#call somehow arrives in BaseSequencer.sequence(self) which is the
		#getter

		self._reset_sequence()

	def _reset_sequence(self):
		rhythm = self._euclid(self.seq_length, self.num_beats)

		self._internal_sequence = []
		for chord in self.sequence:
			cur = 0
			chord_notes = NoteList.chord(self.rootnote, self.scale, chord)
			for beat in rhythm:
				if beat:
					self._internal_sequence.append(chord_notes[cur])
					cur += 1
					cur = cur % len(chord_notes)
				else:
					self._internal_sequence.append(None)

		self._cursor = 0

	def _advance(self):
		if len(self._internal_sequence) > 0:
			current = self._internal_sequence[self._cursor]
			self._cursor += self.step
			self._cursor = self._cursor % len(self._internal_sequence)
			return current

	@property
	def scale(self):
		return self._scale

	@scale.setter
	def scale(self, val):
		if val in SCALE_NAMES.keys():
			if self._scale != val:
				self._scale = val
				self._reset_sequence()
		else:
			raise KeyError(val + ' is not a valid scale name')

	@property
	def rootnote(self):
		return self._rootnote

	@rootnote.setter
	def rootnote(self, val):
		if 		(len(val) == 2 \
					and val[0] in NOTE_NAMES.keys()\
					and val[1] in ['#', 'b'])\
				or (len(val) == 1\
					and val[0] in NOTE_NAMES.keys()\
		):
			if self._rootnote != val:
				self._rootnote = val
				self._reset_sequence()
		else:
			raise ValueError(val + ' is no viable root note')

	@property
	def num_beats(self):
		return self._num_beats

	@num_beats.setter
	def num_beats(self, val):
		if 0 < val < self.seq_length:
			self._num_beats = val
		else:
			raise ValueError('{a} number of beats is not'\
				' within bounds 0 < num < {b}'.format(a=val, b=self.seq_length))

	@classmethod
	def _euclid(cls, seq_length, num_beats):
		'''
		This returns a euclidian rhythm of length seq_length with num_beats
		beats.
		'''
		def flatten(l, ltypes=(list, tuple)):
			#this flattens nested tuples and lists quite effectively
			#from http://rightfootin.blogspot.com/
			#		2006/09/more-on-python-flatten.html
			ltype = type(l)
			l = list(l)
			i = 0
			while i < len(l):
				while isinstance(l[i], ltypes):
					if not l[i]:
						l.pop(i)
						i -= 1
						break
					else:
						l[i:i + 1] = l[i]
				i += 1
			return ltype(l)

		#------
		#the following implements Bjorklund's algorithm to obtain a euclidian
		#rhythm with n beats in a sequence of length s
		#see http://cgm.cs.mcgill.ca/~godfried/publications/banff.pdf
		l = [1]*num_beats
		r = [0]*(seq_length - num_beats)

		while len(r) > 1:
			new_l = []
			new_r = []

			for tup in itertools.zip_longest(l, r, fillvalue=None):
				if None in tup:
					val = list(tup)
					val.remove(None)
					new_r.append(val)
				else:
					new_l.append(list(tup))

			l = new_l
			r = new_r

		return flatten(l+r)

	@classmethod
	def list_euclidian_sequences(cls, seq_length, num_beats):
		#returns a list of all euclidian sequences of length seq_length with
		#num_beats beats that start with a beat
		def math_euclid(a,b):
			#iterative implementation of Euclid's algorithm
			#see https://en.wikipedia.org/wiki/
			#		Euclidean_algorithm#Implementations
			while b != 0:
				a, b = b, a % b
			return a

		def shift(seq):
			#shifts a sequence cyclically to the left until it starts with a 1
			#generator yields all possible shifts
			for n, e in enumerate(seq):
				if e == 1:
					if n == 0:
						yield seq
					else:
						yield seq[n:] + seq[0:n]

		euc = self._euclid(seq_length, num_beats)
		math_euc = math_euclid(seq_length, num_beats)

		l = []
		for s in shift(euc):
			l.append(s)
		num = len(l) #number of all shifts

		#all sequences after num//math_euc are repetitions of the ones before
		#proof pending
		return l[:num//math_euc]


class MetaSequencer(BaseSequencer):
	def __init__(
		self,
		sequence=[],
		receiver=None,
		division=16,
		channel=1,
		step=1
	):
		super().__init__(sequence,receiver,division,channel,step)

	@classmethod
	def note_to_midi(cls, notes):
		#overwritten from BaseSequencer
		#meta sequencer doesn't deal with musical note values
		raise NotImplementedError

	def _clock_callback(self):
		with self._lock:
		#self._lock is inherited from mido.ports.BaseOutput
		#TODO: has all of this to be locked? Can a subset be savely locked?
			if self._pulses == 0:
				self._current_step = self._advance()

				if isinstance(self._current_step, dict):
					send_bytes = \
						json.dumps(self._current_step).encode(encoding='ascii')
					msg = mido.Message('sysex', data=send_bytes)
					#receive this with dict = json.dumps(bytes(msg.data))
					self.receiver.send(msg)

				self._pulses += 1
			elif self._pulses == self._pulse_limit:
				self.pulses = 0
			else:
				self._pulses += 1


class SequencerGroup(BaseSequencer):
	def __init__(
		self,
		sequence=[],
		receiver=None,
		division=16,
		channel=1,
		step=1
	):
		super().__init__(sequencer,	receiver, division,	channel, step)
		Timer().remove_receiver(self)
		self._group = []

	def append(self, seq):
		self._group.append(seq)


class Arpeggiator(BaseSequencer):
	def __init__(
		self,
		receiver=None,
		division=16,
		channel=1
	):
		super().__init__(
			receiver,
			division,
			channel,
			sequence=self._create_sequence(),
			step=1
		)

		self.rhythm = [1,1,1,0]
		self.chords = ['cmin','d#maj','gmin']

	@property
	def chords(self):
		return self._chords

	@chords.setter
	def chords(self, chords):
		self._chords = chords
		self.sequence = self._create_sequence()

	def _create_sequence(self):
		#translates the chord to notes like 'c#'', 'd', etc.'

		arp_seq = []
		for chord in self.chords:
			if chord[1] == '#' or chord[1] == 'b':
				_root_note = chord[:2].lower()
				_chord_modifier = chord[2:].lower()
			else:
				_root_note = chord[:1].lower()
				_chord_modifier = chord[1:].lower()


			note_val = NOTE_NAMES[_root_note[0]]
			if len(_root_note) == 2:
				if _root_note[1] == '#':
					note_val += 1
				elif _root_note[1] == 'b':
					note_val -= 1

			notelist = []

			try:
				chord_semitones = CHORD_NAMES[_chord_modifier]
			except KeyError:
				chord_semitones = CHORD_NAMES['maj']

			for semitones in chord_semitones:
				notelist.append(note_val + semitones)

			notelist.reverse()
			#for FIFO access

			for beat in self.rhythm:
				cursor = 0
				if beat:
					#if the sequence of beats contains more beats than the
					#sequence of notes contains notes, the sequence of notes
					#will be inserted repeatedly
					arp_seq.append((notelist[cursor],))
					cursor += 1
					cursor = cursor % len(notelist)
				else:
					arp_seq.append(tuple())

		return arp_seq


if __name__ == '__main__':
	import unittest

	class SeqTest(unittest.TestCase):
		class Port(mido.ports.BaseOutput):
			def __init__(self):
				super().__init__()
			def _send(self, msg):
				pass

		def setUp(self):
			self.port = self.Port()
			self.allNotesSequence = [ \
				n+ex+str(num) \
				for n in NOTE_NAMES.keys() \
				for ex in ['','#','b'] \
				for num in range(1,11) \
			]
			self.allChordsSequence = [
				x + ' ' + y + ' ' + z + ' ' \
				for x in self.allNotesSequence[0:26] \
				for y in self.allNotesSequence[0:26] \
				for z in self.allNotesSequence[0:26] \
			]

		def tearDown(self):
			self.port.close()

		def test_NoteList(self):
			def checkElements(seq):
				seq = NoteList.string_to_note(seq)
				for elem in seq:
					self.assertIsInstance(elem, tuple)
					for note in elem:
						self.assertIsInstance(note, int)

			checkElements(self.allNotesSequence)
			checkElements(self.allChordsSequence)
			seq = ['this', 'is', 'a', 'test']
			with self.assertRaises(KeyError):
				NoteList.string_to_note(seq)
			seq = [None]
			with self.assertRaises(AttributeError):
				NoteList.string_to_note(seq)
			seq = [12]
			with self.assertRaises(AttributeError):
				NoteList.string_to_note(seq)

			for scale in SCALE_NAMES.keys():
				for note in NOTE_NAMES.keys():
					for octave in range(1,10):
						for offset in ('','#','b'):
							NoteList.scale(
								note+offset,
								scale,
								octaves=(octave,)
							)

		def test_BaseSequencer(self):
			baseseq = BaseSequencer(
				sequence=self.allNotesSequence,
				receiver=self.port
			)
			for elem in baseseq.sequence:
				baseseq._advance()
			baseseq._advance()
			#this would raise some error if implementation of advance was broken

			baseseq.start()
			with self.assertRaises(ValueError):
				baseseq.division = 2**12
			baseseq.division = 1
			with self.assertRaises(ValueError):
				baseseq.division = 0
			baseseq.note_length = 0.1
			baseseq.note_length = 1.0
			with self.assertRaises(ValueError):
				baseseq.note_length = 1.01
			with self.assertRaises(ValueError):
				baseseq.note_length = 0.0
			with self.assertRaises(ValueError):
				baseseq.note_length = 0.001
			baseseq.stop()

		def test_MetaSequencer(self):
			base = BaseSequencer(
				sequence=[(x,) for x in [60,61,62,63,64,65]],
				receiver=self.port
			)
			metaseq = [
				{'division':8, 'note_length':0.3, 'channel':2},
				{'division':12, 'note_length':0.7, 'channel':12}
			]
			meta = MetaSequencer(receiver=base, sequence=metaseq, division=1)
			Timer().remove_receiver(meta)
			Timer().remove_receiver(base)
			meta.start()
			base.start()
			meta._clock_callback()
			self.assertTrue(base.division == 8)
			self.assertTrue(base.note_length == 0.3)
			self.assertTrue(base.channel == 2)
			meta._pulses = 0
			meta._clock_callback()
			self.assertTrue(base.division == 12)
			self.assertTrue(base.note_length == 0.7)
			self.assertTrue(base.channel == 12)
			meta.stop()
			base.stop()

		def test_Arpeggiquencer(self):
			euseq = Arpeggiquencer(receiver=self.port)
			with self.assertRaises(ValueError):
				euseq.sequence = ['a']

	unittest.main(verbosity=2)
