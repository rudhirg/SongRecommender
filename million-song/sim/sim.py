from __future__ import division
import sys
from scipy.sparse import *
from scipy.sparse import lil_matrix
import numpy
from sparsesvd import sparsesvd
import pdb
import operator;
import math;

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

    print("user preprocessing done\n");

    rankVect = {};
    for itemId in gTrainingItems.iterkeys():    #for every song, find the recommendation weights for this song
        if (user.m_features.has_key(itemId) == True):
            continue;
        
        item = gTrainingItems[itemId];
        itemWeight = 0.0;

        for relUid in item.m_users.iterkeys():  # for every related user who have listened to item
            relUser = gTrainingUsers[relUid];
            #Wuv = GetUserSimilarityWeight(user, relUser, alpha);
            Wuv = UserSim[relUid];
            itemWeight += Wuv;

        rankVect[itemId] = itemWeight;

    print ("User: %d - done\n" % (user.m_userId));
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

def CalculateMeanAveragePrecision(alpha):
    numCount = 0;
    totalPrec = 0.0;
    topTenMostPlayed = None;

    for uid in gTrainingUsers.iterkeys():
        user = gTrainingUsers[uid];
        itemVecSorted = GetUserBasedRecommendations(user, alpha);
        totalPrec += CalculatePrecision(user, itemVecSorted);
        numCount = numCount + 1;
        if( numCount%1000 == 0):
            print "User: ", uid;

    print 'Avg Precision: ', totalPrec/numCount, '\n';
    gResultsFile.write("alpha: %f, precision: %f\n" % (alpha, totalPrec/numCount));
    gResultsFile.flush();


def main(argv):
    global gResultsFile;
    alpha = 0.5;

    if(len(sys.argv) > 1):
        alpha = float(sys.argv[1]);

    print("starting sim with alpha: %f\n" % (alpha));
    ParseUserData('../data/users_40000.train', False);
    ParseUserData('../data/users_40000.test', True);
    print("Data Parsed\n");

    gResultsFile = open(gResultsFileName, 'a');

    CalculateMeanAveragePrecision(alpha);
    gResultsFile.close();


if __name__ == "__main__":
    main(sys.argv)    



