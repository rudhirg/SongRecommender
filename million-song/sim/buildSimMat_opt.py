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
from song_similarity_module import SongSimilarity, SongSimilaritySharedData

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

def WriteRecToFile(itemId, itemVecSorted, recFile):
	recFile.write("%d -" % (itemId));
	Len = len(itemVecSorted);
	for i in range(0, len(itemVecSorted)):
		recFile.write(" %d:%f" % (itemVecSorted[i][1], itemVecSorted[i][0]));
	recFile.write("\n");
	recFile.flush();

def SampleMostPopularSongs():
	N = 20000;

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

	
def BuildItemSimilarityMatrix(mostPopItemsList, startIndx, unitLen, alpha, gamma, recFileName, songSimCalculator):
	#pdb.set_trace();
	k = 100;	# k most similar songs

	iter = 0;
	
	for i in range(startIndx, startIndx+unitLen):
	#for itemId in mostPopItemsList:
		itemId = mostPopItemsList[i];
		iter += 1;
		ranking_list = [];
		item = gTrainingItems[itemId];
		for compItemId in mostPopItemsList:
			if itemId == compItemId:
				continue;
			compItem = gTrainingItems[compItemId];
			#w = GetSongSimilarityWeight(item, compItem, alpha, gamma);
			w = songSimCalculator.calculate_similarity(itemId, compItemId);
			ranking_list.append((w, compItemId));
		ranking = heapq.nlargest(k, ranking_list);

		gItemSimMat[itemId] = ranking;

		#pdb.set_trace();
		if iter%100 == 0:
			print("Build item sim matrix iter - %d\n" % (iter));

	recFile = open(recFileName, 'w');
	for itemId in gItemSimMat.iterkeys():
		WriteRecToFile(itemId, gItemSimMat[itemId], recFile);

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
	
	denom = (pow(numQUsers, alpha) * pow(numRUsers, 1.0-alpha));
	sim = 0.0;
	if( denom != 0.0 ):
		sim = numCommonUsers/denom;    
	return pow( sim, gamma );

class SimThread(multiprocessing.Process):
	def __init__(self,  itemList, startIndx, unitLen, alpha, recFileName, gamma, songsimCalc):
		multiprocessing.Process.__init__(self);
		self.itemList=itemList;
		self.startIndx=startIndx;
		self.unitLen=unitLen;
		self.alpha=alpha;
		self.gamma = gamma;
		self.precision = 0;
		self.simCalculator = songsimCalc;
		self.recFileName = recFileName;

	def run(self):
		print("Thread starting, indx: %d, len: %d\n" % (self.startIndx, self.unitLen));
		BuildItemSimilarityMatrix(self.itemList, self.startIndx, self.unitLen, self.alpha, self.gamma, self.recFileName, self.simCalculator);
		print("Thread Ending, indx: %d, precision: %f\n" % (self.startIndx, self.precision));
		return;

def RunThreads(alpha, datalen, headline, gamma, songsimSharedData):
	itemList = gMostPopItems.keys();
	Len = len(itemList);
	startIndx = 0;
	maxLen = datalen;   #max length of data for each thread

	threadList = [];
	resultQueue = multiprocessing.Queue();

	count = 0;
	while(True):
		if( startIndx >= Len ):
			break;
		count += 1;
		recFileName = "song_sim_" +headline + "_" + str(alpha) + "_" + str(count) + ".txt";
		unitLen = min(Len-startIndx, maxLen);
		songSimCalc = SongSimilarity(songsimSharedData)
		t = SimThread( itemList, startIndx, unitLen, alpha, recFileName, gamma, songSimCalc );
		t.daemon = True;
		t.start();
		threadList.append(t);
		startIndx = startIndx + unitLen;

	print("waiting for threads\n");

	try:
		for t in range(0, len(threadList)):
			threadList[t].join();
	except (KeyboardInterrupt, SystemExit):
		print "interruped\n";
		sys.exit();

	print("All threads done\n");

def main(argv):
	global gResultsFile;
	alpha = 0.5;
	datalen = 5000;
	gamma = 1;
	headline = "similarity";

	if(len(sys.argv) > 4):
		alpha = float(sys.argv[1]);
		datalen = int(sys.argv[2]);
		headline = sys.argv[3];
		gamma = int(sys.argv[4]);

	print("starting sim with alpha: %f, gamma: %d, datalen: %d\n" % (alpha, gamma, datalen));
	ParseUserData('../data/users_30000.train', False);
	ParseUserData('../data/users_30000_10000.test', True);
	print("Data Parsed\n");
	print("Calculating Item similarity...\n");
	SampleMostPopularSongs();

	sssd = SongSimilaritySharedData();
	sssd.initialize("../data/lyrics_nodups.txt", "../data/tags_nodups.txt", "../data/msd_song_track_map.txt", "../data/msd.txt", "../data/songs_map.txt");

	RunThreads(alpha, datalen, headline, gamma, sssd);
	print("Item similarity calculated\n");

if __name__ == "__main__":
	try:
		main(sys.argv);
	except KeyboardInterrupt:
		sys.exit();
