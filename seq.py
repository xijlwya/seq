import mido
import time
import random
import threading
import itertools
import json

from seq_data import *
#imports several note value dicts and CONSTANTS

class NoteList:
	@classmethod
	def _string_to_note(cls, note):
		#helper method
		#expects a note string with chord notes separated by spaces
		#examples: 'c3 e3 g3', 'c1' ,'c#4 d5 gb6', 'd2']
		chord_list = []
		for n in note.split(' '):
			if n:
				note_value = note_names[n[0].lower()]
			else:
				break

			if n[1] == '#' or n[1] == 'b':
				if n[1] == '#':
					note_value += 1
				elif n[1] == 'b':
					note_value -= 1
				note_value += 12*(int(n[2:])-4)
				#-4 because c4 is the middle c, MIDI note 60
			else:
				note_value += 12*(int(n[1:])-4)
			chord_list.append(note_value)
		return tuple(chord_list)

	@classmethod
	def string_to_note(cls, notes):
		if isinstance(notes, list):
			note_list = []
			for string in notes:
				note_list.append(cls._string_to_note(string))
			return note_list
		else:
			return cls._string_to_note(notes)

	@classmethod
	def scale(cls, rootnote, name, octaves=(4,)):
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
		for rom in roman_priolist:
			if degree_w_mod.lower().startswith(rom):
				degree_num = roman_num[rom]
				break
		mod = degree_w_mod[len(rom):]

		resultchord = []
		root = cls.string_to_note(rootnote)

		if mod:
		##TODO: the modifier will overwrite the diatonic chord:
		#if you put in 'VII7' it will always be a major chord with a minor seven
			for semitone in chord_names[mod]:
				resultchord.append(root + semitone)
		else:
			for semitone in scale_chords_abs[scale][degree_num]:
				resultchord.append(root + semitone)
		return tuple(resultchord)


	@classmethod
	def _base_note_string(cls, base_note_str):
		base_note = cls.string_to_note(base_note_str)
		if len(base_note) > 1:
			raise ValueError(base_note_str + ' invalid base note for a scale (probably a chord?)')
		else:
			return base_note[0]

	@classmethod
	def _notes_of_scale(cls, base_note_str, scale):
		base_note = cls._base_note_string(base_note_str)
		scale_notes = scale_names[scale]
		return [base_note + note for note in scale_notes]

	@classmethod
	def _chord_degree(cls, base_note_str, scale, degree):
		base_note = cls._base_note_string(base_note_str)
		deg = roman_num[degree.lower()]
		notes = scale_chords_abs[scale][deg]
		return tuple(base_note + note for note in notes)


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
	"""
	A timer will continuously send MIDI clock messages to its receiver. It
	does so from a daemon thread so it is terminated ungraciously when the
	interpreter exits.

	-	'tempo' is the rate of the clock in bpm. That means that tempo*PPQN
		pulses are sent in one minute
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
	"""
	This is a step sequencer which plays back sequences to a MIDI device. It
	plays those sequences one step at a time, where one step may contain
	multiple notes. All notes of a step will be sent simultaneously which
	allows to play chords.

	The Sequencer needs to receive MIDI clock messages from a clock source.
	Without a clock input, it will not advance.
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
				self.clock_callback()
			elif msg.type == 'sysex':
				self.sysex_callback(msg.data)

	def sysex_callback(self, data):
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

	def clock_callback(self):
		with self._lock:
		#self._lock is inherited from mido.ports.BaseOutput
		#TODO: has all of this to be locked? Can a subset be savely locked?
			if self._pulses == 0:
				self._current_step = self.advance()

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

	def advance(self):
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

	##TODO: set up a sequence property so the new sequence is behaving like the old sequence


