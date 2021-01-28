import requests
import json
 
API_KEY = ''
with open('api_key.dat') as f:
    API_KEY = f.readline()

def get_accountId(user_name):
    data = requests.get('https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user_name+'?api_key='+API_KEY).text
    return json.loads(data)['accountId']

def get_puuid(user_name):
    data = requests.get('https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user_name+'?api_key='+API_KEY).text
    return json.loads(data)['puuid']

def get_encrypedId(user_name):
    data = requests.get('https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user_name+'?api_key='+API_KEY).text
    return json.loads(data)['id']

def get_user_level(user_name):
    data = requests.get('https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user_name+'?api_key='+API_KEY).text
    return json.loads(data)['puuid']

def get_current_match(user_name):
    data = requests.get('https://kr.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/'+get_accountId(user_name)+'?api_key='+API_KEY).text
    return json.loads(data)


def get_image(img_url):    
    return requests.get(img_url)

user_name = ''
print(get_encrypedId(user_name))
print(get_accountId(user_name))
print(get_puuid(user_name))
