import pdb

def get_dups():
	print "Reading duplicates file...",
	dup_file = open("data/msd_duplicates.txt")
	line = dup_file.readline()
	dup_lines = []
	dup_group = []
	while line != "":
		if line.startswith("%") and len(dup_group) > 0:
			dup_lines.extend(dup_group[1:])
			dup_group = []
		if not line.startswith("%") and not line.startswith("#"):
			dup_group.append(line.strip())
		line = dup_file.readline()
	if len(dup_group) > 0:
		dup_lines.extend(dup_group[1:])
	dup_file.close()
	print "done."
	return dup_lines

def remove_dups(fname, fout_name, dup_lines):
	print "Removing dups from %s..." % fname
	num_dups = 0
	msd_file = open("out/" + fname)
	msd_out = open("out/" + fout_name,"w")
	line = msd_file.readline()
	processed = 1
	out_lines = []
	while line != "":
		track_id = line.split("\t")[0].strip()
		if dup_lines.count(track_id) == 0:
			out_lines.append(line)
		else:
			#print " Found dup, ignoring:", line
			num_dups += 1
		processed += 1

		if processed % 5000 == 0:
			print "Processing %d to %d" %(processed - 5000, processed)
			msd_out.write("".join(out_lines))
			out_lines = []

		line = msd_file.readline()
	if len(out_lines) > 0:
		msd_out.write("".join(out_lines))
	msd_out.close()
	msd_file.close()
	print "Done. Found %d dups of possible %d" % (num_dups, len(dup_lines))

dup_list = get_dups()
print "Total dups:", len(dup_list)
pdb.set_trace()

remove_dups("lyrics.txt", "lyrics_nodups.txt", dup_list)

