
import pdb
import math
import sqlite3
import time

def load_data_table(fname):
	result = []
	f = open(fname,"r")
	line = f.readline()
	while line != "":
		result.append(line.split("\t")[0].strip())
		line = f.readline()
	f.close()
	return result

def load_track_meta(track_id, fname, delim, delim2, lookup_list):
	result = []
	if lookup_list.count(track_id) > 0:
		lineno = lookup_list.index(track_id)

		f = open(fname, "r")
		while lineno > 0:
			f.readline()
			lineno -= 1
		line = f.readline()
		f.close()

		parts = line.split("\t")
		if parts[0].strip() != track_id:
			print "ERROR!1"
			pdb.set_trace()
		else:
			if delim == None:
				result = parts[1:]
			else:
				result = parts[1].split(delim)

		for i in range(0, len(result)):
			result[i] = result[i].split(delim2)[0]

	return result

def year_equal(y1, y2):
	if y1 == 0 or y2 == 0:
		return 0.0
	elif (y1 - 1900) / 10 == (y2 - 1900) / 10:
		return 1.0
	else:
		return 0.0

def shared_element_count(list1, list2):
	l1_len = len(list1)
	l2_len = len(list2)
	score = 0
	if l1_len > 0 and l2_len > 0:
		if l1_len >= l2_len:
			for i in range(0, l2_len):
				if list1.count(list2[i]) > 0:
					score += 1
		else:
			for i in range(0, l1_len):
				if list2.count(list1[i]) > 0:
					score += 1
	return score

def calculate_similarity(data1, data2):
	score = 0.0
	data1_denom = 0.0
	data2_denom = 0.0
	
	#artist will be a binary feature
	artist1 = data1[1].lower().strip()
	artist2 = data2[1].lower().strip()
	if artist1 == artist2 or artist1.count(artist2) > 0 or artist2.count(artist1) > 0:
		score += 1.0
	data1_denom += 1.0
	data2_denom += 1.0

	#energy, loudness, and tempo
	score += float(data1[2]) * float(data2[2])
	data1_denom += float(data1[2]) ** 2.0
	data2_denom += float(data2[2]) ** 2.0

	score += float(data1[3]) * float(data2[3])
	data1_denom += float(data1[3]) ** 2.0
	data2_denom += float(data2[3]) ** 2.0

	score += float(data1[4]) * float(data2[4])
	data1_denom += float(data1[4]) ** 2.0
	data2_denom += float(data2[4]) ** 2.0

	# year will also be a binary feature
	year1 = int(data1[5].strip())
	year2 = int(data2[5].strip())
	score += year_equal(year1, year2)

	if year1 > 0:
		data1_denom += 1.0
	if year2 > 0:
		data2_denom += 1.0

	# lyrics are also binary
	score += float(shared_element_count(data1[6], data2[6]))
	data1_denom += len(data1[6])
	data2_denom += len(data2[6])

	# tags are also binary
	score += float(shared_element_count(data1[7], data2[7]))
	data1_denom += len(data1[7])
	data2_denom += len(data2[7])

	return float(score) / float(math.sqrt(float(data1_denom)) * math.sqrt(float(data2_denom)))

print "Loading lyrics lookup list... ",
lyrics_table = load_data_table("data/lyrics_nodups.txt")
print "done.\nLoading tags lookup list... ",
tags_table = load_data_table("data/tags_nodups.txt")
print "done.\nLoading song data... ",

# Load the songs file... only 55 MB
msd_file = open("data/msd_nodups.txt","r")
msd_lines = msd_file.readlines()
msd_file.close()

print "done.\nCalculating similarities... "

line_count = len(msd_lines)
processed = 0

conn = sqlite3.connect("song_similarities.db")
cur = conn.cursor()

inserts = []

for i in range(0,line_count):
	lineA = msd_lines[i]
	for j in range(i+1, line_count):
		lineB = msd_lines[j]

		dataA = lineA.split("\t")
		dataB = lineB.split("\t")

		dataA.append(load_track_meta(dataA[0], "data/lyrics_nodups.txt", ",", ":", lyrics_table))
		dataA.append(load_track_meta(dataA[0], "data/tags_nodups.txt", None, ",", tags_table))

		dataB.append(load_track_meta(dataB[0], "data/lyrics_nodups.txt", ",", ":", lyrics_table))
		dataB.append(load_track_meta(dataB[0], "data/tags_nodups.txt", None, ",", tags_table))

		sim = calculate_similarity(dataA, dataB)

		inserts.append((dataA[0], dataB[0], sim))
		processed += 1

		if processed % 1000 == 0:
			print "Saving %d to %d... " % (processed - 1000, processed),
			cur.executemany("INSERT INTO song_similarities VALUES (?,?,?)", inserts)
			conn.commit()
			inserts = []
			print "done."

		if processed % 10000 == 0:
			time.sleep(60*min(10, int(processed / 10000)))

if len(inserts) > 0:
	print "Saving final", len(inserts),
	cur.executemany("INSERT INTO song_similarities VALUES (?,?,?)", inserts)
	conn.commit()
	print "done."

conn.close()

print "Done."
