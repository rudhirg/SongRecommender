from __future__ import division
import sys
from scipy.sparse import *
from scipy.sparse import lil_matrix
import numpy
from sparsesvd import sparsesvd
import pdb
import operator;
import math;
import thread;
import threading;
import time;
import signal
import sys

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

gResultsFileName = "results.txt";
gResultsFile = None;
gTrainingUsers = {};
gTrainingItems = {};
gTrainingNonZeroElems = 0;  # number to know the total number of non zero elements in the user-song matrix
gSparseMatrix = None;
gNumSongs = 0;

gUserFeatMatrix = None;     # left singular matrix
gSongFeatMatrix = None;     # right singular matrix
gUserSongFeatMatrix = None;     # dot product of right left singular matrix

class User:
    m_origUserId = 0;       # original user id
    m_userId = 0;           # mapped user id
    m_features = {}; # ductionary - songId as key, weight as vals
    m_featuresTest = {}; # ductionary - songId as key, weight as vals

    def __init__(self):
        self.m_origUserId = 0;
        self.m_userId = 0;
        self.m_features = {};
        self.m_featuresTest = {};

class Item:
    m_origItemId = 0;      
    m_itemId = 0;          
    m_users = {}; 
    m_usersTest = {}; 

    def __init__(self):
        self.m_origItemId = 0;
        self.m_itemId = 0;
        self.m_users = {};
        self.m_usersTest = {};

def ParseUserData(fileName, bTestdata):
    userFile = open(fileName, 'r');
    lines = [];
    userMapId = 0;

    for line in userFile:
        ParseUser(line, bTestdata, userMapId);
        userMapId += 1;

def ParseUser(data, bTestdata, userMapId):
    global gTrainingNonZeroElems;
    global gNumSongs;
    
    [userId, userData] = data.split('-');
    userId = userId.strip();
    userData = userData.strip();
    #print userId, ':', userData;

    user = 0;
    if( bTestdata == False ):
        user = User();
        user.m_origUserId = int(userId);
        user.m_userId = userMapId;
    else:
        user = gTrainingUsers[int(userId)];        

    features = userData.split();
    for feature in features:
        
        if( bTestdata == False ):
            [songId, weight] = feature.split(':');
            songId = int(songId);
            weight = int(weight);
            gNumSongs = max(gNumSongs, int(songId));
            user.m_features[int(songId)] = int(weight);
            gTrainingNonZeroElems += 1;

            item = 0;
            # add in items hash
            if( gTrainingItems.has_key( songId ) == False ):
                item = Item();
                item.m_itemId = songId;
                gTrainingItems[int(songId)] = item;
            item = gTrainingItems[songId];
            item.m_users[int(userId)] = 1;
            
        else:
            songId = feature
            user.m_featuresTest[int(songId)] = int(0);

    if( bTestdata == False ):
        gTrainingUsers[int(userId)] = user;

# finds similarity between query user and related user
def GetUserSimilarityWeight(qUser, relUser, alpha):
    #similarity is P(qUser|relUser)*P(relUser|qUser) = I(u)AI(v)/(I(u)^alpha)*(I(v)^(1-alpha)) = (#common items)/(#items in quser)^alpha*(#items in reluser)
    #TODO: generalize over alpha

    numQItems = 0;
    numRItems = 0;
    numCommonItems = 0;
    items = {};

    for qitem in qUser.m_features.iterkeys():   # finds the common items
        items[qitem] =1;
        numQItems += 1;

    for ritem in relUser.m_features.iterkeys():
        numRItems += 1;
        if( items.has_key(ritem) ):
            numCommonItems += 1;
    
    return numCommonItems/(pow(numQItems, alpha) * pow(numRItems, 1.0-alpha));

def GetSongSimilarityWeight(qItem, relItem, alpha):
    #similarity is P(qsong|relSong)*P(relSong|qSong) = I(u)AI(v)/(I(u)^alpha)*(I(v)^(1-alpha)) = (#common items)/(#items in quser)^alpha*(#items in reluser)
    #TODO: generalize over alpha

    numQUsers = 0;
    numRUsers = 0;
    numCommonUsers = 0;
    users = {};

    for quser in qItem.m_users.iterkeys():   # finds the common items
        users[quser] =1;
        numQUsers += 1;

    for ruser in relItem.m_users.iterkeys():
        numRUsers += 1;
        if( users.has_key(ruser) ):
            numCommonUsers += 1;
    
    return numCommonUsers/(pow(numQUsers, alpha) * pow(numRUsers, 1.0-alpha));    

                
#calculates the user based similarity for items
def GetUserBasedRecommendations(user, alpha):

    #find the similarity with all users as preprocessing step
    UserSim = {};
    for relUid in gTrainingUsers.iterkeys():
        if( relUid == user.m_userId ):
            continue;
        relUser = gTrainingUsers[relUid];
        Wuv = GetUserSimilarityWeight(user, relUser, alpha);
        UserSim[relUid] = Wuv;

    rankVect = {};
    for itemId in gTrainingItems.iterkeys():    #for every song, find the recommendation weights for this song
        if (user.m_features.has_key(itemId) == True):
            continue;
        
        item = gTrainingItems[itemId];
        itemWeight = 0.0;

        for relUid in item.m_users.iterkeys():  # for every related user who have listened to item
            if( relUid == user.m_userId ):
                continue;
            relUser = gTrainingUsers[relUid];
            #Wuv = GetUserSimilarityWeight(user, relUser, alpha);
            Wuv = UserSim[relUid];
            itemWeight += Wuv;

        rankVect[itemId] = itemWeight;

    print ("User: %d - done\n" % (user.m_userId));
    # sort songs and get ranks for each song and find precision
    rankVectSorted  = sorted(rankVect.iteritems(), key=operator.itemgetter(1), reverse=True);
    return rankVectSorted;

