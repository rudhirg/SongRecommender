fin = open("../data/train_triplets.txt");
fout = open("../data/user_song_counts_full.train", "w");

userMapFile = open("../data/users_map.txt", "w");
songMapFile = open("../data/songs_map.txt", "w");

userMap = {};
songMap = {};

'''
# first read all the song and user id mapping file into hash
userMapFile = open("../data/kaggle_users.txt");
songMapFile = open("../data/kaggle_songs.txt");

ulineNum = 1;
for uline in userMapFile:
        uline = uline.strip();
        userMap[uline] = ulineNum;
        ulineNum = ulineNum + 1;

for sline in songMapFile:
        sline = sline.strip();
        [songGID, songID] = sline.split();
        songMap[songGID] = songID;
        
print "Mapping files read\n";
'''
#reformat
diffSongNum = 0;
diffUserNum = 0;
        
line = fin.readline();
line_count = 1;
diff_users = 0;
last_user = "";
processed = 0;
line_to_write = "";

# Users are blocked out into contiguous chunks... I counted.
while line != "":
	if line != "":
		trip = line.split();
		user = trip[0];

		#get the mapped user and song id
		userId = 0;
		songId = 0;
		if userMap.has_key(user) == False:
			diffUserNum = diffUserNum + 1;
			userMap[user] = diffUserNum;
			userMapFile.write("%s %d\n" % (user, diffUserNum));
		if songMap.has_key(trip[1]) == False:
			diffSongNum = diffSongNum + 1;
			songMap[trip[1]] = diffSongNum;
			songMapFile.write("%s %d\n" % (trip[1], diffSongNum));

		userId = userMap[user];
		songId = songMap[trip[1]];
		
		if last_user != user:
			if last_user != "":
				fout.write(line_to_write.strip() + "\n");
				line_to_write = "";
			#fout.write("%s - %s:%s " % (user, trip[1], trip[2]));
			fout.write("%d - %d:%s " % (userId, songId, trip[2]));
			diff_users += 1;
			last_user = user;
		else:
			line_to_write += "%d:%s " % (songId,trip[2]);
                #line_to_write += "%s:%s " % (trip[1],trip[2]);
		processed += 1;

	line = fin.readline().strip();
	line_count += 1;

if line_to_write != "":
	fout.write(line_to_write.strip());

fin.close();
fout.close();

print "Num lines: ", line_count;
print "User count: ", diff_users;
print "Processed lines: ", processed;





