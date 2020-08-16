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

			message_list.append(mido.Message(msg_type, note=note_value, channel=channel, velocity=velocity))

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

	def insert(self, index, obj):
		#insert value before index
		self.__data__.insert(index, obj)

	def __next__(self):
		#CAUTION: this will iterate forever!
		self.calls += 1

		if len(self) > 0:
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

class Timer:
	def __init__(self, receiver=None, ppqn=24, tempo=120):
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
		self.ppqn = ppqn
		self.running = False
		self.receiver = receiver
		self.tempo = tempo

		self.start()

	def _start(self):
		self.running = True
		delta_t = 0
		while self.running:
			t0 = time.perf_counter()
			if delta_t >= self._pulse_length:
				if self.receiver.closed:
					self.running = False
				else:
					self.receiver.send(mido.Message('clock'))

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
		timer=None,
		tempo=120,
		division=16,
		channel=1
	):
		super().__init__(self)
		self.running = False

		if timer:
			self.timer = timer
		else:
			self.timer = Timer(receiver=self, tempo=tempo)

		self.seq = iter(sequence)
		self.receiver = receiver
		self.division = division #the musical note division, e.g. 16 means 16th-notes; i.e. notes per measure
		self.channel = channel
		self.note_length = 0.5
		self.pulses = 0
		self.lock = threading.Lock()

	def _send(self, msg):
		#inherited fom mido.BaseOutput
		if msg.type == 'clock' and self.running:
			self.clock_callback()

	def clock_callback(self):
		with self.lock:
			if self.pulses == 0:
				self._current_step = next(self.seq)
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
	def division(self):
		return self._division

	@division.setter
	def division(self, val):
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

if __name__ == '__main__':
	sequence1 = Sequence(['c4','d4','e4','f4'], direction='backward')
	sequence2 = Sequence(['', 'd#1', '', 'd#1', None, 'c#1', '', 'c#1', 'c2', 'd#2', 'c2', 'd#2', 'a#0', 'a#0', 'a#0', 'a#0'], skip=3)

	with mido.open_output(mido.get_output_names()[0]) as reface:
		seq = Sequencer(sequence=sequence1, receiver=reface)
		seq.start()
		time.sleep(5)
		seq.stop()
