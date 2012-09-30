names = []

fin = open("pokemon.csv", "r")
for line in fin:
	names.append(line.split(",", 2)[1])

fin = open("pokemon_flavortexts.csv", "r")
for line in fin:
	splitstr = line.split(",")
	if names[int(splitstr[0]) - 1] in line:
			print line

