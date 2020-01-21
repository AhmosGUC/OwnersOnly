#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from flask import Flask, jsonify, request, abort, render_template, redirect ,url_for
import requests
from bs4 import BeautifulSoup
import re
import time

app = Flask(__name__)

# url = "https://www.olx.com.eg/en/properties/apartments-duplex-for-sale/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36"
headers = {'user-agent': user_agent}

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/olxauto')
def olxauto():
    print("Here auto")
    url = make_url(request.args.to_dict())
    n_pages = request.args['n_pages']
    req_dates = request.args['req_dates']
    return redirect(url_for('.crawl_olx', url=url,n_pages=n_pages,req_dates = req_dates))

@app.route('/olx')
def crawl_olx():
    start_time = time.time()
    url = request.args['url']
    n_pages = 1
    try:
        n_pages = int(request.args['n_pages'].encode('utf-8'))
    except:
        print("Error")
    req_dates = request.args['req_dates']

    if ( req_dates == "1" ):
        date_flag=True
    else:
        date_flag=False    

    if url is not None:
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')    

        pager = soup.find_all("div",{"class":"pager"})
        if( pager.__len__() == 1):
            last_page = pager[0].find_all("span",{"class":"item fleft"})
            last_page = last_page[last_page.__len__()-1]
            max_pages = last_page.getText().strip()
        else:
            max_pages = 1
        
        if(n_pages == "4"):
            n_pages = max_pages
        else:       
            n_pages = min([max_pages,n_pages])   

        items_owner = []
        items_broker = []  
        for p in range(1,n_pages+1):
            if(url[-1] == "/"):
                url = url + "?page=" + str(p)
            else:
                url = url + "&page=" + str(p)
            page = requests.get(url, headers=headers)
            soup = BeautifulSoup(page.content, 'html.parser')
            for item in soup.find_all('div', attrs={"class": "ads__item__info"}):
                post_date = item.find_all('p',{"class":"ads__item__date"})[0].contents[0].strip().lower()
                title = item.find_all('a',{"class":"ads__item__ad--title"})[0].get('title').strip()
                if date_flag:
                    if "today" in post_date or "yesterday" in post_date:
                        p = item.find_all('p', attrs={"class": "ads__item__price"})[0]
                        price = p.getText().lower().replace('\t', '').replace('\n', '').replace('negotiable', '').replace('egp',
                                                                                                                            '')
                        loc = item.find_all('p', attrs={"class": "ads__item__location"})[0]
                        location = loc.getText().lower().replace('\t', '').replace('\n', '')
                        link  = item.find_all('a', href=True)[0]
                        item_link = link['href']
                        item_link = item_link.replace(".eg/", ".eg/en/")
                        print(item_link)
                        item_page = requests.get(item_link, headers=headers)
                        soup_page = BeautifulSoup(item_page.content, 'html.parser')

                        info = {
                            "title":title,
                            "url": item_link,
                            "price": price,
                            "location": location,
                            "post_date": post_date
                        }
                        details = item_details_olx(soup_page)             
                        info.update({'details': details })
                        check = details["Broker"]
                        if "Yes" in check:
                            items_broker.append(info)
                        else:
                            items_owner.append(info)      
                else:
                    p = item.find_all('p', attrs={"class": "ads__item__price"})[0]
                    price = p.getText().lower().replace('\t', '').replace('\n', '').replace('negotiable', '').replace('egp',
                                                                                                                        '')
                    loc = item.find_all('p', attrs={"class": "ads__item__location"})[0]
                    location = loc.getText().lower().replace('\t', '').replace('\n', '')
                    link  = item.find_all('a', href=True)[0]
                    item_link = link['href']
                    item_link = item_link.replace(".eg/", ".eg/en/")
                    print(item_link)
                    item_page = requests.get(item_link, headers=headers)
                    soup_page = BeautifulSoup(item_page.content, 'html.parser')

                    info = {
                        "title":title,
                        "url": item_link,
                        "price": price,
                        "location": location,
                        "post_date": post_date
                    }
                    details = item_details_olx(soup_page)             
                    info.update({'details': details })
                    check = details["Broker"]
                    if "Yes" in check:
                        items_broker.append(info)
                    else:
                        items_owner.append(info)      

        end_time = time.time()
        delta_time = end_time-start_time    
        # return jsonify({'Brokers': items_broker, 'Owners' : items_owner, 'count_owners': items_owner.__len__(),'count_brokers': items_broker.__len__(),'atime':delta_time})
        data = [items_owner ,items_broker,items_owner.__len__(),items_broker.__len__(),url]
        return render_template("view.html",data=data)
    else:
        msg = {"error":"missing url query parameter"}
        return jsonify(msg), 400


