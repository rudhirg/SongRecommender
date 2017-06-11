import sqlite3
import unicodedata

SQL_FORMAT = "SELECT tags.tag, tid_tag.val FROM tid_tag, tids, tags WHERE tags.ROWID=tid_tag.tag AND tid_tag.tid=tids.ROWID and tids.tid='%s'"

conn = sqlite3.connect("data/lastfm_tags.db")

msd_file = open("out/msd_nodups.txt")
err_file = open("out/mismatched_tracks.txt")
out_file = open("out/tags_nodups.txt", "w")

errs = err_file.readlines()
for i in range(0, len(errs)):
	errs[i] = errs[i].strip() #just in case
err_file.close()

line = msd_file.readline()
output = []
processed = 0
mismatches = 0
tagless = 0

while line != "":
	track = line.split("\t")[0].strip()

	if errs.count(track) == 0:
		data = conn.execute(SQL_FORMAT % track).fetchall()
		out_str = ""

		for row in data:
			out_str +=  unicodedata.normalize('NFKD',row[0]).encode('ascii','ignore')+","+str(row[1])+"\t"

		if out_str == "":
			tagless += 1
		else:
			output.append(track + "\t" + out_str.rstrip("\t")+"\n")
			processed += 1

			if processed % 5000 == 0:
				print "Writing %d to %d" % (processed - 5000, processed)
				out_file.write("".join(output))
				output = []
	else:
		mismatches += 1

	line = msd_file.readline()

if len(output) > 0:
	"Writing last", len(output)
	out_file.write("".join(output))

out_file.close()
msd_file.close()

result = conn.execute("SELECT count(1) FROM (SELECT DISTINCT tid FROM tid_tag)").fetchall()[0]
print "Processed:", processed
print "Tracks with tags:", result[0]
print "Ignored tracks (mismatches):", mismatches
print "Ignored trachs (no tags):", tagless

conn.close()
