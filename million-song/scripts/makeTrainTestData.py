import math;
fin = open("../data/user_song_counts_40000.train");

trainFile = open("../data/users_40000.train", "w");
testFile = open("../data/users_40000.test", "w");

for line in fin:
        [userId, userData] = line.split('-');
        userId = userId.strip();
        userData = userData.strip();

        features = userData.split();

        trainFile.write("%s -" % (userId));
        for i in range(0, math.ceil(len(features)/2) ):
                feature = features[i];
                trainFile.write(" %s" % (feature));
        trainFile.write("\n");

        testFile.write("%s -" % (userId));
        for i in range( math.ceil(len(features)/2), len(features) ):
                feature = features[i];
                [songId, weight] = feature.split(':');
                testFile.write(" %s" % (songId));
        testFile.write("\n");
                
fin.close();
trainFile.close();
testFile.close();





