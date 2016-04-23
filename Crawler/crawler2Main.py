
from BeautifulSoup import BeautifulSoup
from urlparse import urljoin
import urllib2
import argparse
import re
import codecs
import time
import random
import csv

get_yelp_page = \
    lambda zipcode, page_num: \
	'https://www.yelp.com/search?find_loc=={0}' \
	'&start={1}' \
	'&cflt=restaurants'.format(zipcode, page_num)

get_yelp_review_page = \
    lambda bizname, page_num: \
	'https://www.yelp.com{0}' \
	'?start={1}'.format(bizname, page_num)


ZIP_URL = "zipcodesNY.txt"
FIELD_DELIM = u'###'
LISTING_DELIM = u'((('
GOODREVIEW = 1
BADREVIEW = 0

def get_zips():
    """
    """
    f = open(ZIP_URL, 'r+')
    zips = [int(zz.strip()) for zz in f.read().split('\n') if zz.strip() ]
    f.close()
    return zips

def crawl_page(zipcode, page_num, verbose=False):
    """
    This method takes a page number, yelp GET param, and crawls exactly
    one page. We expect 10 listing per page.
    """
    try:
        page_url = get_yelp_page(zipcode, page_num)
        soup = BeautifulSoup(urllib2.urlopen(page_url).read())
    except Exception, e:
        print str(e)
        return []

    restaurants = soup.findAll('div', attrs={'class':re.compile
            (r'^search-result natural-search-result')})
    try:
        assert(len(restaurants) == 10)
    except AssertionError, e:
        # We make a dangerous assumption that yelp has 10 listing per page,
        # however this can also be a formatting issue, so watch out
        print 'ASSERT ERROR we have hit the end of the zip code', str(e)
        # False is a special flag, returned when quitting
        return [], False

    extracted = [] # a list of tuples
    extractedGR = [] # a list of tuples
    extractedBR = [] # a list of tuples
    for r in restaurants:
        yelpPage = ''
	title = ''
	restRating = ''
	try:
            title = r.find('a', {'class':'biz-name'}).getText().encode('utf-8')
        except Exception, e:
            if verbose: print 'title extract fail', str(e)
        try:
            yelpPage = r.find('a', {'class':'biz-name'})['href']
        except Exception, e:
            if verbose: print 'yelp page link extraction fail', str(e)
            continue
        try:
            restRating = r.find('i', {'class':re.compile(r'^star-img')}).img['alt'].encode('utf-8')
	    restRating = restRating[:3]
        except Exception, e:
            if verbose: print 'restRating extract fail', str(e)

	time.sleep(random.randint(1, 2) * .931467298)
	goodreviewpage = 0
	grflag = True
	extractedBRFull = []
	while grflag:
	    extractedGR, grflag = crawlGoodReviews(yelpPage, goodreviewpage, title, restRating, grflag)
	    extractedBRFull = extractedBRFull + extractedGR
	    #print 'check................', grflag, title
	    if not grflag: 
		print 'extraction stopped or broke at review page end'
	    	break
	    if goodreviewpage > 500:
		break
	    goodreviewpage += 20
	    #time.sleep(random.randint(1, 2) * .931467298)

	time.sleep(random.randint(1, 2) * .931467298)
	brflag = False
	extractedBR, brflag = crawlBadReviews(yelpPage, title, restRating, brflag)
        #print '=============='

        # extracted.append((title, categories, rating, img, addr, phone, price, menu,
        #    creditCards, parking, attire, groups, kids, reservations, delivery, takeout,
        #    waiterService, outdoor, wifi, goodFor, alcohol, noise, ambience, tv, caters,
        #    wheelchairAccessible))
	extracted = extracted + extractedBRFull + extractedBR
    return extracted, True

#######################################################################################################################################################################

def crawlGoodReviews(bizname, page_num, title, restRating, verbose=False):
	try:
		page_url = get_yelp_review_page(bizname, page_num)
		soup2 = BeautifulSoup(urllib2.urlopen(page_url).read())
	except Exception, e:
		print str(e)
		return []
	extracted = [] # a list of tuples
	reviews = soup2.findAll('div', attrs={'class':re.compile
	    (r'^review review--with-sidebar')})

	for r in reviews:
		author = ''
		authorid = ''
		friends = ''
		numberOfReviews = ''
		rating = ''
		review = ''
		date = ''
	
		try:
			author = r.find('a', {'class':'user-display-name'}).getText().encode('utf-8')
		except Exception, e:
	    		if verbose: print 'author extract fail', str(e)
		try:
			authorid = r.find('a', {'class':'user-display-name'})['data-hovercard-id'].encode('utf-8')
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
			rating = r.find('meta', {'itemprop':'ratingValue'})['content'].encode('utf-8')
		except Exception, e:
	    		if verbose: print 'rating extract fail', str(e)
		try:
			review = r.find('p', {'itemprop':'description'}).getText().encode('utf-8')
		except Exception, e:
	    		if verbose: print 'review extract fail', str(e)
		try:
			date = r.find('span', {'class':'rating-qualifier'}).getText().encode('utf-8')
		except Exception, e:
	    		if verbose: print 'date extract fail', str(e)
		bizname = bizname.rsplit('/', 1)[-1]
		extracted.append((title, bizname, restRating, author, authorid, friends, numberOfReviews, rating, review, date, GOODREVIEW))
		#if author: print 'aGR:', author
		#if review: print 'review:', review
		#if rating: print 'rating:', rating
	return extracted, True
#######################################################################################################################################################################



def crawlBadReviews(yelpPage, title, restRating, verbose=False):
	try:
	    #print 'starting soup3', yelpPage
	    yelpPage = yelpPage.rsplit('/', 1)[-1]
	    #print 'url', yelpPage
	    soup3 = BeautifulSoup(urllib2.urlopen(urljoin('http://www.yelp.com/not_recommended_reviews/',yelpPage)).read())
	except Exception, e:
	    print "**failed to get you a page", str(e)
	extracted = [] # a list of tuples
	filteredreviews = soup3.findAll('div', attrs={'class':re.compile
	    (r'^review review--with-sidebar')})

	#print 'Not Recommended Reviews'
	for r in filteredreviews:
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
		#if author: print 'aBR:', author
		#if author: print 'f1:', friends
		#if review: print 'reviewF1:', numberOfReviews
		#if rating: print 'ratingF1:', rating
	return extracted, True


#######################################################################################################################################################################
def crawl(zipcode=None):
    page = 0
    flag = True
    some_zipcodes = [zipcode] if zipcode else get_zips()

    if zipcode is None:
        print '\n**We are attempting to extract all zipcodes in America!**'
    text_file = open("Output.csv", "wb")
    for zipcode in some_zipcodes:
        print '\n===== Attempting extraction for zipcode <', zipcode, '>=====\n'
	flag=True
	writer = csv.writer(text_file, delimiter='|')
	while flag:
	    print '...'
	    extracted, flag = crawl_page(zipcode, page)
	    #text_file.write(extracted)
	    writer.writerows(extracted)
	    if not flag:
	        print 'extraction stopped or broke at zipcode'
	        break
	    page += 10
	    time.sleep(random.randint(1, 2) * .931467298)
    text_file.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extracts all yelp restaurant \
        data from a specified zip code (or all American zip codes if nothing \
        is provided)')
    parser.add_argument('-z', '--zipcode', type=int, help='Enter a zip code \
        you\'t like to extract from.')
    args = parser.parse_args()
    crawl(args.zipcode)
