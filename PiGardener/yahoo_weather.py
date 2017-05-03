import urllib3, urllib, json
import urllib.request

def get_weather(place):
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = "select item.condition.temp, atmosphere.humidity from weather.forecast where woeid in (select woeid from geo.places(1) where text=\""+place+"\")"
    yql_url = baseurl + urllib.parse.urlencode({'q':yql_query}) + "&format=json"
    result = urllib.request.urlopen(yql_url).read().decode('utf8')
    data = json.loads(result)
    return (data['query']['results']['channel']['item']['condition']['temp'], data['query']['results']['channel']['atmosphere']['humidity'])
