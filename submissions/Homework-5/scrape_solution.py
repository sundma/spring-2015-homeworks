#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import requests
from bs4 import BeautifulSoup



log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
loghandler = logging.StreamHandler(sys.stderr)
loghandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(loghandler)

base_url = "http://www.tripadvisor.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"
f = open("hotel_data.csv", "w")
f2 = open("hotel_data2.csv", "w")


def get_city_page(city, state, datadir):
    """ Returns the URL of the list of the hotels in a city. Corresponds to
    STEP 1 & 2 of the slides.

    Parameters
    ----------
    city : str

    state : str

    datadir : str


    Returns
    -------
    url : str
        The relative link to the website with the hotels list.

    """
    # Build the request URL
    url = base_url + "city=" + city + "&state=" + state
    # Request the HTML page
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    with open(os.path.join(datadir, city + '-tourism-page.html'), "w") as h:
        h.write(html)

    # Use BeautifulSoup to extract the url for the list of hotels in
    # the city and state we are interested in.

    # For example in this case we need to get the following href
    # <li class="hotels twoLines">
    # <a href="/Hotels-g60745-Boston_Massachusetts-Hotels.html" data-trk="hotels_nav">...</a>
    soup = BeautifulSoup(html)
    li = soup.find("li", {"class": "hotels twoLines"})
    city_url = li.find('a', href=True)
    return city_url['href']


def get_hotellist_page(city_url, page_count, city, datadir='data/'):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.

    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.
    city : str
        The name of the city that we are interested in.
    datadir : str, default is 'data/'
        The directory in which to save the downloaded html.

    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """
    url = base_url + city_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    # Save the webpage
    with open(os.path.join(datadir, city + '-hotelist-' + str(page_count) + '.html'), "w") as h:
        h.write(html)
    return html

def scrape_hotelDetails(url):

    url = base_url + url

    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')

    soup = BeautifulSoup(html, 'html.parser')
    box = soup.findAll('form', {'class' :'review_filter_2col review_filter_radios_2col'} )

    #Gets the rating
    ratings = box[0].findAll('span', {'class': 'compositeCount'} )
    i = 5
    averageRating = 0
    numberExcellent = 0
    total = 0.0
    for r in ratings:

        t = r.text
        if "," in t:
            noComma = t.split(",")
            t = ""
            for n in noComma:
                t += n
        r = int(t)
        total += r
        averageRating += (i * r)

        if i == 5:
            numberExcellent = r

        i -= 1

    averageRating = averageRating / total

    excellent = (numberExcellent / total > 0.60) * 1

    f2.write(","+str(excellent))
    f.write(","+str(averageRating))

    #Gets the number of stars for each category
    stars = box[0].findAll("span", {"class" : "rate sprite-rating_s rating_s"})
    for star in stars:
        star = star.find("img")
        t = star['alt'].split()[0]
        f.write(","+t)
        f2.write(","+t)



    reviews = box[0].findAll("div", {"class" : "filter_connection_wrapper"})
    for review in reviews:
        review = review.find("div", {"class": "value"})
        t =  review.text
        if "," in t:
            noComma = t.split(",")
            t = ""
            for n in noComma:
                t += n

        f.write(","+t)
        f2.write(","+t)

    f2.write("\n")
    f.write("\n")







def parse_hotellist_page(html):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.

    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.

    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """
    soup = BeautifulSoup(html, 'html.parser')
    # Extract hotel name, star rating and number of reviews

    hotel_boxes = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'} )
    if not hotel_boxes:
        log.info("#################################### Option 2 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing_info jfy'})
    if not hotel_boxes:
        log.info("#################################### Option 3 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing easyClear  p13n_imperfect'})

    for hotel_box in hotel_boxes:
        hotel_name = hotel_box.find("a", {"target" : "_blank"}).find(text=True)



        log.info("Hotel name: %s" % hotel_name.strip())

        name = hotel_name.strip()
        if "," in name:
            name = name.split(",")
            newName = ""
            for n in name:
                newName += n

            name = newName

        f.write(name)
        f2.write(name)

        hotel_url = hotel_box.find("a", {"target" : "_blank"})
        hotel_url =  hotel_url['href']

        scrape_hotelDetails(hotel_url)



        stars = hotel_box.find("img", {"class" : "sprite-ratings"})
        if stars:
            log.info("Stars: %s" % stars['alt'].split()[0])

        num_reviews = hotel_box.find("span", {'class': "more"}).findAll(text=True)
        if num_reviews:
            log.info("Number of reviews: %s " % [x for x in num_reviews if "review" in x][0].strip())

    # Get next URL page if exists, otherwise exit
    div = soup.find("div", {"class" : "pagination paginationfillbtm"})
    # check if this is the last page
    if div.find('span', {'class' : 'guiArw pageEndNext'}):
        log.info("We reached last page")
        sys.exit()
    # If not, return the url to the next page
    else:
        href = div.find('a', {'class' : 'guiArw sprite-pageNext '})
        log.info("Next url is %s" % href['href'])
        return href['href']

def scrape_hotels(city, state, datadir='data/'):
    """Runs the main scraper code

    Parameters
    ----------
    city : str
        The name of the city for which to scrape hotels.

    state : str
        The state in which the city is located.

    datadir : str, default is 'data/'
        The directory under which to save the downloaded html.
    """

    # Get current directory
    current_dir = os.getcwd()
    # Create datadir if does not exist
    if not os.path.exists(os.path.join(current_dir, datadir)):
        os.makedirs(os.path.join(current_dir, datadir))

    # Get URL to obtaint the list of hotels in a specific city
    city_url = get_city_page(city, state, datadir)
    c = 0
    while(True):
        c += 1
        html = get_hotellist_page(city_url, c, city, datadir)
        city_url = parse_hotellist_page(html)


def run():

    f = open("hotel_data.csv", "w")
    f2 = open("hotel_data2.csv", "w")

    f.write("Average Rating,Sleep Quality,Location,Rooms,Service,Value,Cleanliness,Families,Couples,Solo,Business\n")
    f2.write("Excellent,Sleep Quality,Location,Rooms,Service,Value,Cleanliness,Families,Couples,Solo,Business\n")

    scrape_hotels('Boston', 'Massachusetts', 'data/')
    f.close()
    f2.close()



if __name__ == "__main__":


    f.write("Average Rating,Sleep Quality,Location,Rooms,Service,Value,Cleanliness,Families,Couples,Solo,Business\n")
    f2.write("Excellent,Sleep Quality,Location,Rooms,Service,Value,Cleanliness,Families,Couples,Solo,Business\n")

    scrape_hotels('Boston', 'Massachusetts', 'data/')
    f.close()
    f2.close()
