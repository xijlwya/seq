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

def noteToMIDI(notes, msg_type='note_on', channel=1, velocity=127):
	"""
	Converts strings like 'c1', 'f#2', 'bb-3' to mido.Messages
	"""
	message_list = []

	if notes:
	#noteToMIDI receives None when a sequence skips a beat
		for note in notes.split(' '):
			if note:
				note_value = note_names[note[0].lower()]
			else:
				break

			if note[1] == '#' or note[1] == 'b':
				if note[1] == '#':
					note_value += 1
				elif note[1] == 'b':
					note_value -= 1
				note_value += 12*(int(note[2:])-4)
				#-4 because c4 is the middle c - MIDI note 60
			else:
				note_value += 12*(int(note[1:])-4)

			message_list.append(
				mido.Message(
					msg_type,
					note=note_value,
					channel=channel,
					velocity=velocity
				)
			)

	return message_list

class Sequence(collections.abc.MutableSequence):
	"""
	A sequence is a ring list which can be traversed by iterating over it. This
	iteration does not terminate and the contents of the list are returned
	repeatedly.

	Depending on the self.direction, the sequence traverses forward or backward.
	"""
	def __init__(self, elems, direction='forward', skip=1):
		self.__data__ = list(elems)
		self.direction = direction
		self.skip = skip
		#every 'skip' calls to __next__, the sequence will play a note

		self.calls = 0
		self.lock = threading.Lock()
		self.reset()

	def __len__(self):
		return len(self.__data__)

	def __getitem__(self, index):
		if len(self) > 0:
			try:
				return self.__data__[index]
			except IndexError:
				return self.__data__[index%len(self.__data__)]
		else:
			raise IndexError('Sequence is empty')

	def __setitem__(self, index, value):
		self[index] = value

	def __delitem__(self, index):
		del self[index]
		if self.cursor > 0:
			self.cursor -= 1

	def insert(self, index, obj):
		#insert value before index
		self.__data__.insert(index, obj)

	def __next__(self):
		#CAUTION: this will iterate forever!
		self.calls += 1

		if len(self) > 0:
			with self.lock:
				if self.calls % self.skip == 0:
					#IF the number of calls is a multiple of skip

					self.calls = 0

					if self.direction == 'forward':
						if self.cursor < len(self.__data__):
							self.cursor += 1
							return self.__data__[self.cursor-1]
						else:
							self.cursor = 1
							return self.__data__[0]

					elif self.direction == 'backward':
						if self.cursor > 0:
							self.cursor -= 1
							return self.__data__[self.cursor+1]
						else:
							self.cursor = len(self.__data__) - 1
							return self.__data__[0]

					elif self.direction == 'random':
						self.cursor = random.randint(0,len(self.__data__)-1)
						return self.__data__[self.cursor]
					else:
						raise ValueError(self.direction + ' is invalid direction.')

				else:
					self.calls += 1

		else:
			raise StopIteration

	def __iter__(self):
		return self

	def reset(self):
		if self.direction == 'backward':
			self.cursor = len(self.__data__) - 1
		else:
			self.cursor = 0

	@property
	def skip(self):
		return self._skip

	@skip.setter
	def skip(self, val):
		if 1 <= val and isinstance(val, int):
			self._skip = val
		else:
			raise ValueError('Invalid skip: '+str(val))


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

	-	'receiver' is an mido output with a send method
	-	'ppqn' means "pulses per quarter note" and determines how many clock
	msgs are sent per quarter note
	-	'tempo' is the rate of the clock in bpm. That means that tempo*ppqn
	pulses are sent in one minute
	"""
	def __init__(self, ppqn=24, tempo=120):
		self.ppqn = ppqn
		self.running = False
		self.tempo = tempo
		self.receivers = []
		self.lock = threading.Lock()
		self.start()

	def _start(self):
		self.running = True
		delta_t = 0
		while self.running:
			t0 = time.perf_counter()
			if delta_t >= self._pulse_length:
				self.running = False
				with self.lock:
					for r in self.receivers:
						if not r.closed:
							self.running = True
							r.send(mido.Message('clock'))
						else:
							self.receivers.remove(r)
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
			self._pulse_length = 60/(self.tempo*self.ppqn)
		else:
			raise ValueError('tempo out of bounds.')

	def add_receiver(self, add):
		if 	hasattr(add, 'send') and \
			hasattr(add, 'closed') and \
			add not in self.receivers and \
			not add.closed:
			#checks whether the new receiver is a mido port
			self.receivers.append(add)

	def remove_receiver(self, rec):
		self.receivers.remove(rec)

class Sequencer(mido.ports.BaseOutput):
	"""
	A sequencer plays back sequences to a MIDI device. It manages its own tempo
	and tempo subdivision. It executes in a separate thread and is safely
	manipulateable during playback.
	"""
	def __init__(
		self,
		sequence=Sequence([]),
		receiver=None,
		division=16,
		channel=1,
		direction='forward',
		skip=1,
	):
		super().__init__(self)
		self.running = False

		self.timer = Timer()
		self.timer.add_receiver(self)

		self.seq_iter = iter(sequence)
		self.seq = sequence
		self.receiver = receiver
		self.division = division #the musical note division, e.g. 16 means 16th-notes; i.e. notes per measure
		self.channel = channel
		self.note_length = 0.5
		self.pulses = 0
		self.seq.skip = skip
		self.lock = threading.Lock()

	def _send(self, msg):
		#inherited fom mido.BaseOutput
		if msg.type == 'clock' and self.running:
			self.clock_callback()

	def clock_callback(self):
		with self.lock:
			if self.pulses == 0:
				try:
					self._current_step = next(self.seq_iter)
				except ValueError:
					self.seq.direction = 'forward'
					self._current_step = next(self.seq_iter)

				for note in noteToMIDI(self._current_step, channel=self.channel):
					self.receiver.send(note)
				self.pulses += 1

			elif self.pulses == round(self._pulse_limit*self.note_length):
				for note in noteToMIDI(self._current_step, msg_type='note_off', channel=self.channel):
					self.receiver.send(note)
				self.pulses = 0

			else:
				self.pulses += 1

	def stop(self):
		self.receiver.reset()
		self.running = False

	def start(self):
		self.running = True

	@property
	def direction(self):
		return self.seq.direction

	@direction.setter
	def direction(self, dir):
		self.seq.direction = dir

	@property
	def division(self):
		return self._division

	@division.setter
	def division(self, val):
		#TODO decouple Timer and Sequencer

		if 0 < val and round(self.timer.ppqn*4/val) > 0:
			#TODO is this check sane??
			self._division = val
			self._pulse_limit = round(self.timer.ppqn*4/self.division)
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
			raise ValueError('Note length is the relative time a note takes of one step')

	##TODO: set up a sequence property so the new sequence is behaving like the old sequence

if __name__ == '__main__':
	##TODO: this should be a test
	sequence1 = Sequence(['c4','d#4','g4','',''])
	sequence2 = Sequence(['g3','g3','c3','c3'])

	with mido.open_output(mido.get_output_names()[1]) as reface:
		seq1 = Sequencer(sequence=sequence1, receiver=reface)
		seq2 = Sequencer(sequence=sequence2, receiver=reface)
		print('seq1 timer: '+str(seq1.timer))
		print('seq2 timer: '+str(seq2.timer))
		# print(seq1.timer.receivers)
		seq1.start()
		seq2.start()
		time.sleep(5)
		# seq2.skip = 2
		# time.sleep(5)
		# seq1.direction = 'backward'
		# print('seq1 backwards')
		# seq2.direction = 'random'
		# print('seq2 random')
		# time.sleep(0.5)
		# seq1.skip = 2
		# print('seq1 skip 2')
		# seq2.skip = 3
		# print('seq2 skip 3')
		# seq2.division = 64
		# print('seq2 div 64')
		# seq2.note_length = 0.9
		# print('seq2 notelength 0.9')
		# time.sleep(0.5)
		# seq1.note_length = 0.2
		# print('seq1 notelnegth 0.2')
		# seq1.division = 32
		# print('seq1 div 32')
		# seq1.direction = 'forward'
		# print('seq1 forward')
		# time.sleep(0.5)
		# seq2.seq = sequence1
		# seq1.seq = sequence2
		# time.sleep(0.5)
		seq1.stop()
		seq2.stop()