class StepSequencer(BaseSequencer):
	def __init__(
		self,
		sequence=[],
		receiver=None,
		division=16,
		channel=1,
		step=1
	):
		super().__init__(sequence,receiver,division,channel,step)

	def _euclid(self, seq_length, num_beats):
		def flatten(l, ltypes=(list, tuple)):
		#from http://rightfootin.blogspot.com/2006/09/more-on-python-flatten.html
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

	def clock_callback(self):
		with self._lock:
		#self._lock is inherited from mido.ports.BaseOutput
		#TODO: has all of this to be locked? Can a subset be savely locked?
			if self._pulses == 0:
				self._current_step = self.advance()

				if isinstance(self._current_step, dict):
					#CAREFUL: json converts all dictionary key/value pairs to strings!
					send_bytes = json.dumps(self._current_step).encode(encoding='ascii')
					msg = mido.Message('sysex', data=send_bytes)
					#receive this with dict = json.dumps(bytes(msg.data))
					self.receiver.send(msg)

				self._pulses += 1

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
	def __init__(self, receiver=None, channel=1):
		super().__init__(
			receiver=receiver,
			division=16,
			channel=channel,
			step=1
		)
		self.rhythm = [True, True, True, False,]
		self.chords = ['cmin','d#maj','gmin']
		self.sequence = self._create_sequence()

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


			note_val = note_names[_root_note[0]]
			if len(_root_note) == 2:
				if _root_note[1] == '#':
					note_val += 1
				elif _root_note[1] == 'b':
					note_val -= 1

			notelist = []

			try:
				chord_semitones = chord_names[_chord_modifier]
			except KeyError:
				chord_semitones = chord_names['maj']

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
				for n in note_names.keys() \
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

			for scale in scale_names.keys():
				for note in note_names.keys():
					for octave in range(1,10):
						for offset in ('','#','b'):
							NoteList.scale(note+offset, scale, octaves=(octave,))

		def test_Sequencer(self):
			def _work(obj):
				for elem in obj.sequence:
					obj.advance()
				obj.advance()
				#this would raise some error if implementation of advance was broken

				obj.start()
				with self.assertRaises(ValueError):
					obj.division = 2**12
				obj.division = 1
				with self.assertRaises(ValueError):
					obj.division = 0
				obj.note_length = 0.1
				obj.note_length = 1.0
				with self.assertRaises(ValueError):
					obj.note_length = 1.01
				with self.assertRaises(ValueError):
					obj.note_length = 0.0
				with self.assertRaises(ValueError):
					obj.note_length = 0.001
				obj.stop()

			baseseq = BaseSequencer(sequence=self.allNotesSequence, receiver=self.port)
			seq = StepSequencer(sequence=self.allNotesSequence, receiver=self.port)
			_work(baseseq)
			_work(seq)

		def test_metaSequencer(self):
			base = BaseSequencer(sequence=[(x,) for x in [60,61,62,63,64,65]], receiver=self.port)
			meta = MetaSequencer(receiver=base, sequence=[{'division':8}], division=1)
			base.start()
			meta.start()
			time.sleep(0.1)
			base.stop()
			meta.stop()
			self.assertTrue(base.division == 8)



	unittest.main(verbosity=2)

	sequence2 = NoteList.string_to_note(['g#4','c5','f4'])

	# output_list = mido.get_output_names()
	# print('Select the target port:')
	# for num, name in enumerate(output_list):
	# 	print('{num}: {name}'.format(num=num, name=name))
	#
	# port = int(input('(seq) '))

	# with mido.open_output(mido.get_output_names()[port]) as port:
	with PrintPort() as port:
		Timer().tempo = 160
		# arp = Arpeggiator(receiver=port)
		seq = StepSequencer(receiver=port)
		seq.sequence = sequence2
		# seq = StepSequencer(receiver=port)
		# seq.division = 16
		# seq.sequence = sequence1.string_to_note()
		seq.start()
		# arp.start()
		time.sleep(1)
		seq.stop()
		#arp.chord = 'dmaj'
		# time.sleep(5)
		#arp.chord = 'd#sus2'
		# time.sleep(5)
		# arp.stop()
	# 	seq1 = Sequencer(sequence=sequence1, receiver=synth)
	# 	seq2 = Sequencer(sequence=sequence2, receiver=synth)
	# 	seq1.start()
	# 	seq2.start()
	# 	time.sleep(5)
		# seq1.stop()
	# 	seq2.stop()
