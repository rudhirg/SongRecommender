
import pdb
import math
import sqlite3
import time
import random
from operator import itemgetter

class SongSimilaritySharedData:
	def __init__(self):
		self.LYRIC_CUTOFF = 5
		self.TAG_CUTOFF = 5

	def load_tags(self, fname):
		result = {}
		f = open(fname, "r")
		line = f.readline()
		while line != "":
			parts = line.strip().split("\t")
			
			#for some reason not all lines have entries
			if len(parts) < 2:
				line = f.readline()
				continue
			
			track_id = parts[0].strip()
			subparts = parts[1:]

			for i in range(0, len(subparts)):
				split_subpart = subparts[i].split(",")
				subparts[i] = (split_subpart[0], float(split_subpart[1]))
			subparts = sorted(sorted(subparts, key=itemgetter(0)), key=itemgetter(1), reverse=True)[0:self.TAG_CUTOFF]
			for i in range(0, len(subparts)):
				subparts[i] = subparts[i][0]

			result[track_id] = subparts
			line = f.readline()
		f.close()
		return result

	def load_lyrics(self, fname):
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
			subparts = parts[1].split(",")

			for i in range(0, len(subparts)):
				split_subpart = subparts[i].split(":")
				subparts[i] = (split_subpart[0], int(split_subpart[1]))
			subparts = sorted(sorted(subparts, key=itemgetter(0)), key=itemgetter(1), reverse=True)[0:self.LYRIC_CUTOFF]
			for i in range(0, len(subparts)):
				subparts[i] = subparts[i][0]

			result[track_id] = subparts
			line = f.readline()
		f.close()
		return result

	def initialize(self, lyrics_file, tags_file, map_file, songs_file, songs_map_file):
		print "Loading lyrics... ",
		lyrics = self.load_lyrics(lyrics_file)
		print "done.\nLoading tags... ",
		tags = self.load_tags(tags_file)
		print "done.\nLoading song-track map...",
		stmap_file = open(map_file)
		stmap_line = stmap_file.readline()
		stmap = {}
		while stmap_line != "":
			stmap_line_split = stmap_line.strip().split("\t")
			stmap[stmap_line_split[0]] = stmap_line_split[1]
			stmap_line = stmap_file.readline()
		stmap_file.close()
		print "done.\nLoading songs... ",
		msd_file = open(songs_file)
		msd_lines = msd_file.readlines()
		msd_file.close()
		print "done.\nLoading song map file...",
		sm_file = open(songs_map_file)
		sm_line = sm_file.readline()
		song_id_map = {}
		while sm_line != "":
			hi = sm_line.strip().split()
			if len(hi) > 1:
				song_id_map[hi[0]] = int(hi[1])
			sm_line = sm_file.readline()
		sm_file.close()
		print "done.\nPreparing data...",

		line_count = len(msd_lines)
		linetemp = (msd_lines[0]).split("\t")
		self.LOUDNESS_MAX = float(linetemp[3])
		self.LOUDNESS_MIN = float(linetemp[3])
		self.TEMPO_MAX = float(linetemp[4])
		self.TEMPO_MIN = float(linetemp[4])

		self.songs = {}

		# calculating min and max for energy, loudness and tempo
		for i in range(0, line_count):
			linetemp = msd_lines[i].strip()
			datatemp = linetemp.split("\t")
			track_id = stmap[datatemp[0]]

			if lyrics.has_key(track_id):
				datatemp.append(lyrics[track_id])
			else:
				datatemp.append([])
			
			if tags.has_key(track_id):
				datatemp.append(tags[track_id])
			else:
				datatemp.append([])

			if song_id_map.has_key(datatemp[0]) > 0:
				self.songs[song_id_map[datatemp[0]]] = datatemp

			if i >0 and i % 50000 == 0:
				print " Finished %d of %d" % (i, line_count)

			if float( (datatemp[3]))>self.LOUDNESS_MAX:
				self.LOUDNESS_MAX = float( (datatemp[3]))
			if float( (datatemp[3]))<self.LOUDNESS_MIN:
				self.LOUDNESS_MIN = float( (datatemp[3]))
			if float( (datatemp[4]))>self.TEMPO_MAX:
				self.TEMPO_MAX = float( (datatemp[4]))
			if float( (datatemp[4]))<self.TEMPO_MIN:
				self.TEMPO_MIN = float( (datatemp[4]))
		print "done. Loaded=",len(self.songs)

class SongSimilarity:
	def __init__(self, shared_data):
		self.LYRIC_CUTOFF = shared_data.LYRIC_CUTOFF
		self.TAG_CUTOFF = shared_data.TAG_CUTOFF
		self.songs = shared_data.songs
		self.LOUDNESS_MAX = shared_data.LOUDNESS_MAX
		self.LOUDNESS_MIN = shared_data.LOUDNESS_MIN
		self.TEMPO_MAX = shared_data.TEMPO_MAX
		self.TEMPO_MIN = shared_data.TEMPO_MIN

	def year_equal(self, y1, y2):
		if y1 == 0 or y2 == 0:
			return 0.0
		elif (y1 - 1900) / 10 == (y2 - 1900) / 10:
			return 1.0
		else:
			return 0.0

	def shared_element_count(self, list1, list2):
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

	def calculate_similarity_private(self, data1, data2, loudint, tempoint):
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
		#(energy are all zeros so ignore them)
		score += float(data1[3]) * float(data2[3]) / loudint / loudint
		data1_denom += (float(data1[3]) / float(loudint)) ** 2.0
		data2_denom += (float(data2[3]) / float(loudint)) ** 2.0

		score += float(data1[4]) * float(data2[4]) / tempoint / tempoint
		data1_denom += (float(data1[4]) / float(tempoint )) ** 2.0
		data2_denom += (float(data2[4]) / float(tempoint )) ** 2.0

		# year will also be a binary feature
		year1 = int(data1[5].strip())
		year2 = int(data2[5].strip())
		score += self.year_equal(year1, year2)

		if year1 > 0:
			data1_denom += 1.0
		if year2 > 0:
			data2_denom += 1.0
		
		# lyrics are also binary
		lyric_score = float(self.shared_element_count(data1[6], data2[6]))
		score += lyric_score / float(self.LYRIC_CUTOFF)
		
		if len(data1[6]) == 0 or len(data2[6]) == 0:
			data1_denom += 1.0;
			data2_denom += 1.0;
		else:
			data1_denom += float(len(data1[6])) / float(self.LYRIC_CUTOFF)
			data2_denom += float(len(data2[6])) / float(self.LYRIC_CUTOFF)
		
		# tags are also binary
		tag_score = float(self.shared_element_count(data1[7], data2[7]))
		score += tag_score / float(self.TAG_CUTOFF)
		
		if len(data1[7]) == 0 or len(data2[7]) == 0:
			data1_denom += 1.0;
			data2_denom += 1.0;
		else:
			data1_denom += float(len(data1[7])) / float(self.TAG_CUTOFF)
			data2_denom += float(len(data2[7])) / float(self.TAG_CUTOFF)
		
		result_val = score / float(math.sqrt(data1_denom) * math.sqrt(data2_denom))
		return result_val

	def calculate_similarity(self, id1, id2):
		try:
			s1 = self.songs[id1]
			s2 = self.songs[id2]
		except:
			print("something wrong %d, %d\n" %(id1, id2));
		loudness_range = self.LOUDNESS_MAX - self.LOUDNESS_MIN
		tempo_range = self.TEMPO_MAX - self.TEMPO_MIN
		return self.calculate_similarity_private(s1, s2, loudness_range, tempo_range)
