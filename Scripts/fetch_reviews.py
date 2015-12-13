from urllib.request import urlopen
import urllib
from bs4 import BeautifulSoup
import string
import pickle
import sys
import csv

"""
Given a csv of the form

movie id, movie title (year), genres

As in what is available in the Movie Lens Datasets available at 
http://grouplens.org/datasets/movielens/

In particular the files at:
http://files.grouplens.org/datasets/movielens/ml-latest-small.zip

or:
http://files.grouplens.org/datasets/movielens/ml-latest.zip

This script parses the movie file, then queries Rotten Tomatoes to try and scrape any related reviews
for each movie. Then dumps the results into the outfile specified in the format:

"name", "movie id", "title", "year", "genres", "source", "score", "url", "original link"

Separated by tabs.


This takes a long time to run since it's just making requests over the open internet, then scraping
one by one. Really this should be multithreaded with executable tasks, but I have noticed that running
this for a few thousand movies, the pace slows to a crawl. It's possible that RottenTomatoes
throttles repeated calls from a single IP address...

So it's generally advisable to execute this in chunks for larger sets of movies.
"""

args = sys.argv
if (len(args) <= 2):
    print("Missing Required Arguments: INPUT_FILE OUTPUT_FILE (ERROR_FILE)")
    sys.exit(1)
    
    
# Input file
input_file = args[1]

# Output file
output_file = args[2]

# Error file for movies
pickle_file = None
if (len(args) >= 4):
    pickle_file = args[3]
    
    
errored_lines = []


#####
#
# Load all data into a movies dictionary keyed by movie id.
#
#####

def split_title(title):
    title = title.strip()
    return [title[0:-7], int(title[-5:-1])]

print("Loading file...")

lines = []
for line in csv.reader(open(input_file, newline=''), delimiter=',', quotechar='\"'):
    lines.append(line)
    
movies = {}
for i in range(1,len(lines)):
    try:
        line = lines[i]
        idnum = int(line[0])
        title, year = split_title(line[1])
        genres = line[2].split('|')

        movies[idnum] = [title, year, genres]
        
    except Exception as inst:
        errored_lines.append(lines[i])

print("Loaded movies.")

#####
#
# UTILITY FUNCTIONS
#
#####

rt_url = "http://www.rottentomatoes.com"
rt_search_url = rt_url + "/search/?search="

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def encode_unicode(title):
    """
    replaces unicode characters with percent encodings.
    """
    tmp = ''
    for i in range(0, len(title)):
        c = title[i]
        if is_ascii(c):
            tmp += c
        else:
            tmp += urllib.parse.quote(c)
    tmp = tmp.encode("utf-8")
    return urllib.parse.quote(tmp)
    
    
exclude = set(string.punctuation.replace('(','').replace(')', '').replace("'",''))
def get_search_url(movie):
    """
    Finds the rotten tomatoes URL for the given title.
    """
    title = ''.join(ch for ch in movie[0] if ch not in exclude).lower()
    
    if not is_ascii(title):
        # Percent encode UNICODE characters
        title = encode_unicode(title)
        
    search_url = rt_search_url + '+'.join(title.split(' '))
    
    return search_url
    
    
def convert_letter_grade(score):
    """
    Converts letter grade to score.
    """
    score = score.lower()
    
    if score == 'a':
        return 1
    
    letter = score[0]
    sign = None
    if len(score) > 1:
        sign = score[1]
    
    s = None
    if letter == 'a':
        s = .80
    elif letter == 'b':
        s = .60
    elif letter == 'c':
        s = .40
    elif letter == 'd':
        s = .20
    elif letter == 'f':
        s = 0
        
    if sign == '+':
        s += .1
    elif sign == '-':
        s -= .1
        
    return s

def compute_score(score):
    """
    Takes a score from rotten tomatoes and converts it to a score between 0 and 1. 0 being terrible
    and 1 being perfect. If there isn't a score, returns -1.
    """
    if not score:
        return None
    try:
        if '/' in score:
            num, denom = score.split('/')
            return float(num)/float(denom)
            
        return convert_letter_grade(score)
    except:
        return score
        
        
        
