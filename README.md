# FilmRecommendations

Submission for a final project for CS-81: Machine Learning and Data Mining

This project was an experiment to determine whether or not I could produce accurate personalized film recommendations for
new movies using reviews data scraped from Rotten Tomatoes™. We used the Movie Lens (http://grouplens.org/datasets/movielens/)
datasets for getting movie titles and test reviews.

It is currently divided into 3 directories:

Data
====
Contains base data from our scraping. Only reviews for movies in the past 3-4 years. Contains the reviews information
in a sparse matrix format. Also a small set of ratings from classmates and friends.

web-scraping
============
Contains ipython notebooks and scripts that were used for parsing. The ipython notebooks were used to determine how to 
setup our scripts and where data is located on the RT website. The scripts 

fetch_reviews.py - takes a movie lens datasets and attempts to scrape as many titles as possible from the web.
parse_results.py - takes the output from fetch_reviews.py and puts it into a sparse matrix csv

Recommendations
===============
Contains ipython notebooks for our work with producing ratings predictions. We ended up using Crab since it integrated easily
with our current setup (in python), and allowed us to experiment with parsing data and get an idea of whether or not this
method is actually accurate. I am currently working on a scalable service solution that uses LensKit for collaborative filtering.

Recommendations.ipynb - main work centered on using crab to get recommendations
Visualizations.ipynb - I wanted to come up with something that let us visualize our recommendations performance, but 
didn't get very far.
