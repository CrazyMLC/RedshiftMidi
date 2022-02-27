import mido,sys

mid = mido.MidiFile(sys.argv[1])

trackskip = 0
if len(sys.argv) > 2:
	t = sys.argv[2]
trackskip = float(t)

shift = 0
if len(sys.argv) > 3:
	shift = int(sys.argv[3])

notes = []
tempo = None
ticks = None

for track in mid.tracks:
	foundnotes = False
	for msg in track:
		if not tempo and msg.type == 'set_tempo':
			tempo = msg.tempo
		if not ticks and msg.type == 'time_signature':
			ticks = 32 * (msg.clocks_per_click/msg.notated_32nd_notes_per_beat)
		if not foundnotes and 'note' in msg.type:
			if trackskip > 0:
				trackskip -= 1
				break
			if msg.type == 'note_on':
				if msg.time > 0:
					notes.append([0, msg.time])
				notes.append([msg.note, 0])
			if msg.type == 'note_off':
				notes[-1][1] = msg.time
	if notes:
		foundnotes = True
	if notes and tempo and ticks:
		break

tickrate = 30*mido.tick2second(1, ticks, tempo)

commands = ['DATA']

for note in notes:
	length = round(note[1]*tickrate)
	while length > 0:
		c = f' {min(99,length)*100 + max(min(note[0]+shift,99),0)}'
		length -= 99
		if len(commands[-1])+len(c) > 24:
			commands.append('DATA')
		commands[-1] += c

with open(sys.argv[1]+f'.{t}.red', 'w') as output:
	output.write('\n'.join(commands))
	output.write('\nLINK 801\nMARK S\nSEEK -9999\nMARK L\nCOPY F X\nSWIZ X 43 T\nSWIZ X 21 #SQR0\nMARK W\nWAIT\nSUBI T 1 T\nTJMP W\nTEST EOF\nTJMP S\nJUMP L')