def process_review(review):
    reviewer_and_source = review.find("div", {"class" : "critic_name"})
    link_and_score = review.find("div", {"class" : "small subtle"})
    
    source = reviewer_and_source.find('em').getText()
    reviewer = reviewer_and_source.find('a')
    
    if not reviewer:
        reviewer = source
    else:
        reviewer = reviewer.getText()

    review_link = link_and_score.find('a')
    if (review_link):
        review_link = review_link['href']

    score = link_and_score.getText().split('Original Score:')
    if len(score) > 1:
        score = score[1].strip()
    else:
        score = None
    
    return [reviewer, source, compute_score(score), review_link]
    
    
page_suffix = "?page=%d&sort="
def get_reviews(url):
    """
    Given an RT reviews page, this grabs links to all of the reviews on the page.
    """
    if not url:
        return {}
    
    if not (url[-1] == '/'):
        url += '/'
    
    all_reviews = {}
    for i in range(1,20):
        page = url + (page_suffix % i)
        
        try:
            response = urlopen(page)
        except:
            break
        
        soup = BeautifulSoup(response)
        reviews = soup.findAll("div", { "class" : "row review_table_row" })
    
        for review in reviews:
            data = process_review(review)
            all_reviews[data[0]] = data
    return all_reviews
    
    
    
def get_movie_url(movie):
    """
    Given a movie, determines the rotten tomatoes URL for the critics' reviews of that movie.
    """
    search_url = get_search_url(movie)
    
    response = urlopen(search_url)
    soup = BeautifulSoup(response)
    
    url = None
    
    # No results tag
    if (soup.find("h1", {"class" : "center noresults"})):
        return url
    
    if "search results" in soup.find("title").text.lower():
        # Find the movie with the correct year
        year = movie[1]
        results = soup.findAll("li", {"class" : "media bottom_divider clearfix"})
        
        for i in results:
            result_year = i.find("span", {"class" : "movie_year"}).getText().strip()[1:5]
            if not result_year:
                continue
            result_year = int(result_year)
            result_url = rt_url + i.find("a")["href"]
            
            title = i.find("div", {"class" : "nomargin media-heading bold"}).find("a").getText().lower()

            if year == result_year:
                url = result_url
                break
    
    else:
        url = response.url.split('?')[0]

    if url:
        url = url + "reviews"
    
    return url

#####
#
# Processes all movies in file
#
#####

recent_reviews = {}
count = 0
errors = 0
print("Starting Rotten Tomatoes queries...")
for mid in movies:
    
    if mid in recent_reviews:
        continue
        
    movie = movies[mid]
    
    try:
        url = get_movie_url(movie)
        movie.append(url)
    except Exception as ex:
        errored_lines.append([mid, movie, ex])
        errors += 1
        continue
        
                    
    try:
        rs = get_reviews(url)
    except Exception as ex:
        errored_lines.append([mid, movie, ex])
        errors += 1
        continue
        
        
    recent_reviews[mid] = rs
    
    count += 1
    if (count % 20 == 1):
        print("Processed %d movies..." % count)
        
    if (count % 3 == 1):
        f = open("recent_reviews.pickle", 'wb')
        pickle.dump(recent_reviews, f)
        
print(errored_lines)

print("Done! Processed %d movies. Errored on %d movies" % (count, errors))

#####
#
# Converts all reviews into a dictionary keyed by names
#
#####
print("Writing results to file...")
reviewers = {}
for i in recent_reviews:
    reviews = recent_reviews[i]
    title, year, genre, url = movies[i]

    for name in reviews:

        if name not in reviewers:
            reviewers[name] = {}
        
        rev, source, score, link = reviews[name]
        reviewers[name][i] = [title, year, genre, source, score, url, link]

    
#####
#
# Dumps output to file
#
#####
f = open(output_file, "w")

header = '\t'.join(["name", "movie id", "title", "year", 
                    "genres", "source", "score", "url", "original link"])
f.write(header + '\n')

for person in reviewers:
    reviews = reviewers[person]
    
    for mid in reviews:
        line = '\t'.join(str(x) for x in ([person, mid] + reviews[mid]))
        
        f.write(line + '\n')

f.close()

print("Done!")