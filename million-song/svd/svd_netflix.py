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
gTestingUsers = {};
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
        user = User();
        user.m_origUserId = int(userId);
        user.m_userId = userMapId;

    features = userData.split();
    featLen = len(features);
    clen = 0;
    for feature in features:
        
        if( bTestdata == False ):
            [songId, weight] = feature.split(':');
            gNumSongs = max(gNumSongs, int(songId));
            user.m_features[int(songId)] = int(weight);
            gTrainingNonZeroElems += 1;
        else:
            [songId, weight] = feature.split(':');
            gNumSongs = max(gNumSongs, int(songId));

            if( 2*clen < featLen):
                user.m_features[int(songId)] = int(weight);
                gTrainingNonZeroElems += 1;
            else:
                user.m_featuresTest[int(songId)] = int(weight);

        clen += 1;
                

    # half of the songs in the test data would be used for training
    # thus test data is both in training and test
    if( bTestdata == False ):
        gTrainingUsers[int(userId)] = user;
    else:
        gTrainingUsers[int(userId)] = user;
        gTestingUsers[int(userId)] = user;

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

def DoSVD(lrate, ugamma, dim):
    global gUserFeatMatrix;
    global gSongFeatMatrix;
    
    print "Starting Matrix Factorization...\n";
    #pdb.set_trace();

    k = dim;
    rate = lrate;
    gamma = ugamma;
    epsilon = 0.001;

    avgErr = avgErr_last = 2.0;
    
    #initialize
    gUserFeatMatrix = 0.1*numpy.ones((len(gTrainingUsers), k));
    gSongFeatMatrix = 0.1*numpy.ones(( gNumSongs+1, k ));

    # for all the features to calculate
    for iter in range(0, k):
        epoch = 0;
        errSq_prev = 0;
        decreasing = 0;
        
        while( epoch < 50 or avgErr <= (avgErr_last - epsilon) ):
            epoch += 1;
            errSq = 0;
            avgErr_last = avgErr;

            # for all non zero entries
            for i in range( 0, gSparseMatrix.shape[1] ):
                usr = gSparseMatrix[0, i];
                song = gSparseMatrix[1, i];
                
                realVal = gSparseMatrix[2, i];

                userVec = gUserFeatMatrix[usr, 0: iter+1];
                songVec = gSongFeatMatrix[song, 0: iter+1];

                predictedVal = numpy.dot(userVec, songVec.T);

                error = realVal - predictedVal;
                errSq = errSq + error*error;

                #if( math.isnan(error) or math.isnan(errSq) or math.isnan(predictedVal) or math.isinf(predictedVal) ):
                #    pdb.set_trace();

                gUserFeatMatrix[usr, iter] = gUserFeatMatrix[usr, iter] + rate*( error*gSongFeatMatrix[song, iter] - gamma*gUserFeatMatrix[usr, iter]);
                gSongFeatMatrix[song, iter] = gSongFeatMatrix[song, iter] + rate*( error*gUserFeatMatrix[usr, iter] - gamma*gSongFeatMatrix[song, iter]);

                #if( math.isnan(gUserFeatMatrix[usr, iter]) or math.isnan(gSongFeatMatrix[usr, iter]) ):
                #    pdb.set_trace();

            #pdb.set_trace();
            avgErr = errSq/(float(gSparseMatrix.shape[1]));
            print ("epoch: %d, lrate: %f, errSq: %f\n" % (epoch, rate, errSq));

            if ( (errSq_prev - errSq) < 0 ):
                rate = rate*0.7;
                decreasing = 0;
            else:
                decreasing += 1;
                if( decreasing > 7 ):
                    rate = rate*1.1;
            errSq_prev = errSq;
            
        CalculateMeanAveragePrecision(lrate, gamma, iter+1);

    print "Matrix Factorization Finished\n";

                
def Rank(user):
    #userSongs = gUserSongFeatMatrix[user.m_userId, :];
    #numSongs = gUserSongFeatMatrix.shape[1];
    userSongs = numpy.dot((gUserFeatMatrix)[user.m_userId, :], gSongFeatMatrix.T);
    numSongs = userSongs.shape[0];
    rankVect = {};

    #print "User: ", user.m_userId;    
    for i in range(0, numSongs):
        sid = i+1;
        rankVect[sid] = userSongs[i];
    
    #sort rank vect
    rankVectSorted  = sorted(rankVect.iteritems(), key=operator.itemgetter(1), reverse=True);

    return CalculatePrecision(user, rankVectSorted);

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

def CalculateMeanAveragePrecision(lrate, gamma, dim):
    numCount = 0;
    totalPrec = 0.0;
    topTenMostPlayed = None;

    for uid in gTestingUsers.iterkeys():
        user = gTrainingUsers[uid];
        totalPrec += Rank(user);
        numCount = numCount + 1;
        if( numCount%1000 == 0):
            print "User: ", uid;

    print 'Avg Precision: ', totalPrec/numCount, '\n';
    gResultsFile.write("rate: %f, gamma: %f, dim: %d, precision: %f\n" % (lrate, gamma, dim, totalPrec/numCount));
    gResultsFile.flush();


def main(argv):
    global gResultsFile;
    lrate = 0.01;
    gamma = 0.015;
    dim = 2;

    if(len(sys.argv) >= 3):
        lrate = float(sys.argv[1]);
        gamma = float(sys.argv[2]);
        dim = int(sys.argv[3]);

    print("starting svd with dim: %d, rate: %f, gamma: %f\n" % (dim, lrate, gamma));
    ParseUserData('../data/users_30000.train', False);
    ParseUserData('../data/users_30000_10000.test', True);

    gResultsFile = open(gResultsFileName, 'a');

    extract_CRCSparseMatrix();
    DoSVD(lrate, gamma, dim);
    #CalculateAveragePrecisionAtTen();
    gResultsFile.close();


if __name__ == "__main__":
    main(sys.argv)    



