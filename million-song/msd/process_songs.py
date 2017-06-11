import os
import glob
import hdf5_getters
import pdb

H5 = hdf5_getters

def parse_file(h5):
	data = []
	out = open("out/msd_orig.txt","a")
	num_songs = hdf5_getters.get_num_songs(h5)
	for i in range(990000, num_songs):
		item = {}
		item["msid"] = H5.get_track_id(h5, i)
		item["artist_name"] = H5.get_artist_name(h5, i)
		item["energy"] = H5.get_energy(h5, i)
		item["loudness"] = H5.get_loudness(h5, i)
		item["tempo"] = H5.get_tempo(h5, i)
		item["year"] = H5.get_year(h5, i)
		data.append(item)

		if "\t" in item["artist_name"]:
			print "!Warning! Tab found in artist name:", item["artist_name"]
	
		if i > 990000 and i % 10000 == 0:
			print "Writing %d to %d." % (i-10000, i)
			output = ""
			for j in range(0, len(data)):
				s = data[j]
				output += "%s\t%s\t%s\t%s\t%s\t%s\n" % (\
					s["msid"], \
					s["artist_name"], \
					s["energy"], \
					s["loudness"], \
					s["tempo"], \
					s["year"])
			out.write(output)
			data = []
	
	output = ""
	for j in range(0, len(data)):
		s = data[j]
		output += "%s\t%s\t%s\t%s\t%s\t%s\n" % (\
			s["msid"], \
			s["artist_name"], \
			s["energy"], \
			s["loudness"], \
			s["tempo"], \
			s["year"])
	out.write(output)
	out.close()

def execute(basedir,ext='.h5'):
	for root, dirs, files in os.walk(basedir):
		files = glob.glob(os.path.join(root,'*'+ext))
		for f in files:
			h5 = H5.open_h5_file_read(f)
			parse_file(h5)
			h5.close()

print execute("data");
