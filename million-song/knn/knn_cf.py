import math
import heapq
import sys
import string
import random
import time
import pdb;

# CS 4780/5780 k-Nearest Neighbor implementation example code
# by Joshua L. Moore, August/September 2012
#
# To run the experiment over all users for a particular parameter setting, run
# python knn_cf.py exp nnk (list of integer values for k)
#   sim (metric argument) [weighted]
# where if weighted is not passed as a keyword, the unweighted algorithm will
# be used.
#
# To query for recommendations for a particular user, run
# python knn_cf.py user [user_id] [other parameters as in experiment setting]
#
# To query a particular artist, run
# python knn_cf.py artist [artist_string] [other parameters as before]

nnk = 10
preck = 5
weighted_knn = False
# defined later:
# metrics = [eucDistSim, dotProdSim, cosSim]
chosen_metric = 2

# Cosine similarity
def cosSim(x, y):
  sim = 0.0
  x_norm = 0.0
  y_norm = 0.0
  ykeys = y.keys()
  for index in x.keys():
    if index in y:
      sim += x[index] * y[index]
      y_norm += y[index] ** 2 
      ykeys.remove(index)
    x_norm += x[index] ** 2
  for index in ykeys:
    y_norm += y[index] ** 2 
  x_norm = math.sqrt(x_norm)
  y_norm = math.sqrt(y_norm)
  return sim / (x_norm * y_norm)

# Inverse Euclidean Distance
def eucDistSim(x, y):
  sim = 0.0
  ykeys = y.keys()
  for index in x.keys():
    if index in y:
      sim += (x[index] - y[index]) ** 2
      ykeys.remove(index)
    else:
      sim += x[index] ** 2
  for index in ykeys:
    sim += y[index] ** 2
  if sim > 0:
    return 1.0 / sim
  else:
    return 10000000000.0

# Dot product
def dotProdSim(x, y):
  sim = 0.0
  for index in x.keys():
    if index in y:
      sim += x[index] * y[index]
  return sim

# Adds c*y to x
def addVec(x, y, c = 1):
  for index in y.keys():
    to_add = c * y[index]
    if index not in x:
      x[index] = to_add
    else:
      x[index] += to_add
  return x

# If vector == None, returns a result ranking for query user i. Otherwise,
# returns a result ranking for the specified user vector. nnk is the k used
# for k-nearest neighbor search.
def rankSongsForQuery(i, nnk, vector = None):
  global train
  global weighted_knn
  global preck
  if not vector:
    pl = train[i]
  else:
    pl = vector
  ranking = dict()
  dists = [0] * len(train)
  for j in range(0, len(train)):
    pl2 = train[j]
    dists[j] = (metrics[chosen_metric](pl, pl2), j)
  dists.sort(reverse = True)
  if not vector:
    # remove the query user from the nearest users
    dists = dists[1:]
  nearest_neighbors = [p[1] for p in dists[0:nnk]]
  total_dist = sum([p[0] for p in dists[0:nnk]])
  if (total_dist != 0 and weighted_knn):
    for j in range(0, nnk):
      ranking = addVec(ranking, train[nearest_neighbors[j]], dists[j][0] / total_dist)
  else:
    for j in range(0, nnk):
      ranking = addVec(ranking, train[nearest_neighbors[j]], 1.0 / nnk)
  ranking_list = []
  for song in ranking.keys():
    if song not in pl.keys():
      ranking_list.append((ranking[song], song))
  ranking = ranking_list
  ranking = heapq.nlargest(preck, ranking)
  return ranking

