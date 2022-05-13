import requests
from urllib.parse import quote
from config import apikey
import json
import matplotlib.pyplot as plt
from PIL import Image
def coords_to_ask(coords):
    return 'geo!{0},{1}'.format(coords[0], coords[1])

def adress_to_geo(adress):
    ask = quote(adress)
    req = json.loads(requests.get('https://geocoder.ls.hereapi.com/6.2/geocode.json?searchtext={0}&gen=9&apiKey={1}'.format(ask, apikey)).content)
    coords = req['Response']['View'][0]['Result'][0]['Location']['DisplayPosition']
    lat, long = coords['Latitude'], coords['Longitude']
    return lat, long

def calculate_route(coords1, coords2):
    req = json.loads(
        requests.get(
            'https://route.ls.hereapi.com/routing/7.2/calculateroute.json?apiKey={0}&waypoint0={1}&waypoint1={2}&departure=now&mode=fastest;publicTransport&combineChange=true'.format(apikey,
                                                                                                                                                                                       coords_to_ask(coords1), coords_to_ask(coords2))).content)
    print(req)
    response = req['response']['route'][0]['summary']
    return response['distance'], response['baseTime']

def get_image(coords1, coords2):
    req = requests.get(
        'https://image.maps.ls.hereapi.com/mia/1.6/routing?apiKey={key}&waypoint0={x1},{y1}&waypoint1={x2},{y2}&poix0={x1},{y1};00a3f2;00a3f2;11;.&poix1={x2},{y2};white;white;11;.&w=400&h=600'.format(
            key=apikey, x1=coords1[0], y1=coords1[1], x2=coords2[0], y2=coords2[1]))
    img = Image.frombytes('L', (399, 399), req.content)
    plt.imshow(img)
    plt.show()
