import sqlite3
import unicodedata

STOP_WORDS = [\
'a', \
'able', \
'about', \
'across', \
'after', \
'all', \
'almost', \
'also', \
'am', \
'among', \
'an', \
'and', \
'any', \
'are', \
'as', \
'at', \
'be', \
'because', \
'been', \
'but', \
'by', \
'can', \
'cannot', \
'could', \
'dear', \
'did', \
'do', \
'does', \
'either', \
'else', \
'ever', \
'every', \
'for', \
'from', \
'get', \
'got', \
'had', \
'has', \
'have', \
'he', \
'her', \
'hers', \
'him', \
'his', \
'how', \
'however', \
'i', \
'if', \
'in', \
'into', \
'is', \
'it', \
'its', \
'just', \
'least', \
'let', \
'like', \
'likely', \
'may', \
'me', \
'might', \
'most', \
'must', \
'my', \
'neither', \
'no', \
'nor', \
'not', \
'of', \
'off', \
'often', \
'on', \
'only', \
'or', \
'other', \
'our', \
'own', \
'rather', \
'said', \
'say', \
'says', \
'she', \
'should', \
'since', \
'so', \
'some', \
'than', \
'that', \
'the', \
'their', \
'them', \
'then', \
'there', \
'these', \
'they', \
'this', \
'tis', \
'to', \
'too', \
'twas', \
'us', \
'wants', \
'was', \
'we', \
'were', \
'what', \
'when', \
'where', \
'which', \
'while', \
'who', \
'whom', \
'why', \
'will', \
'with', \
'would', \
'yet', \
'you', \
'your' \
]

WORD_COUNT_SQL = "SELECT word, count FROM lyrics WHERE track_id='%s' AND word NOT IN ('" + "','".join(STOP_WORDS) + "')"

DEBUG_MAX = 500

def get_words_for_ids(fout, ids, cursor):
	for msid in ids:
		cursor.execute(WORD_COUNT_SQL % msid)
		results = cursor.fetchall()
		output = msid + "\t"
		for row in results:
			lyric = "_"
			lyric += unicodedata.normalize('NFKD',row[0]).encode('ascii','ignore')
			output += "%s:%s," % (lyric,str(row[1]))
		fout.write(output.strip(",")+"\n")

def execute(cursor, fname):
	out = open(fname, "w")

	print "Getting distinct track IDs...",
	cursor.execute("SELECT DISTINCT track_id FROM lyrics")# limit 1,"+str(DEBUG_MAX))
	results = cursor.fetchall()
	print "done.\n"

	processed = 0
	count = 1
	id_list = []
	for row in results:
		id_list.append(row[0])
		if count % DEBUG_MAX == 0:
			print "Processing IDs %d to %d" % (count - DEBUG_MAX, count),
			get_words_for_ids(out, id_list, cursor)
			processed += len(id_list)
			id_list = []
			print "done."
		count += 1
	
	get_words_for_ids(out, id_list, cursor)
	processed += len(id_list)
	out.close()
	print "Processed %d of %d" % (processed, len(results))

conn = sqlite3.connect('data/mxm_dataset.db')
execute(conn.cursor(), 'out/lyrics.txt')

