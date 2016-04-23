from BeautifulSoup import BeautifulSoup
from urlparse import urljoin
import urllib2
import argparse
import re
import codecs
import time
import random
import csv

get_yelp_badreview_page = \
    lambda bizname, page_num: \
	'http://www.yelp.com/not_recommended_reviews/{0}' \
	'?not_recommended_start={1}'.format(bizname, page_num)

ZIP_URL = "zipcodesNY.txt"
RDATA_URL = "mydata.txt"
FIELD_DELIM = u'###'
LISTING_DELIM = u'((('
GOODREVIEW = 1
BADREVIEW = 0

def get_zips():
    """
    """
    f = open(RDATA_URL, 'r+')
    zips = [zz.strip() for zz in f.read().split('\n') if zz.strip() ]
    f.close()
    return zips


def crawlBadReviews(yelpPage, page_num, verbose=False):
	try:
	    #print 'starting soup3', yelpPage
	    page_url = get_yelp_badreview_page(yelpPage, page_num)
	    soup3 = BeautifulSoup(urllib2.urlopen(page_url).read())
	    print 'url', yelpPage
	    #soup3 = BeautifulSoup(urllib2.urlopen(urljoin('http://www.yelp.com/not_recommended_reviews/',yelpPage)).read())
	except Exception, e:
	    print "**failed to get you a page", str(e)
	extracted = [] # a list of tuples
	filteredreviews = soup3.findAll('div', attrs={'class':re.compile
	    (r'^review review--with-sidebar')})

	try:
	    assert(len(filteredreviews) > 0)
	except AssertionError, e:
	    print 'ASSERT ERROR ) reviews', str(e)
	    # False is a special flag, returned when quitting
	    return [], False

	#print 'Not Recommended Reviews'
	for r in filteredreviews:
		title = ''
		restRating = ''
		author = ''
		authorid = ''
		friends = ''
		numberOfReviews = ''
		rating = ''
		review = ''
		date = ''
		try:
			author = r.find('span', {'class':'user-display-name'}).getText().encode('utf-8')
		except Exception, e:
	    		if verbose: print 'author extract fail', str(e)
		try:
			authorid = r.find('span', {'class':'user-display-name'})['data-hovercard-id'].encode('utf-8')
		except Exception, e:
	    		if verbose: print 'id extract fail', str(e)
		try:
			friends = r.find('span', {'class':'i-wrap ig-wrap-common_sprite i-18x18_friends_c-common_sprite-wrap'}).b.getText().encode('utf-8')
		except Exception, e:
	    		if verbose: print 'friend extract fail', str(e)
		try:
			numberOfReviews = r.find('span', {'class':'i-wrap ig-wrap-common_sprite i-18x18_review_c-common_sprite-wrap'}).b.getText().encode('utf-8')
		except Exception, e:
	    		if verbose: print 'numberOfReviews extract fail', str(e)
		try:
			rating = r.find('i', {'class':re.compile(r'^star-img')}).img['alt'].encode('utf-8')
			rating = rating[:3]
		except Exception, e:
	    		if verbose: print 'rating extract fail', str(e)
		try:
			review = r.find('p', {'lang':'en'}).getText().encode('utf-8')
		except Exception, e:
	    		if verbose: print 'review extract fail', str(e)
		try:
			date = r.find('span', {'class':'rating-qualifier'}).getText().encode('utf-8')
		except Exception, e:
	    		if verbose: print 'date extract fail', str(e)
		extracted.append((title, yelpPage, restRating, author, authorid, friends, numberOfReviews, rating, review, date, BADREVIEW))
		if author: print 'aBR:', author
		#if author: print 'f1:', friends
		#if review: print 'reviewF1:', numberOfReviews
		#if rating: print 'ratingF1:', rating
	return extracted, True


#######################################################################################################################################################################

def crawl():
    page = 10
    flag = True
    reviewData = get_zips()

    text_file = open("OutputBR.csv", "wb")
    for rwdata in reviewData:
        print '\n===== Attempting extraction for zipcode <', rwdata, '>=====\n'
	flag=True
	writer = csv.writer(text_file, delimiter='|')
    	page = 10
	while flag:
	    print '...'
	    extracted, flag = crawlBadReviews(rwdata, page)
	    #text_file.write(extracted)
	    writer.writerows(extracted)
	    if not flag:
	        print 'extraction stopped or broke at rwdata'
	        break
	    if page > 100:
		break
	    page += 10
	    time.sleep(random.randint(1, 2) * .931467298)
    text_file.close()


if __name__ == '__main__':
    crawl()


