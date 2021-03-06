#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, abort, render_template, redirect, url_for, session, flash
import requests
from bs4 import BeautifulSoup
import re
import time
import logging
import os
import datetime

app = Flask(__name__)
app.secret_key = '*9->q+2PEd[%&_Rba8T-*Qx;;4x2!]9X")9;!R6FtkPLGs2V^LWLU>92yvh.xJUq'
log = logging.getLogger('werkzeug')
log.disabled = True

# url = "https://www.olx.com.eg/en/properties/apartments-duplex-for-sale/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36"
headers = {'user-agent': user_agent}


@app.route('/login', methods=['POST'])
def do_admin_login():
    date_val = datetime.datetime.now()
    var_val = date_val.strftime("%m")
    pass_val = "@0wner$@lloWed"+var_val
    if request.form['password'] == pass_val and request.form['username'].lower() == 'stars':
        if request.form.get('remember'):
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(weeks=1)
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return home()


@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template("home.html")


@app.route('/olxauto')
def olxauto():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        url = make_url(request.args.to_dict())

        n_pages = request.args['n_pages']
        req_dates = request.args['req_dates']
        threshold = request.args['threshold']
        return redirect(url_for('.view_page', url=url, n_pages=n_pages, req_dates=req_dates, threshold=threshold))


@app.route("/view")
def view_page():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('view.html')


@app.route('/olx')
def crawl_olx():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        start_time = time.time()
        # url = str(request.args['url']).replace("25874","?").replace("47852","&").replace('\"','')
        url = str(request.query_string.decode("utf-8").split("url=", 1)[1])
        app.logger.info(url)
        threshold = int(request.args['threshold'])
        n_pages = "1"
        try:
            n_pages = str(request.args['n_pages'].encode('utf-8'))
            url = url + "&page="+str(n_pages)
        except:
            url = url + "&page=1"
            print("Error")
        req_dates = request.args['req_dates']

        if (req_dates == "1"):
            date_flag = True
        else:
            date_flag = False

        if url is not None:
            app.logger.info(url)
            # if (url[-1] == "\/"):
            #     url += "?page=" + n_pages
            # elif (url[-1] == "?"):
            #     url += "page=" + n_pages
            # else:
            #     url += "&page=" + n_pages

            page = requests.get(url, headers=headers)
            soup = BeautifulSoup(page.content, 'html.parser')
            # app.logger.info(soup)
            response = []
            list_soup = soup.find_all(
                'div', attrs={"class": "ads__item__info"})
            # app.logger.info("soup length:")
            # app.logger.info(list_soup.__len__())
            for item in list_soup:
                post_date = item.find_all('p', {"class": "ads__item__date"})[
                    0].contents[0].strip().lower()
                title = item.find_all(
                    'a', {"class": "ads__item__ad--title"})[0].get('title').strip()
                # app.logger.info("title")
                # app.logger.info(title)
                if date_flag:
                    # app.logger.info("Date today")
                    if "today" in post_date or "yesterday" in post_date:
                        p = item.find_all(
                            'p', attrs={"class": "ads__item__price"})[0]
                        price = p.getText().lower().replace('\t', '').replace(
                            '\n', '').replace('negotiable', '').replace('egp', '')
                        loc = item.find_all(
                            'p', attrs={"class": "ads__item__location"})[0]
                        location = loc.getText().lower().replace('\t', '').replace('\n', '')
                        link = item.find_all('a', href=True)[0]
                        item_link = link['href']
                        item_link = item_link.replace(".eg/", ".eg/en/")
                        response.append(
                            [item_link, location, price, post_date, title])
                        # app.logger.info("item_link")
                        # app.logger.info(item_link)
                else:
                    # app.logger.info("Not today")
                    p = item.find_all(
                        'p', attrs={"class": "ads__item__price"})[0]
                    price = p.getText().lower().replace('\t', '').replace(
                        '\n', '').replace('negotiable', '').replace('egp', '')
                    loc = item.find_all(
                        'p', attrs={"class": "ads__item__location"})[0]
                    location = loc.getText().lower().replace('\t', '').replace('\n', '')
                    link = item.find_all('a', href=True)[0]
                    item_link = link['href']
                    item_link = item_link.replace(".eg/", ".eg/en/")
                    response.append(
                        [item_link, location, price, post_date, title])
                    # app.logger.info("item_link")
                    # app.logger.info(item_link)

            # app.logger.info(response.__len__())
            return jsonify(response)
        else:
            msg = {"error": "missing url query parameter"}
            return jsonify(msg), 400


