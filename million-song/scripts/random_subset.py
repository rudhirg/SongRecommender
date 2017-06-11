from __future__ import division;
import random;

k = 40000;
lines = [];

fin = open("../data/user_song_counts_full.train");

linect = 1;
line = fin.readline();

print "Picking lines..."
while line != "":
	pr = random.random();
	Pr = k/linect;
	if pr <= Pr:
		if len(lines) < k:
			lines.append(line);
		else:
			#print "  Updating with", linect,"-->",pr,"<",Pr;
			lines[random.randint(0, k-1)] = line;

	line = fin.readline();
	linect += 1;
fin.close();
print "Done.";

print "Writing... ";
fout = open("../data/user_song_counts_%d.train" % (k), "w");
for l in lines:
	fout.write(l.strip()+"\n");
fout.close();
print "Done.";
