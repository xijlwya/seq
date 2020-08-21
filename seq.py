import mido
import time
import random
import collections.abc
import threading

note_names = {
	'c':60,
	'd':62,
	'e':64,
	'f':65,
	'g':67,
	'a':69,
	'b':71
	}

chord_names = {
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

scale_chords_rel = {
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

scale_chords_abs = {
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

PPQN = 24


class Sequence(collections.abc.MutableSequence):
	"""
	A sequence is a ring list which can be traversed by iterating over it. This
	iteration does not terminate and the contents of the list are returned
	repeatedly.

	The sequence may contain arbitrary values. There are a few helper class-
	methods to deal with certain kinds of values systematically.

	"""
	def __init__(self, elems, step=1):
		self.__data__ = list(elems)
		self._lock = threading.Lock()
		self._step = step
		self._iter = self._traverse()
		self._iter.send(None)
		#this is due to the fact that the first action on a generator has to be
		#send(None) or a next() call on the iterator
		#but the step.setter will call self._iter.send(val) before the first
		#next() is called

	@classmethod
	def _string_to_note(cls, note):
		#helper method
		#expects a note string with chord notes separated by spaces
		#examples: 'c e g', 'c' ,'c# d gb', 'd']
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

	def string_to_note(self):
		note_list = []
		for string in self.__data__:
			note_list.append(self._string_to_note(string))
		return Sequence(note_list)

	def __len__(self):
		return len(self.__data__)

	def __getitem__(self, index):
		return self.__data__[index]

	def __setitem__(self, index, value):
		##TODO: update self.data as well by reversing _numerize somehow
		self[index] = value

	def __delitem__(self, index):
		del self[index]
		self._cursor -= 1

	def insert(self, index, obj):
		#insert value before index
		self.__data__.insert(index, obj)

	def __iter__(self):
		return self._iter

	def __next__(self):
		return next(self._iter)

	def _traverse(self):
		cur = 0 		#cursor position
		dir = self.step	#step direction
		yield #to start the generator with a send without skipping the first element
		while True:
			while len(self) > 0:
				i = (yield self[cur])
				#values can be passed into this with send()
				#with this, you can change dir while the iterator runs
				#see: https://docs.python.org/3/howto/functional.html#passing-values-into-a-generator
				if i == 0:
					#send(0) will reset the cursor
					cur = 0
				elif i is None:
					cur += dir
					cur = cur%len(self)
				else:
					dir = i
			yield None
			#this will yield None until some data is in the Sequence

	def reset(self):
		self._iter.send(0)

	@property
	def step(self):
		return self._step

	@step.setter
	def step(self, val):
		if val != 0:
			self._step = val
			self._iter.send(val)
		else:
			raise ValueError('step cannot be zero!')

	def once(self):
		return list(self.__data__)


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
		sequence=Sequence([]),
		receiver=None,
		division=16,
		channel=1,
		step=1
	):
		super().__init__()
		#for inheriting from BaseOutput

		self._running = False
		self._pulses = 0

		Timer().add_receiver(self)
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
		raise NotImplementedError

	@classmethod
	def note_to_midi(cls, notes, msg_type='note_on', channel=1, velocity=127):
		"""
		Converts tuples of integers to a list of mido.Message
		"""
		message_list = []

		if notes:
		#note_to_midi receives notes=None or empty tuple
		#when a sequence skips a beat
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

	def stop(self):
		self._running = False
		self.receiver.reset()
		#mido method to send MIDI all note offs to port

	def start(self):
		self._running = True

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
		if 0 <= val <= 1.0:
			self._note_length = val
		else:
			raise ValueError('Invalid note length: '+str(val))

	@property
	def step(self):
		return self._sequence.step

	@step.setter
	def step(self, val):
		self._sequence.step = val

	@property
	def sequence(self):
		return self._sequence

	@sequence.setter
	def sequence(self, seq):
		self._sequence = seq
		self._seq_iter = iter(seq)
		self._sequence.step = self.step

	##TODO: set up a sequence property so the new sequence is behaving like the old sequence


class StepSequencer(BaseSequencer):
	def __init__(
		self,
		sequence=Sequence([]),
		receiver=None,
		division=16,
		channel=1,
		step=1
	):
		super().__init__(sequence,receiver,division,channel,step)

	def _send(self, msg):
		#overwritten from BaseSequencer
		if self._running:
			if msg.type == 'clock':
				self.clock_callback()

	def clock_callback(self):
		with self._lock:
		#self._lock is inherited from mido.ports.BaseOutput
		#TODO: has all of this to be locked? Can a subset be savely locked?
			if self._pulses == 0:
				self._current_step = next(self._seq_iter)

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



class Arpeggiator(BaseSequencer):
	##TODO: Sequencer and Arpeggiator should inherit from a common base class
	def __init__(self, receiver=None, channel=1):
		super().__init__(
			receiver=receiver,
			division=16,
			channel=channel,
			step=1
		)
		self.rhythm = Sequence([True, True, True, False,])
		self.chords = Sequence(['cmin','d#maj','gmin'])
		self.sequence = self._create_sequence()

	def _send(self, msg):
		#inherited from BaseSequencer
		if self._running:
			if msg.type == 'clock':
				self.clock_callback()

	def clock_callback(self):
		with self._lock:
		#self._lock is inherited from mido.ports.BaseOutput
		#TODO: has all of this to be locked? Can a subset be savely locked?
			if self._pulses == 0:
				self._current_step = next(self._seq_iter)

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
		for chord in self.chords.once():
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

			chord_seq = Sequence(notelist)

			for beat in self.rhythm.once():
				if beat:
					arp_seq.append((next(chord_seq),))
				else:
					arp_seq.append(tuple())

		return Sequence(arp_seq)

class PrintPort(mido.ports.BaseOutput):
	def __init__(self):
		super().__init__()
	def _send(self, msg):
		print(msg)

if __name__ == '__main__':
	##TODO: this should be a test

	sequence1 = Sequence(['c1','c#1','d1','d#1','e1','f1','f#1','g1','g#1','a1','a#1','b1'])
	print(sequence1.string_to_note())
	sequence2 = Sequence(['g#4','c5','f4'])

	output_list = mido.get_output_names()
	print('Select the target port:')
	for num, name in enumerate(output_list):
		print('{num}: {name}'.format(num=num, name=name))

	port = int(input('(seq) '))

	with mido.open_output(mido.get_output_names()[port]) as port:
		Timer().tempo = 160
		arp = Arpeggiator(receiver=port)
		# seq = StepSequencer(receiver=port)
		# seq.division = 16
		# seq.sequence = sequence1.string_to_note()
		# seq.start()
		arp.start()
		time.sleep(30)
		# seq.stop()
		#arp.chord = 'dmaj'
		# time.sleep(5)
		#arp.chord = 'd#sus2'
		# time.sleep(5)
		arp.stop()
	# 	seq1 = Sequencer(sequence=sequence1, receiver=synth)
	# 	seq2 = Sequencer(sequence=sequence2, receiver=synth)
	# 	seq1.start()
	# 	seq2.start()
	# 	time.sleep(5)
	# 	seq1.stop()
	# 	seq2.stop()