@app.route("/getpages")
def pages():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        # url = str(request.args['url'])
        url = request.query_string.decode("utf-8").split("url=")[1]
        app.logger.info(url)
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')

        pager = soup.find_all("div", {"class": "pager"})
        if(pager.__len__() == 1):
            last_page = pager[0].find_all("span", {"class": "item fleft"})
            last_page = last_page[last_page.__len__()-1]
            max_pages = int(last_page.getText().strip())
        else:
            max_pages = 1
        app.logger.info(url)
        app.logger.info(max_pages)
        return jsonify(max_pages)


@app.route("/property")
def property_details():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        url = request.args['url']
        threshold = int(request.args['threshold'])
        item_page = requests.get(url, headers=headers)
        soup_page = BeautifulSoup(item_page.content, 'html.parser')

        dict_details = item_details_olx(soup_page, threshold)

        return jsonify(dict_details)


def item_details_olx(soup, threshold):
    """
    Type
    """
    array = []
    dict = {}

    ad_desc = soup.find_all('div', {'id': 'textContent'})[0]
    ad_desc = ad_desc.getText().replace('\n', " ").strip().lower()

    dict.update({"description": ad_desc})

    try:
        user_box = soup.find_all('div', {"class": "user-box__info"})[0]
        user_link = user_box.find_all('a')[0]
        user_link = user_link.get('href').__str__()

        user_name = user_box.find_all(
            'p', {"class": "user-box__info__name"})[0].getText()

        dict.update({"user profile": user_link})
        dict.update({"user name": user_name})

        item_page = requests.get(user_link, headers=headers)
        soup_page = BeautifulSoup(item_page.content, 'html.parser')

        ad_list = soup_page.find_all('div', {"class": "ads--list"})[0]
        ad_list = ad_list.find_all('div', {"class", "ads__item"})

        dict.update({"number of ads": ad_list.__len__()})

        if(dict["number of ads"] > threshold):
            dict.update({"Broker": "Yes"})
        else:
            dict.update({"Broker": "No"})
    except IndexError:
        dict.update({"error": "IndexError"})
    except:
        dict.update({"error": "unknown"})

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
    if(not location == "any"):
        url = url + location + "/?"
    else:
        url = url + "?"
    if(not compound == 'all'):
        url = url + "search[filter_enum_compound]="+compound+"&"
    if(not price_from == ""):
        url = url + "search[filter_float_price:from]="+price_from+"&"
    if(not price_to == ""):
        url = url + "search[filter_float_price:to]="+price_to+"&"
    if(not area_from == ""):
        url = url + "search[filter_float_area:from]="+area_from+"&"
    if(not area_to == ""):
        url = url + "search[filter_float_area:to]="+area_to+"&"
    if(not payment_option == "123"):
        url = url + "search[filter_enum_payment_options]="+payment_option+"&"
    if(not keyword == ""):
        url = url + "q="+keyword+"&"

    return url


def conv_cat(option):
    ret = ""
    if(option == "1"):
        ret = "apartments-duplex-for-sale/"
    elif(option == "2"):
        ret = "apartments-duplex-for-rent/"
    elif(option == "3"):
        ret = "villas-for-sale/"
    elif(option == "4"):
        ret = "villas-for-rent/"
    elif(option == "5"):
        ret = "vacation-homes-for-sale/"
    elif(option == "6"):
        ret = "vacation-homes-for-rent/"
    elif(option == "7"):
        ret = "commercial-for-sale/"
    elif(option == "8"):
        ret = "commercial-for-rent/"
    elif(option == "9"):
        ret = "buildings-lands-other/"
    else:
        ret = ""
    return ret


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    # app.secret_key = os.urandom(12)
    app.secret_key = '*9->q+2PEd[%&_Rba8T-*Qx;;4x2!]9X")9;!R6FtkPLGs2V^LWLU>92yvh.xJUq'
    app.run(debug=True, host='0.0.0.0', port=3000)
