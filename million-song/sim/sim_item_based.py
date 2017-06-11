from __future__ import division
import sys
from scipy.sparse import *
from scipy.sparse import lil_matrix
import numpy
import pdb
import operator;
import math;
import thread;
import threading;
import time;
import signal
import sys
import multiprocessing;
import Queue;
import random;
import heapq;
import os.path;
from song_similarity_module import SongSimilarity, SongSimilaritySharedData

def signal_handler(signal, frame):
	print 'You pressed Ctrl+C!'
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

gResultsFileName = "results.txt";
gResultsFile = None;

gItemSimMat = {};
gMostPopItems = {};

gTrainingUsers = {};
gTestingUsers = {};
gTrainingItems = {};
gTestingItems = {};
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
		user = User();
		user.m_origUserId = int(userId);
		user.m_userId = userMapId;

	features = userData.split();
	featLen = len(features);
	clen = 0;
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
			[songId, weight] = feature.split(':');
			songId = int(songId);
			weight = int(weight);
			gNumSongs = max(gNumSongs, int(songId));

			item = 0;
			# add in items hash
			if( gTrainingItems.has_key( songId ) == False ):
				item = Item();
				item.m_itemId = songId;
				gTrainingItems[int(songId)] = item;
			item = gTrainingItems[songId];

			if( 2*clen < featLen):
				user.m_features[int(songId)] = int(weight);
				gTrainingNonZeroElems += 1;
				item.m_users[int(userId)] = 1;
			else:
				user.m_featuresTest[int(songId)] = int(weight);
				gTrainingNonZeroElems += 1;

		clen += 1;

	if( bTestdata == False ):
		gTrainingUsers[int(userId)] = user;
	else:
		gTestingUsers[int(userId)] = user;

def ParseItemSimilarityFile(fileName):
	print("Parsing song sim file : %s\n" % (fileName));
	itemFile = open(fileName, 'r');
	lines = [];
	itemMapId = 0;

	for line in itemFile:
		[itemId, itemData] = line.split('-');
		itemId = itemId.strip();
		itemData = itemData.strip();

		itemList = [];
		features = itemData.split();
		for feature in features:
			[songId, weight] = feature.split(':');
			songId = int(songId);
			weight = float(weight);	

			itemList.append((songId, weight));
			
		gItemSimMat[int(itemId)] = itemList;


def SampleMostPopularSongs():
	N = 5000;

	# create dict of songs with their number of users count
	songUserCount = {};
	for itemId in gTrainingItems.iterkeys():
		item = gTrainingItems[itemId];
		songUserCount[itemId] = len(item.m_users);

	# sort
	rankVectSorted = {};
	rankVectSorted  = sorted(songUserCount.iteritems(), key=operator.itemgetter(1), reverse=True);

	print("Total Songs: %d\n" % (len(rankVectSorted)));

	# create a dict of most popular N songs
	for i in range(0, min(len(rankVectSorted), N)):
		[itemId, count] = rankVectSorted[i];
		gMostPopItems[itemId] = count;

	
def BuildItemSimilarityMatrix(alpha, gamma):
	#pdb.set_trace();
	k = 100;	# k most similar songs

	SampleMostPopularSongs();

	iter = 0;
	mostPopItemsList = gMostPopItems.keys();
	for itemId in mostPopItemsList:
		iter += 1;
		ranking_list = [];
		item = gTrainingItems[itemId];
		for compItemId in mostPopItemsList:
			if itemId == compItemId:
				continue;
			compItem = gTrainingItems[compItemId];
			w = GetSongSimilarityWeight(item, compItem, alpha, gamma);
			ranking_list.append((w, compItemId));
		ranking = heapq.nlargest(k, ranking_list);

		gItemSimMat[itemId] = ranking;

		#pdb.set_trace();
		if iter%1 == 0:
			print("Build item sim matrix iter - %d\n" % (iter));

def GetSongSimilarityWeight(qItem, relItem, alpha, gamma):
	#similarity is P(qsong|relSong)*P(relSong|qSong) = I(u)AI(v)/(I(u)^alpha)*(I(v)^(1-alpha)) = (#common items)/(#items in quser)^alpha*(#items in reluser)
	#TODO: generalize over alpha

	numQUsers = 0;
	numRUsers = 0;
	numCommonUsers = 0;
	users = {};

	for quser in qItem.m_users.iterkeys():   # finds the common items
		if( gTestingUsers.has_key(quser) == True):  # get rid of testing users
			continue;
		users[quser] =1;
		numQUsers += 1;

	for ruser in relItem.m_users.iterkeys():
		if( gTestingUsers.has_key(ruser) == True):  # get rid of testing users
			continue;
		numRUsers += 1;
		if( users.has_key(ruser) ):
			numCommonUsers += 1;
