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
	'sus2'		:(0, 2, 7),
	'sus4'		:(0, 5, 7),
	'dim'		:(0, 3, 6),
	'dim7'		:(0, 3, 6, 9),
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

	"""
	def __init__(self, elems):
		self.data = list(elems)
		self._step = 1
		self._lock = threading.Lock()
		self.reset()
		self.__data__ = [0]*len(self.data)
		for pos, note in enumerate(self.data):
			self.__data__[pos] = self._numerize(note)

	def _numerize(self, note):
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


	def __len__(self):
		return len(self.__data__)

	def __getitem__(self, index):
		return self.__data__[index]

	def __setitem__(self, index, value):
		##TODO: update self.data as well by reversing _numerize somehow
		self[index] = value

	def __delitem__(self, index):
		del self[index]
		del self.data[index]
		self._cursor -= 1

	def insert(self, index, obj):
		#insert value before index
		if isinstance(obj, string):
			self.data.insert(index, obj)
			self.__data__.insert(index, self.numerize(obj))
		else:
			##TODO: update self.data as well by reversing _numerize somehow
			self.__data__.insert(index, obj)

	def __next__(self):
		#CAUTION: this will iterate forever!
		with self._lock:
			if len(self) > 0:
				self._cursor += self._step
				self._cursor = self._cursor%len(self)
				#with this, the cursor will always be within len(self)
				return self[self._cursor - self._step]
			else:
				raise StopIteration

	def __iter__(self):
		return self

	def reset(self):
		self._cursor = 0

	@property
	def step(self):
		return self._step

	@step.setter
	def step(self, val):
		self._step = val


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


class Sequencer(mido.ports.BaseOutput):
	"""
	A sequencer plays back sequences to a MIDI device.
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
		self.__lock = threading.Lock()
		#mido.ports.BaseOutput has a self._lock as well, so this is dundered

		self._running = False

		Timer().add_receiver(self)

		self._seq_iter = iter(sequence)
		self._sequence = sequence
		self.receiver = receiver
		#receiver is supposed to be a mido port with a send(msg) method

		self.division = division
		#the musical note division,
		#e.g. 16 means 16th-notes; i.e. notes per measure

		self.channel = channel
		#MIDI channel the sequencer sends on

		self.note_length = 0.5
		#note length is the relative time a note takes of one step

		self._pulses = 0
		self._step = step


	def _send(self, msg):
		#inherited from mido.BaseOutput
		if self._running:
			if msg.type == 'clock':
				self.clock_callback()
			elif msg.type == 'note_on' or msg.type == 'note_off':
				self.note_callback(msg)

	def clock_callback(self):
		with self.__lock:
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

	@classmethod
	def note_to_midi(cls, notes, msg_type='note_on', channel=1, velocity=127):
		"""
		Converts tuples of integers to MIDI Note messages
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

	def note_callback(self, msg):
		pass
		#TODO: transpose

	def stop(self):
		self.receiver.reset()
		#mido method to send MIDI all note offs to port
		self._running = False

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

class Arpeggiator(Sequencer):
	##TODO: Sequencer and Arpeggiator should inherit from a common base class
	def __init__(self, receiver=None):
		super().__init__(
			sequence=Sequence([]),
			receiver=receiver,
			division=16,
			channel=1,
			step=1
		)
		self.rhythm = [True]
		self.chord = 'cdim7'
		self._sequence = Sequence(self._create_sequence())

	@classmethod
	def _from_val_to_notename(cls, val):
		##TODO: how the hell do I get the right note --> c# == db in this
		for k,v in note_names.items():
			if v == val:
				return k
			elif v+1 == val:
				return k+'#'
			elif v-1 == val:
				return k+'b'


	def _create_sequence(self):
		#translates the chord to notes like 'c#'', 'd', etc.'
		if self.chord[1] == '#' or self.chord[1] == 'b':
			_root_note = self.chord[:2].lower()
			_chord_modifier = self.chord[2:].lower()
		else:
			_root_note = self.chord[:1].lower()
			_chord_modifier = self.chord[1:].lower()


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
			notelist.append((note_val + semitones,))
			#to return a list of tuples

		return notelist

if __name__ == '__main__':
	##TODO: this should be a test
	arp = Arpeggiator()
	print(arp._create_sequence())

	sequence1 = Sequence(['c1','c#1','d1','d#1','e1','f1','f#1','g1','g#1','a1','a#1','b1'])
	print(sequence1.__data__)
	# sequence2 = Sequence(['g#4','c5','f4'])
	#
	# output_list = mido.get_output_names()
	# print('Select the target port:')
	# for num, name in enumerate(output_list):
	# 	print('{num}: {name}'.format(num=num, name=name))
	#
	# port = int(input('(seq)'))
	#
	# with mido.open_output(output_list[port]) as synth:
	# 	seq1 = Sequencer(sequence=sequence1, receiver=synth)
	# 	seq2 = Sequencer(sequence=sequence2, receiver=synth)
	# 	seq1.start()
	# 	seq2.start()
	# 	time.sleep(5)
	# 	seq1.stop()
	# 	seq2.stop()
