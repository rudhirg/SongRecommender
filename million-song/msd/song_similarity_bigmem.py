
import pdb
import math
import sqlite3
import time
import random
from operator import itemgetter

LYRIC_CUTOFF = 5
TAG_CUTOFF = 5
def load_data2(fname, delim, delim2, top_cutoff):
	result = {}

	f = open(fname, "r")
	line = f.readline()
	while line != "":
		parts = line.strip().split("\t")
		
		#for some reason not all lines in the lyrics file have lyrics
		if len(parts) < 2:
			line = f.readline()
			continue
		
		track_id = parts[0].strip()
		subparts = None
		
		if delim == None:
			subparts = parts[1:]
		else:
			subparts = parts[1].split(delim)

		if delim2 != None:
			for i in range(0, len(subparts)):
				split_subpart = subparts[i].split(delim2)
				if len(split_subpart) < 2:
					pdb.set_trace()
				subparts[i] = (split_subpart[0], float(split_subpart[1]))
			subparts = sorted(sorted(subparts, key=itemgetter(0)), key=itemgetter(1), reverse=True)[0:top_cutoff]
			for i in range(0, len(subparts)):
				subparts[i] = subparts[i][0]
			#pdb.set_trace()

		result[track_id] = subparts
		line = f.readline()
	f.close()

	return result
	
def load_data(fname, delim, delim2, top_cutoff):
	result = {}

	f = open(fname, "r")
	line = f.readline()
	while line != "":
		parts = line.strip().split("\t")
		
		#for some reason not all lines in the lyrics file have lyrics
		if len(parts) < 2:
			line = f.readline()
			continue
		
		track_id = parts[0].strip()
		subparts = None
		
		if delim == None:
			subparts = parts[1:]
		else:
			subparts = parts[1].split(delim)

		if delim2 != None:
			for i in range(0, len(subparts)):
				split_subpart = subparts[i].split(delim2)
				if len(split_subpart) < 2:
					pdb.set_trace()
				subparts[i] = (split_subpart[0], int(split_subpart[1]))
			subparts = sorted(sorted(subparts, key=itemgetter(0)), key=itemgetter(1), reverse=True)[0:top_cutoff]
			for i in range(0, len(subparts)):
				subparts[i] = subparts[i][0]
			#pdb.set_trace()

		result[track_id] = subparts
		line = f.readline()
	f.close()

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

def calculate_similarity(data1, data2, loudint, tempoint):
	global LYRIC_CUTOFF
	global TAG_CUTOFF
	
	score = 0.0
	data1_denom = 0.0
	data2_denom = 0.0
	
	#artist will be a binary feature
	artist1 = data1[1].lower().strip()
	artist2 = data2[1].lower().strip()
	if artist1 == artist2:
		score += 1.0
	data1_denom += 1.0
	data2_denom += 1.0
	
	#energy, loudness, and tempo
	
	#energy are all zeros so ignore them
	'''
	score += float(data1[2]) * float(data2[2]) / energyint / energyint
	data1_denom += float(data1[2] / energyint) ** 2.0
	data2_denom += float(data2[2] / energyint) ** 2.0
	'''

	score += float(data1[3]) * float(data2[3]) / loudint / loudint
	data1_denom += (float(data1[3]) / float(loudint)) ** 2.0
	data2_denom += (float(data2[3]) / float(loudint)) ** 2.0

	score += float(data1[4]) * float(data2[4]) / tempoint / tempoint
	data1_denom += (float(data1[4]) / float(tempoint )) ** 2.0
	data2_denom += (float(data2[4]) / float(tempoint )) ** 2.0

	# year will also be a binary feature
	year1 = int(data1[5].strip())
	year2 = int(data2[5].strip())
	score += year_equal(year1, year2)

	if year1 > 0:
		data1_denom += 1.0
	if year2 > 0:
		data2_denom += 1.0
	
	
	# lyrics are also binary
	lyric_score = float(shared_element_count(data1[6], data2[6]))
	score += lyric_score / float(LYRIC_CUTOFF)
	
	if len(data1[6]) == 0 or len(data2[6]) == 0:
		data1_denom += 1.0;
		data2_denom += 1.0;
	else:
		data1_denom += float(len(data1[6])) / float(LYRIC_CUTOFF)
		data2_denom += float(len(data2[6])) / float(LYRIC_CUTOFF)
	
	# tags are also binary
	tag_score = float(shared_element_count(data1[7], data2[7]))
	score += tag_score / float(TAG_CUTOFF)
	
	if len(data1[7]) == 0 or len(data2[7]) == 0:
		data1_denom += 1.0;
		data2_denom += 1.0;
	else:
		data1_denom += float(len(data1[7])) / float(TAG_CUTOFF)
		data2_denom += float(len(data2[7])) / float(TAG_CUTOFF)
	
	result_val = float(score) / float(math.sqrt(float(data1_denom)) * math.sqrt(float(data2_denom)))
	return result_val

