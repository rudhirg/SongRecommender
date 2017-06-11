import sys

filename = "user_song_counts_100000.train"
outfile = "100000_user_read_cpp.train"
outfile_mapping = outfile + "mapping"
def read_data():
  input = open(filename, 'r') 
  output = open(outfile, 'w')
  output_mapping = open(outfile_mapping, 'w')
  rowsize = 0
  colsize = 0
  index = 0
  for line in input.read().strip().split('\n'):
    user_id = int(line.split()[0].strip())
    output.write(str(index))
    output_mapping.write(str(index) + " " + str(user_id) + "\n")
    output.write(" ")
    elements_in_row = line.split()[2:]
    for elt in elements_in_row:
      value = elt.split(":")
      output.write(value[0])
      output.write(" ")
    output.write("\n")
    index += 1
  input.close()
  output.close()
  
if( __name__ == '__main__'):  
  read_data()
