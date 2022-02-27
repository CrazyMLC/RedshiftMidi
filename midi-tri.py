import mido,sys

mid = mido.MidiFile(sys.argv[1])

if len(sys.argv) > 2:
	t = sys.argv[2]
	selected = t.split(',')
	for i in range(len(selected)):
		selected[i] = int(selected[i])
else:
	selected = [0,1,2]
	t = f'{selected[0]},{selected[1]},{selected[2]}'

shift = 0
if len(sys.argv) > 3:
	shift = int(sys.argv[3])
	
fixtempo = 0
if len(sys.argv) > 4:
	fixtempo = int(sys.argv[4])

tracks = []
tempo = None
ticks = None

for track in mid.tracks:
	notes = []
	for msg in track:
		if not tempo and msg.type == 'set_tempo':
			tempo = msg.tempo
		if not ticks and msg.type == 'time_signature':
			ticks = 32 * (msg.clocks_per_click/msg.notated_32nd_notes_per_beat)
		if 'note' in msg.type:
			if msg.type == 'note_on':
				time = 0
				if notes:
					time = notes[-1][1]+notes[-1][2]
				if msg.time > 0:
					notes.append([0, time, msg.time])
					time += msg.time
				notes.append([msg.note, time, 0])
			if msg.type == 'note_off':
				notes[-1][2] = msg.time
	if notes:
		tracks.append(notes)

if fixtempo:
	tempoadjust = 4000000/30
	tempo = round(tempo/tempoadjust)*tempoadjust

tickrate = 30*mido.tick2second(1, ticks, tempo)

maxlen = 0
state = [0,0,0]
for i,s in enumerate(selected):
	maxlen = max(maxlen, tracks[s][-1][1]+tracks[s][-1][2])
	state[i] = tracks[s][0][0]

queue = []
passed = 0

for i in range(maxlen+1):
	newstate = [0,0,0]
	#this is a really bad way to do this but, well, foolproof at least
	for s in range(len(selected)):
		for msg in tracks[selected[s]]:
			if msg[1] <= i < msg[1]+msg[2]:
				newstate[s] = msg[0]
				break
	if newstate != state:
		queue.append([state.copy(), i-passed])
		passed = i
		state = newstate.copy()

commands = ['DATA']
for event in queue:
	def append(str):
		if len(commands[-1]) + len(str) > 24:
			commands.append('DATA')
		commands[-1] += str
	
	length = round(event[1]*tickrate)
	while length > 0:
		c1 = f' {min(99,length)*100 + max(min(event[0][0]+shift,99),0)}'
		c2 = f' {max(min(event[0][1]+shift,99),0)*100 + max(min(event[0][2]+shift,99),0)}'
		length -= 99
		append(c1)
		append(c2)

with open(sys.argv[1]+f'.{t}.red', 'w') as output:
	output.write('\n'.join(commands))
	output.write('\nLINK 801\nMARK S\nSEEK -9999\nMARK L\nCOPY F X\nSWIZ X 43 T\nSWIZ X 21 #SQR0\nCOPY F X\nSWIZ X 43 #SQR1\nSWIZ X 21 #TRI0\nMARK W\nWAIT\nSUBI T 1 T\nTJMP W\nTEST EOF\nTJMP S\nJUMP L\n')
