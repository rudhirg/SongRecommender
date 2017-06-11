
error_file = open("data/sid_mismatches.txt")
out_file = open("data/mismatched_tracks.txt", "w")

line = error_file.readline()

while line != "":
	out_file.write(line.split()[2].rstrip(">") + "\n")
	line = error_file.readline()

error_file.close()
out_file.close()