# Function to run the experiment on all users for one set of parameters
def experiment():
  global train
  global test
  global nnk
  avg_prec = 0.0
  if len(sys.argv) > 2 and sys.argv[2] == "freq":
    # Popularity baseline
    sum_vector = dict()
    for train_vector in train:
      addVec(sum_vector, train_vector)
    ranking_list = []
    for index in sum_vector.keys():
      ranking_list.append((sum_vector[index], index))
      ranking = heapq.nlargest(preck, ranking_list)
      ranking = [r[1] for r in ranking]
  for i in range(0, len(train)):
    if i % 1000 == 0:
      print "Item " + str(i)
    labels = test[i]
    if len(sys.argv) <= 2 or sys.argv[2] != "baseline":
      ranking = rankSongsForQuery(i, nnk)
      ranking = [r[1] for r in ranking]
    elif sys.argv[2] == "random":
      # Random baseline
      random.seed()
      ranking = range(0, len(train));
      random.shuffle(ranking)
    num_relevant = 0
    for song in ranking:
      if song in labels:
        num_relevant += 1
    rank_len = float(len(ranking));
    if rank_len > 0.0:
      avg_prec += num_relevant / float(len(ranking))
    else:
      avg_prec += 0.0;
    if len(labels) < preck:
      print "Warning: fewer labels than songs considered for preck."
  avg_prec = avg_prec / float(len(train))
  #print "k = {}, metric = {}, weighted = {}:".format(nnk, chosen_metric, weighted_knn)
  print "Average precision at " + str(preck) + ": " + str(avg_prec)

# End function declarations

# Begin main body

print "Beginning at {}"

train_file = open('../data/users_3000.train', 'r')
test_file = open('../data/users_3000.test', 'r')
song_names_file = open('../data/song_mapping.txt')
song_names = dict()
for line in song_names_file:
  tokens = string.split(line, maxsplit = 1)
  song_id = int(tokens[0])
  song_names[song_id] = tokens[1].rstrip()

metrics = [eucDistSim, dotProdSim, cosSim]

# argument parsing

nnk_list = [nnk]

if len(sys.argv) > 1 and "baseline" not in sys.argv:
  for i in range(1, len(sys.argv)):
    if sys.argv[i] == "nnk":
      nnk_list = []
      while i < len(sys.argv) + 1 and sys.argv[i + 1].isdigit():
        nnk_list.append(int(sys.argv[i + 1]))
        i += 1
    elif sys.argv[i] == "sim":
      chosen_metric = int(sys.argv[i + 1])
      i += 1
    elif sys.argv[i] == "weighted":
      weighted_knn = True
    elif sys.argv[i] == "user":
      query = int(sys.argv[2])
      input_vector = train[query]
    elif sys.argv[i] == "artist":
      query = -1
      input_vector = dict()
      artist_name = sys.argv[i + 1].lower()
      for song_id in song_names.keys():
        if artist_name in song_names[song_id].lower():
          input_vector[song_id] = 1
      print len(input_vector)
      i += 1

print nnk_list, chosen_metric, weighted_knn

# first parse the two files to sparse vector format
train = []
test = []

for line in train_file:
  tokens = line.split()[2:]
  sv = dict()
  for t in tokens:
    ts = [int(tsplit) for tsplit in t.split(':')]
    sv[ts[0]] = ts[1]
  train.append(sv)
for line in test_file:
  test.append([int(t) for t in line.split()[2:]])

# Run experiments if desired, otherwise run the single query we picked
if sys.argv[1] == "exp":
  for k in nnk_list:
    nnk = k
    experiment()
else:
  query_vector_list = []
  for index in input_vector.keys():
    query_vector_list.append((input_vector[index], index))
  top_songs_in_query_pl = sorted(query_vector_list, reverse = True)
  top_songs_in_query_pl = top_songs_in_query_pl[0:10]
  print
  print "Query playlist top songs:"
  for song in top_songs_in_query_pl:
    print song_names[song[1]]
  print
  print "Retrieved songs:"
  if query == -1:
    ranking = rankSongsForQuery(query, nnk, vector = input_vector)
  else:
    ranking = rankSongsForQuery(query, nnk)
  ranking = [r[1] for r in ranking]
  for song_id in ranking:
    print song_names[song_id]
  print

print "Ending at {}"


