#	print("number of user items compared: %d - %d\n" % (numQUsers, numRUsers));
	denom = (pow(numQUsers, alpha) * pow(numRUsers, 1.0-alpha));
	sim = 0.0;
	if( denom != 0.0 ):
		sim = numCommonUsers/denom;    
	return pow( sim, gamma );

def GetItemBasedRecommendations(user):

	# find the k sim items for each of user songs and remove duplicates and already listened user songs
	rankVect = {};
	userItemDict = {};
	for itemId in user.m_features.iterkeys():
		if gItemSimMat.has_key(itemId) == False:
			continue;
		itemList = gItemSimMat[itemId];
		for tup in itemList:
			[simItemId, w] = tup;
			if userItemDict.has_key(simItemId) == True:
				continue;
			if user.m_features.has_key(simItemId) == True:
				continue;
			userItemDict[simItemId] = w;
			#pdb.set_trace();

	#pdb.set_trace();
	# find the weight for each to be recommeded song by calc sim with each of users already listened songs
	for itemId in userItemDict.iterkeys():
		itemList = gItemSimMat[itemId];
		Wuv = 0.0;
		item = gTrainingItems[itemId];
		for userItemId in user.m_features.iterkeys():
			userItem = gTrainingItems[userItemId];
			for tup in itemList:
				[simItemId, w] = tup;
				if(simItemId != userItemId):
					continue;
				Wuv += w;
				break;
			rankVect[itemId] = Wuv;	

	#pdb.set_trace();
    	#print ("Item: %d - done\n" % (user.m_userId));
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

	#pdb.set_trace();
	if NumRelSongs > 0:
		AvgPrec = AvgPrec/NumRelSongs;
	else:
		AvgPrec = 0;
	#print 'uid: ', user.m_userId, ' Precision = ', numGood/10.0, '\n';
	return AvgPrec;

def CalculateMeanAveragePrecision():
	numCount = 0;
	totalPrec = 0.0;
	recFile = open("UserRecommendation_20000.txt", "w");
	userList = gTestingUsers.keys();
	for i in range(0, len(userList)):
		uid = userList[i];
		user = gTestingUsers[uid];
		#itemVecSorted = GetUserBasedRecommendations(user, alpha);
		itemVecSorted = GetItemBasedRecommendations(user);
		totalPrec += CalculatePrecision(user, itemVecSorted);
		#write the ranked songs for the user in a file
		#WriteRecToFile(user, itemVecSorted, recFile);
		WriteResultToFile(user, itemVecSorted, recFile);
		numCount = numCount + 1;
		if( i%40 == 0):
			print ("User: %d, %d, %f\n" % (uid, i, totalPrec));

	#recFile.close();
	return totalPrec/numCount;

def WriteResultToFile(user, itemVecSorted, recFile):
	recFile.write("%d -" % (user.m_userId));
        Len = min(len(itemVecSorted), 100);
        for i in range(0, len(itemVecSorted)):
                recFile.write(" %d:%f" % (itemVecSorted[i][0], itemVecSorted[i][1]));
	recFile.write("\n");
	#recFile.flush();

def main(argv):
	global gResultsFile;
	datafile = "";

	if(len(sys.argv) > 1):
		datafile = sys.argv[1];

	print("starting sim with file: %s\n" % (datafile));
	ParseUserData('../data/users_30000.train', False);
	ParseUserData('../data/users_30000_10000.test', True);

	# parse every data file (similarity file)
	count = 1;
	while True:
		filename = datafile + '_' + str(count) + '.txt';
		if os.path.isfile(filename) == False:
			break;

		ParseItemSimilarityFile(filename);
		count += 1;

	print("Data Parsed\n");
	print("Calculating Item similarity...\n");
	#BuildItemSimilarityMatrix(alpha, gamma);
	precision = CalculateMeanAveragePrecision();
	print("Item similarity calculated\n");

	gResultsFile = open(gResultsFileName, 'a');

	print 'Avg Precision: ', precision, '\n';
	gResultsFile.write("Item based recommendation, file: %s, precision: %f\n" % (datafile, precision));
	gResultsFile.flush();

	#RunThreads(alpha, datalen, headline, gamma);
	#CalculateMeanAveragePrecision(alpha);
	gResultsFile.close();
	

if __name__ == "__main__":
	try:
		main(sys.argv);
	except KeyboardInterrupt:
		sys.exit();
