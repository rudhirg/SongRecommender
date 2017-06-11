import operator
import pdb

TOP_X = 10

songs = {}

f = open("../data/users_30000.train")
line = f.readline()

while line != "":
	line_split = line.split("-");
	items = line_split[1].split()
	for item in items:
		item_split = item.split(":")
		songid, playcount = item_split[0].strip(), int(item_split[1].strip())
		if songs.has_key(songid):
			songs[songid] += playcount
		else:
			songs[songid] = playcount
	line = f.readline()
f.close()

topSongs = sorted(songs.iteritems(), key=operator.itemgetter(1), reverse=True)
topSongs = [int(s[0]) for s in topSongs]

f = open("../data/users_30000_10000.test")
line = f.readline()

totalPrec = 0.0
totalCounted = 0.0
while line != "":       #for each test user
        line_split = line.split("-");
        items = line_split[1].split()

        cutoff = 100;
        AvgPrec = 0.0;
        NumRelSongs = min(cutoff, len(items));

        numCount = 0;
        matches = 0.0
        user_songs = []
        for item in items:
                item_split = item.split(":")
                songid, playcount = int(item_split[0].strip()), int(item_split[1].strip())
                user_songs.append(songid)
        for song in topSongs:
                M_yk = 0;
                numCount += 1;
                if user_songs.count(song) > 0:
                        matches += 1.0
                        M_yk = 1;

                prec_k = matches/numCount;
                AvgPrec += (prec_k * M_yk);

                if( numCount >= cutoff ):
                        break;
        #totalPrec += matches / float(TOP_X)
        totalCounted += 1.0
        if NumRelSongs > 0:
                AvgPrec = AvgPrec/NumRelSongs;
        else:
                AvgPrec = 0;
        totalPrec += AvgPrec;        
        line = f.readline()

f.close()

print totalPrec / totalCounted
