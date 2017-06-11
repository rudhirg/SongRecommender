
songs_file = open("out/msd_nodups.txt")

smallest = 99999
largest = -9999
line = songs_file.readline()
while line != "":
	curr = int(line.split("\t")[-1])
	if smallest > curr and curr > 0:
		smallest = curr
	if largest < curr:
		largest = curr
	line = songs_file.readline()

songs_file.close()
print "Range: %d to %d" % (smallest, largest)