def GetItemBasedRecommendations(user, alpha):

    #find the similarity with all users as preprocessing step
    rankVect = {};
    for relSid in gTrainingItems.iterkeys():
        Wuv = 0.0;
        relItem = gTrainingItems[relSid];
        for i in user.m_features.iterkeys():
            if( relSid == i ):
                continue;
            item = gTrainingItems[i];
            Wuv += GetSongSimilarityWeight(item, relItem, alpha);
        rankVect[relSid] = Wuv;
            
    print ("Item: %d - done\n" % (user.m_userId));
    # sort songs and get ranks for each song and find precision
    rankVectSorted  = sorted(rankVect.iteritems(), key=operator.itemgetter(1), reverse=True);
    return rankVectSorted;
                
def CalculatePrecision(user, rankVectSorted):
    #get the top ten songs
    cutoff = 100;
    AvgPrec = 0.0;
    NumRelSongs = min(cutoff, len(user.m_featuresTest));
    
    numTopSongs = 10;
    numCount = 0;
    numGood = 0;    #num song in test data too

    for s in range(0, len(rankVectSorted)):
        sid = rankVectSorted[s][0];
        weight = rankVectSorted[s][1];

        if( user.m_features.has_key(sid) == False ):
            numCount = numCount + 1;
            M_yk = 0;
            if( user.m_featuresTest.has_key(sid) == True ):
                numGood = numGood + 1;
                M_yk = 1;
                
            prec_k = numGood/numCount;
            AvgPrec += (prec_k * M_yk);
            
        if( numCount >= cutoff ):
            break;

    if NumRelSongs > 0:
        AvgPrec = AvgPrec/NumRelSongs;
    else:
        AvgPrec = 0;
    #print 'uid: ', user.m_userId, ' Precision = ', numGood/10.0, '\n';
    return AvgPrec;

def WriteRecToFile(user, itemVecSorted, recFile):
    recFile.write("%d -" % (user.m_userId));
    Len = min(len(itemVecSorted), 150);
    for i in range(0, len(itemVecSorted)):
        recFile.write(" %d:%f" % (itemVecSorted[i][0], itemVecSorted[i][1]));
    recFile.write("\n");
    recFile.flush();

def CalculateMeanAveragePrecision(userList, startIndx, unitLen, alpha, recFileName):
    numCount = 0;
    totalPrec = 0.0;
    #recFile = open(recFileName, 'w');

    for i in range(startIndx, startIndx+unitLen):
        uid = userList[i];
        user = gTrainingUsers[uid];
        #itemVecSorted = GetUserBasedRecommendations(user, alpha);
        itemVecSorted = GetItemBasedRecommendations(user, alpha);
        totalPrec += CalculatePrecision(user, itemVecSorted);
        #write the ranked songs for the user in a file
        #WriteRecToFile(user, itemVecSorted, recFile);
        numCount = numCount + 1;
        if( numCount%1000 == 0):
            print "User: ", uid;

    #recFile.close();
    return totalPrec;

class SimThread(threading.Thread):
     def __init__(self,  userList, startIndx, unitLen, alpha, recFileName):
         threading.Thread.__init__(self);
         self.userList=userList;
         self.startIndx=startIndx;
         self.unitLen=unitLen;
         self.alpha=alpha;
         self.precision = 0;
	 self.recFileName = recFileName;
         return;

     def run(self):
         print("Thread starting, indx: %d, len: %d\n" % (self.startIndx, self.unitLen));
         self.precision = CalculateMeanAveragePrecision(self.userList, self.startIndx, self.unitLen, self.alpha, self.recFileName);
         return;
         

def RunThreads(alpha, datalen, headline):
    userList = gTrainingUsers.keys();
    Len = len(userList);
    startIndx = 0;
    maxLen = datalen;   #max length of data for each thread

    threadList = [];

    while(True):
        if( startIndx >= Len ):
            break;
        recFileName = "user_reco_" + headline + "_" + str(alpha) + "_" + str(startIndx) + ".txt";
        unitLen = min(Len-startIndx, maxLen);
        t = SimThread( userList, startIndx, unitLen, alpha, recFileName);
        t.daemon = True;
        t.start();
        threadList.append(t);
        startIndx = startIndx + unitLen;

    print("waiting for threads\n");
    main_thread = threading.currentThread();

    try:
        for t in threading.enumerate():
            if t is main_thread:
                continue;
            t.join();
    except (KeyboardInterrupt, SystemExit):
        print "interruped\n";
        sys.exit();

    print("All threads done\n");

    totalPrec = 0.0;
    for i in range(0, len(threadList)):
        totalPrec += threadList[i].precision;

    print 'Avg Precision: ', totalPrec/Len, '\n';
    gResultsFile.write("alpha: %f, precision: %f\n" % (alpha, totalPrec/Len));
    gResultsFile.flush();

def main(argv):
    global gResultsFile;
    alpha = 0.5;
    datalen = 5000;
    headline = "similarity";

    if(len(sys.argv) > 3):
        alpha = float(sys.argv[1]);
        datalen = int(sys.argv[2]);
        headline = sys.argv[3];

    print("starting sim with alpha: %f, datalen: %d\n" % (alpha, datalen));
    ParseUserData('../data/user_train.txt', False);
    ParseUserData('../data/user_test.txt', True);
    print("Data Parsed\n");

    gResultsFile = open(gResultsFileName, 'a');
    
    RunThreads(alpha, datalen, headline);
    #CalculateMeanAveragePrecision(alpha);
    gResultsFile.close();
    

if __name__ == "__main__":
    try:
        main(sys.argv);
    except KeyboardInterrupt:
        sys.exit();



