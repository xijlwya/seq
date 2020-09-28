import mido
import time
import random
import threading
import itertools
import json
import re

from seq_data import *
#imports several note value dicts and constants, all ALLCAPS

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


class Sequencer(mido.ports.BaseOutput):
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
		sequence='',
		note_pool=[],
		receiver=None,
		division=16,
		channel=1,
		step=1,
		name=None
	):
		super().__init__(name=name)
		#for inheriting from BaseOutput
		#with this, self._lock (threading.Lock object) is available

		self._running = False
		self._pulses = 0
		self._rhythm_cursor = 0
		self._note_cursor = 0
		Timer().add_receiver(self)
		#set up the sequencer to receive clock messages from the Timer

		self.receiver = receiver
		#receiver is supposed to be a mido port with a send(msg) method

		self.regex = re.compile(r'(-|xo*)*')
		#regular expression to check sequence strings
		# ( ... )*	-> 0 or more
		# (A | B)	-> A or B
		# -			-> match '-'
		# xo*		-> match 'x' followed by 0 or more 'o'

		self.sequence = sequence
		self.note_pool = note_pool
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
		self._rhythm_cursor = 0
		self._note_cursor = 0
		self._pulses = 0

	def _advance(self):
		if len(self.sequence) > 0:
			current = self.sequence[self._rhythm_cursor]
			self._rhythm_cursor += self.step
			self._rhythm_cursor = self._rhythm_cursor % len(self.sequence)
			if current == 'x':
				self._note_cursor += self.step
				self._note_cursor = self._note_cursor % len(self.note_pool)
				return self.note_pool[self._note_cursor]
			elif current == 'o':
				pass #TODO implement a tie note
			else: #current == '-'
				pass

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
		check = self.regex.fullmatch(seq) #see __init__ for regex
		if check:
			self._sequence = seq
			if self._rhythm_cursor >= len(seq):
				self._rhythm_cursor = 0
		else:
			raise ValueError('Invalid sequence string {s}'.format(s=s))

	@property
	def note_pool(self):
		return self._note_pool

	@note_pool.setter
	def note_pool(self, pool):
		self._note_pool = pool
		if self._note_cursor >= len(pool):
			self._note_cursor = 0

	@property
	def channel(self):
		return self._channel

	@channel.setter
	def channel(self, ch):
		if 0 <= ch <= 15:
			self._channel = int(ch)
		else:
			raise ValueError('invalid channel {ch}'.format(ch=ch))

	def __str__(self):
		return '{name}@channel {ch}'.format(name=self.name, ch=self.channel)


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

		def test_Sequencer(self):
			seq = Sequencer(
				sequence='x',
				note_pool=self.allNotesSequence,
				receiver=self.port
			)
			for elem in seq.sequence:
				seq._advance()
			seq._advance()
			#this would raise some error if implementation of advance was broken

			seq.start()
			with self.assertRaises(ValueError):
				seq.division = 2**12
			seq.division = 1
			with self.assertRaises(ValueError):
				seq.division = 0
			seq.note_length = 0.1
			seq.note_length = 1.0
			with self.assertRaises(ValueError):
				seq.note_length = 1.01
			with self.assertRaises(ValueError):
				seq.note_length = 0.0
			with self.assertRaises(ValueError):
				seq.note_length = 0.001
			seq.stop()

	unittest.main(verbosity=2)