def item_details_olx(soup):
    """
    Type
    """
    array = []
    dict = {}
    
    ad_desc = soup.find_all('div',{'id':'textContent'})[0]
    ad_desc = ad_desc.getText().replace('\n'," ").strip().lower()

    ad_desc_ar = ad_desc.encode("utf-8")

    dict.update({"description":ad_desc})
    if "owner" in ad_desc :
        dict.update({"contain keywords en":"yes"})
    else:
        dict.update({"contain keywords en":"no"})
    
    if b'\xd9\x85\xd8\xa7\xd9\x84\xd9\x83' in ad_desc_ar :
        dict.update({"contain keywords ar":"yes"})
    else:
        dict.update({"contain keywords ar":"no"})
    
    
    try:
        user_box = soup.find_all('div',{"class":"user-box__info"})[0]
        user_link = user_box.find_all('a')[0]
        user_link = user_link.get('href').__str__()

        user_name = user_box.find_all('p',{"class":"user-box__info__name"})[0].getText()
        
        dict.update({"user profile":user_link})
        dict.update({"user name":user_name})

        item_page = requests.get(user_link, headers=headers)
        soup_page = BeautifulSoup(item_page.content, 'html.parser')

        ad_list = soup_page.find_all('div',{"class":"ads--list"})[0]
        ad_list = ad_list.find_all('div',{"class","ads__item"})
        
        dict.update({"number of ads":ad_list.__len__()})

        if(dict["number of ads"]>10):
            dict.update({"Broker":"Yes"})
        else:
            dict.update({"Broker":"No"})
    except IndexError:
        dict.update({"error":"IndexError"})
    except :
        dict.update({"error":"unknown"})


    return dict

def make_url(args):
    category = args['category']
    compound = args['compound']
    price_from = args['pricefrom']
    price_to = args['priceto']
    area_from = args['areafrom']
    area_to = args['areato']
    keyword = args['keyword']
    payment_option = args['paymentoption']
    location = args['location']

    url = "https://www.olx.com.eg/en/properties/"
    url = url + conv_cat(category)
    if(not location =="any"):
        url = url + location +"/?"
    else:
        url = url + "?"    
    if(not compound == 'all'):
        url= url+ "&search[filter_enum_compound]="+compound
    if(not price_from == ""):
        url= url + "&search[filter_float_price:from]="+price_from
    if(not price_to == ""):
        url= url + "&search[filter_float_price:to]="+price_to
    if(not area_from == ""):
        url= url + "&search[filter_float_area:from]="+area_from
    if(not area_to == ""):
        url= url + "&search[filter_float_area:to]="+area_to
    if(not payment_option == "123"):
        url= url + "&search[filter_enum_payment_options]="+payment_option
    if(not keyword == ""):
        url= url + "&q="+keyword

    print("Here url",url)
    return url

def conv_cat(option):
    ret = ""
    if( option == "1"):
        ret = "apartments-duplex-for-sale/"
    elif( option == "2" ):
        ret = "apartments-duplex-for-rent/"    
    elif( option == "3" ):    
        ret = "villas-for-sale/"    
    elif( option == "4" ):    
        ret = "villas-for-rent/"    
    elif( option == "5" ):    
        ret = "vacation-homes-for-sale/"    
    elif( option == "6" ):    
        ret = "vacation-homes-for-rent/"    
    elif( option == "7" ):    
        ret = "commercial-for-sale/"    
    elif( option == "8" ):    
        ret = "commercial-for-rent/"    
    elif( option == "9" ):    
        ret = "buildings-lands-other/"    
    else:    
        ret = ""
    return ret        

if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(debug=True, host='0.0.0.0', port=3000)
