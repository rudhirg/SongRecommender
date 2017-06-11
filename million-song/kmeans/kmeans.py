import sys
from scipy.sparse import *
from scipy.sparse import lil_matrix
from sklearn.cluster import KMeans
import pdb

#filename = "users_3000.train.txt"
filename = "user_train.txt"

def extract_nonzero(S):
  #with open(filename, 'r') as input:
  input = open(filename, 'r')
  ind = 0
  output = open("mapping_of_" + filename, 'w') 
  for line in input.read().strip().split('\n'):
    user_id = int(line.split()[0])
    elements_in_row = line.split()[2:]
    output.write(str(ind) + ":" + str(user_id)+"\n")
    for elt in elements_in_row:
      value = elt.split(":")
      S[int(ind), int(value[0])] = int(value[1])
    ind += 1
  input.close()
  output.close()

def read_data():
  input = open(filename, 'r') 
  rowsize = 0
  colsize = 0
  for line in input.read().strip().split('\n'):
    #print line
    user_id = int(line.split()[0].strip())
    elements_in_row = line.split()[2:]
    for elt in elements_in_row:
      value = elt.split(":")
      if len(value) > 1 and colsize < int(value[0]) : 
        colsize = int(value[0])
    #return 
    rowsize += 1
  input.close()
  return (rowsize, colsize)

# python kmeans.py 3 filename.txt
if( __name__ == '__main__'):  
  
  num_k = 10

  if len(sys.argv) > 1:
    num_k = int(sys.argv[1])

  if len(sys.argv) > 2:
    filename = sys.argv[2]

  # obtain dimensions of data
  (rdim, cdim) = read_data()

  # allocate a lil_matrix of size (rdim by cdim)
  # note: lil_matrix is used since we be modifying
  #       the matrix a lot.
  print "Dimensions: (num users - num songs)" + str(rdim) + " - " + str(cdim)
  S = lil_matrix((rdim, cdim + 1))

  # add data to S
  extract_nonzero(S)

  # perform clustering
  labeler = KMeans(k=num_k)
  # convert lil to csr format
  # note: Kmeans currently only works with CSR type sparse matrix
  labeler.fit(S.tocsr()) 

  label_array = [0] * num_k

  centroids = labeler.cluster_centers_

  for (row, label) in enumerate(labeler.labels_):
    label_array[label] += 1

  for elt in centroids:
    print elt

  iter = 0
  for elt in label_array: 
    print "CLUSTER : " + str(iter) + " : " + str(elt)
    iter += 1

  results = []
  # read the test data 
  
  # for each element in the test data
  #   find which centroid it is closest to
  #   get the list of songs that that centroid has
  #   compare it with the actual songs the user prefers
  #   save this number in the results array

  # calculate the average of the results array

