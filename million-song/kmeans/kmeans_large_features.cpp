#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sstream>

using namespace std;

const int k = 3;
//const string input_filename = "filename.txt";
char * input_filename;


vector< vector<int> > all_elements;
//vector<string> fields;

map<int, double> centroid_values [k];

vector<int> in_which_centroids [k];

void get_elements()
{
	ifstream file (input_filename, ifstream::in);
	string get_elt;
	while(!file.fail())
	{
    getline(file, get_elt);
    stringstream oss;
    oss << get_elt;
    int array_ind = -1;
    oss >> array_ind;//atoi(fields[0]);
    vector<int> local_elements;
    while(!oss.fail())
    {
      int val = 0;
      oss >> val;
      local_elements.push_back(val);
    }
    all_elements.push_back(local_elements);
	}
}

int determine_which_centroids(int element_index)
{
	double similarity_index = 0;
	int centroid_ind = -1;
	for(int i = 0; i < k; i++){
		double local_sim_index = 0;
		for(int j = 0; j < all_elements[element_index].size(); j++){
      //cout <<all_elements[element_index][j] <<endl;
      if(centroid_values[i].find(all_elements[element_index][j]) != centroid_values[i].end()) local_sim_index += centroid_values[i][all_elements[element_index][j]];
		}
    if(local_sim_index > similarity_index){
      similarity_index = local_sim_index;
      centroid_ind = i; 
    } 
	}
	return centroid_ind;
}

void assign_centers()
{
	int centroid_contains [k];
	for(int i = 0; i < k; i++){
		in_which_centroids[k].clear();
		centroid_contains[i] = 0;
	}
  //cout << all_elements.size() <<endl;
	for(int i = 0; i < all_elements.size(); i++){
		int which_centroid = determine_which_centroids(i);
		in_which_centroids[which_centroid].push_back(i);
		centroid_contains[which_centroid]++;
	}
	cout << " Centroid elements: ";
	for(int i = 0; i < k; i++)
	{
		cout << centroid_contains[i] << " ";
	}
	cout << endl;
}

void recompute_centers()
{
	for(int i = 0; i < k; i++)
	{
		centroid_values[i].clear();
    double divide_by = 0;
		for(int j = 0; j < in_which_centroids[i].size(); j++)
		{
      int index = in_which_centroids[i][j];
      for(int q = 0; q < all_elements[index].size();q++){
        if(centroid_values[i].find(all_elements[index][q]) != centroid_values[i].end()) centroid_values[i][all_elements[index][q]] = centroid_values[i][all_elements[index][q]] + 1;
        else{
          centroid_values[i][all_elements[index][q]] = 1;
        }
        divide_by++;
      }
		}
    for(map<int, double>::iterator it = centroid_values[i].begin(); it != centroid_values[i].end(); it++)
    {
      it->second = it->second/divide_by;
    }
	}
}

int main(int argc, char ** argv)
{
  //input_filename = string();
  input_filename= argv[1];
	get_elements();
	srand ( time(NULL) );
	int num_iter = 10;
	for(int i = 0; i < k; i++)
	{
		int index = rand()%all_elements.size();
		in_which_centroids[i].push_back(index);
	}
  cout <<"Done reading." <<endl;
	for(int i = 0; i < num_iter; i++)
	{
		recompute_centers();
		assign_centers();
	}
	return 0;
}
