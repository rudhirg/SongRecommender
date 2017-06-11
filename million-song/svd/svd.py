import sys
from scipy.sparse import *
from scipy.sparse import lil_matrix
import numpy
from sparsesvd import sparsesvd
import pdb
import operator;

trainFilename = "../data/user_train.txt"
testFilename = "../data/user_test.txt"
#filename = "user_train.txt"

gTrainingUsers = {};
gTrainingNonZeroElems = 0;  # number to know the total number of non zero elements in the user-song matrix
gSparseMatrix = None;

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

def ParseUserData(fileName, bTestdata):
    userFile = open(fileName, 'r');
    lines = [];
    userMapId = 0;

    for line in userFile:
        ParseUser(line, bTestdata, userMapId);
        userMapId += 1;

def ParseUser(data, bTestdata, userMapId):
    global gTrainingNonZeroElems;
    
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
            user.m_features[int(songId)] = int(weight);
            gTrainingNonZeroElems += 1;
        else:
            songId = feature
            user.m_featuresTest[int(songId)] = int(0);

    if( bTestdata == False ):
        gTrainingUsers[int(userId)] = user;

#builds the sparse matrix of user-song
def extract_CRCSparseMatrix():
    global gSparseMatrix;
    
    gSparseMatrix = numpy.empty((3, gTrainingNonZeroElems + 1));
    numEle = 0;
    
    for uid in gTrainingUsers.iterkeys():
        user = gTrainingUsers[uid];
        gSparseMatrix[0][numEle] = user.m_userId;   #rows
        for sid in user.m_features.iterkeys():
            playcount = user.m_features[sid];
            gSparseMatrix[1][numEle] = sid;   #cols
            gSparseMatrix[2][numEle] = playcount;   #data
            numEle += 1;

def DoSVD(topK):
    global gUserFeatMatrix;
    global gSongFeatMatrix;
    
    print "Starting Matrix Factorization...\n";
    sparseMat = csc_matrix( (gSparseMatrix[2, :], (gSparseMatrix[0, :], gSparseMatrix[1, :])) );
    (gUserFeatMatrix, Sigma, gSongFeatMatrix) = sparsesvd(sparseMat, topK);
    
    # calculate dot product of right and left singular matrix
    pdb.set_trace();
    #gUserSongFeatMatrix = numpy.dot(gUserFeatMatrix.T, gSongFeatMatrix);
    print "Matrix Factorization Finished\n";

def Rank(user):
    #userSongs = gUserSongFeatMatrix[user.m_userId, :];
    #numSongs = gUserSongFeatMatrix.shape[1];
    userSongs = numpy.dot((gUserFeatMatrix.T)[user.m_userId, :], gSongFeatMatrix);
    numSongs = userSongs.shape[0];
    rankVect = {};

    print "User: ", user.m_userId;    
    for i in range(0, numSongs):
        sid = i+1;
        rankVect[sid] = userSongs[i];
    
    #sort rank vect
    rankVectSorted  = sorted(rankVect.iteritems(), key=operator.itemgetter(1), reverse=True);

    return CalculatePrecision(user, rankVectSorted);

def CalculatePrecision(user, rankVectSorted):
    #get the top ten songs
    numTopSongs = 10;
    numCount = 0;
    numGood = 0;    #num song in test data too

    for s in range(0, len(rankVectSorted)):
        sid = rankVectSorted[s][0];
        weight = rankVectSorted[s][1];

        if( user.m_features.has_key(sid) == False ):
            numCount = numCount + 1;
            if( user.m_featuresTest.has_key(sid) == True ):
                numGood = numGood + 1;
        #else:
        #    print 'songID: ', sid, ' weight: ', weight, ' Already Present\n';
        if( numCount >= numTopSongs ):
            break;

    #print 'uid: ', user.m_userId, ' Precision = ', numGood/10.0, '\n';
    #pdb.set_trace();
    return numGood/10.0;

def CalculateAveragePrecisionAtTen():
    numCount = 0;
    totalPrec = 0.0;
    topTenMostPlayed = None;

    for uid in gTrainingUsers.iterkeys():
        user = gTrainingUsers[uid];
        totalPrec += Rank(user);
        numCount = numCount + 1;

    print 'Avg Precision: ', totalPrec/numCount, '\n';
    

def main(argv):
    ParseUserData('../data/user_train.txt', False);
    ParseUserData('../data/user_test.txt', True);

    extract_CRCSparseMatrix();
    DoSVD(70);
    CalculateAveragePrecisionAtTen();


if __name__ == "__main__":
    main(sys.argv)    