print "Loading lyrics... ",
lyrics = load_data("data/lyrics_nodups.txt", ",", ":", LYRIC_CUTOFF)
print "done.\nLoading tags... ",
tags = load_data2("data/tags_nodups.txt", None, "," , TAG_CUTOFF)
#tags = {}
print "done.\nLoading songs... ",
msd_file = open("data/msd_nodups.txt")
msd_lines = msd_file.readlines()
msd_file.close()
print "done.\nCalculating similarities... "

line_count = len(msd_lines)
processed = 0

conn = sqlite3.connect("song_similarities.db")
cur = conn.cursor()

inserts = []
linetemp = (msd_lines[0]).split("\t")
#ENERGY_MAX = float(linetemp[2])
#ENERGY_MIN = float(linetemp[2])
LOUDNESS_MAX = float(linetemp[3])
LOUDNESS_MIN = float(linetemp[3])
TEMPO_MAX = float(linetemp[4])
TEMPO_MIN = float(linetemp[4])

# calculating min and max for energy, loudness and tempo
for i in range(0, line_count):
	linetemp = msd_lines[i]
	datatemp = linetemp.split("\t")
		
	if float( (datatemp[3]))>LOUDNESS_MAX:
		LOUDNESS_MAX = float( (datatemp[3]))
	if float( (datatemp[3]))<LOUDNESS_MIN:
		LOUDNESS_MIN = float( (datatemp[3]))
	if float( (datatemp[4]))>TEMPO_MAX:
		TEMPO_MAX = float( (datatemp[4]))
	if float( (datatemp[4]))<TEMPO_MIN:
		TEMPO_MIN = float( (datatemp[4]))	

#pdb.set_trace()

sample = random.sample(xrange(line_count), 1000)

t0 = time.clock()

for i in range(0,len(sample)):
	lineA = msd_lines[i]
	for j in range(i+1, len(sample)):
		lineB = msd_lines[j]

		dataA = lineA.split("\t")
		dataB = lineB.split("\t")

		if lyrics.has_key(dataA[0]):
			dataA.append(lyrics[dataA[0]])
		else:
			dataA.append([])
		if tags.has_key(dataA[0]):
			dataA.append(tags[dataA[0]])
		else:
			dataA.append([])
			
		if lyrics.has_key(dataB[0]):
			dataB.append(lyrics[dataB[0]])
		else:
			dataB.append([])
		if tags.has_key(dataB[0]):
			dataB.append(tags[dataB[0]])
		else:
			dataB.append([])

		sim = calculate_similarity(dataA, dataB, LOUDNESS_MAX-LOUDNESS_MIN, TEMPO_MAX-TEMPO_MIN)

		inserts.append((dataA[0], dataB[0], sim))
		processed += 1

		if processed % 5000 == 0:
			print " Saving %d to %d... " % (processed - 5000, processed),
			cur.executemany("INSERT INTO song_similarities VALUES (?,?,?)", inserts)
			conn.commit()
			inserts = []
			print "done."

	#print " * Sleeping for 5s...",
	#time.sleep(5)
	#print "done."

print "Elapsed:", (time.clock() - t0)


if len(inserts) > 0:
	print "Saving final", len(inserts),
	cur.executemany("INSERT INTO song_similarities VALUES (?,?,?)", inserts)
	conn.commit()
	print "done."

conn.close()

print "Done."
