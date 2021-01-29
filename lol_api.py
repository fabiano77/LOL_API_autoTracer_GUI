import requests
import json
import os

'''
[This program] isn't endorsed by Riot Games and doesn't reflect the views or opinions of 
Riot Games or anyone officially involved in producing or managing Riot Games properties.
Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
''' 
API_KEY = ''
with open('api_key.dat', 'r') as f:
    API_KEY = f.readline()

def get_user_json(user_name):
    '''
    "id": "~~~",
    "accountId": "~~~",
    "puuid": "~~~",
    "name": "user_name",
    "profileIconId": 23,
    "revisionDate": 1611474081000,
    "summonerLevel": 330
    '''
    data_json = json.loads(requests.get('https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user_name+'?api_key='+API_KEY).text)
    if 'status' in data_json:
        print('get_user_json, api error :', data_json['status']['status_code'])
        return data_json['status']['status_code']
    return data_json

def get_user_league_info(encryptedId):
    '''
    리스트 -> 딕셔너리 -> (티어, 랭크 등등)
    [
        {
        "leagueId": "ca4f10d3-08ce-4b39-aee7-b2fd5225f214",
        "queueType": "RANKED_SOLO_5x5",
        "tier": "GOLD",
        "rank": "III",
        "summonerId": "w9U4kY2yGAWVVKJL98h8fjmzoulF0-KeXuQ24HVWz9CtwJo",
        "summonerName": "26세고졸무직공익",
        "leaguePoints": 49,
        "wins": 11,
        "losses": 15,
        "veteran": false,
        "inactive": false,
        "freshBlood": false,
        "hotStreak": false
        }
    ]
    '''
    data_json = json.loads(requests.get('https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/'+encryptedId+'?api_key='+API_KEY).text)
    if 'status' in data_json:
        print('get_user_league_info, api error :', data_json['status']['status_code'])
        return data_json['status']['status_code']
    return data_json

def get_user_solo_rank_info(encryptedId):
    data_league_list = json.loads(requests.get('https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/'+encryptedId+'?api_key='+API_KEY).text)
    # 언랭 구별
    if len(data_league_list) == 0:
        return 'Unranked'
    # 자유랭 구별
    data_rank = data_league_list[0]
    if data_league_list[0]['queueType'] == 'RANKED_FLEX_SR':
        return '자유 '+data_rank['tier']+' '+data_rank['rank']+' '+str(data_rank['leaguePoints'])
    return data_rank['tier']+' '+data_rank['rank']+' '+str(data_rank['leaguePoints'])

def get_current_match(user_name):
    # api 2회 사용.
    # 존재하는 key 목록:
    # gameId : 매치 고유숫자
    # mapId : 맵의 id(11, )
    # gameMode : 게임 모드(CLASSIC, )
    # gameType : 게임 타입(MATCHED_GAME, )
    # gameQueueConfigId : 대기열 유형(?)
    # participants : 참가자명단 list 타입으로 존재 
        # 내부는 dict 타입과 list타입 혼재하여 존재
        # dict 타입
        # teamId : 팀 정보(100, 200)
        # spellId1 : 스펠1
        # spellId2 : 스펠2
        # championId : 챔피언(23, 164, ...)
        # profileIconID : 프로필 아이콘(4794등, )
        # summonerName : 닉네임
        # bot : False
        
    # observers : 관전 정보
    # platformId : 게임실행되는 플랫폼 ID
    # bannedChampions : 금지된 챔피언
    # gameStartTime : 게임 시작 시간 [ms]
    # gameLength : 게임 경과 시간[s]
    user_id = get_user_json(user_name)['id']
    if len(user_id) < 4:
        print('id error')
        return None
    data_json = json.loads(requests.get('https://kr.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/'+user_id+'?api_key='+API_KEY).text)
    if 'status' in data_json:
        if data_json['status']['status_code'] == 404:
            # 게임 미진행중
            return False
        # 그외 error code
        print('api error :', data_json['status']['status_code'])
        return data_json['status']['status_code']
    return data_json

def get_champ_json():
    cache = dict()
    with open('cache.json', 'r', encoding='utf-8') as f:
        cache = json.load(f)

    champ_json = dict()
    if 'champ' in cache:
        champ_json = cache['champ']
    else:
        champ_json = json.loads(requests.get('http://ddragon.leagueoflegends.com/cdn/11.2.1/data/en_US/champion.json').text)
        cache['champ'] = champ_json
        with open('cache.json', 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent='\t')
    return champ_json

def get_champ_name(champ_key):
    champ_key = str(champ_key)
    champ_json = get_champ_json()
    target_name = ''
    for champ_name in champ_json['data']:
        if champ_json['data'][champ_name]['key'] == champ_key:
            target_name = champ_name
            break
    return target_name

icon_storage = {}
def get_profileIcon(icon_key):
    icon_key = str(icon_key)
    file_path_name = '.\\cache\\profile_icon\\'+icon_key+'.png'
    img_raw = 0
    if os.path.isfile(file_path_name):
        with open(file_path_name, 'rb') as img:
            img_raw = img.read()
    else:
        img_url = 'http://ddragon.leagueoflegends.com/cdn/11.2.1/img/profileicon/'+icon_key+'.png'
        img_raw = requests.get(img_url).content
        with open(file_path_name, 'wb') as img:
            img.write(img_raw)
    return img_raw

def get_champ_image(champ_name):
    img_url = 'http://ddragon.leagueoflegends.com/cdn/11.2.1/img/champion/'+champ_name+'.png'
    img_raw = requests.get(img_url).content
    return img_raw

# def get_

if __name__ == '__main__':
    user_name = '엉덩국 갱승제로'
    
    user_info = get_user_json(user_name)
    print('puuid :',  user_info['puuid'])
    print('encrypedId :', user_info['id'])
    print('accountId :', user_info['accountId'])
    print('icon key', user_info['profileIconId'])
    print('user rank : ', get_user_solo_rank_info(user_info['id']))

    # print('match info : ', get_current_match(user_name))
    match_data = get_current_match(user_name)
    for item in match_data:
        print(item, match_data[item])
    for i in range(10):
        if match_data['participants'][i]['summonerName'] == user_name:
            champ_key = match_data['participants'][i]['championId']
            print(get_champ_name(champ_key))

