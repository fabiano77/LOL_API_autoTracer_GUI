import requests
import json
import os
import time
import datetime

'''
[This program] isn't endorsed by Riot Games and doesn't reflect the views or opinions of 
Riot Games or anyone officially involved in producing or managing Riot Games properties.
Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
''' 


API_KEY = ''        # web site getting API key : https://developer.riotgames.com/
with open('api_key.dat', 'r') as f:
    API_KEY = f.readline()

def check_api():
    'return status code'
    r = requests.get('https://kr.api.riotgames.com/lol/status/v4/platform-data?api_key='+API_KEY)
    return r.status_code

def get_user_json(user_name):
    user_name = user_name.replace(" ", "")
    user_cache = dict()
    user_data = dict()
    # 캐시파일 불러오기
    if os.path.isfile('.\\cache\\user_cache.json'):
        with open('.\\cache\\user_cache.json', 'r', encoding='utf-8') as f:
            user_cache = json.load(f)

    if user_name in user_cache and 'user_info' in user_cache[user_name] : # and cacheDate와 시간차이 확인
        # 찾으려고 하는 유저 정보가 있다면
        user_data = user_cache[user_name]['user_info']
    else:
        # 찾으려고 하는 유저 정보다 없다면
        r = requests.get('https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user_name+'?api_key='+API_KEY)
        if r.status_code != 200:
            # api 에러 코드
            print('get_user_json, api error :', r.status_code)
            return r.status_code

        user_data = json.loads(r.text)
        # 캐시파일에 저장
        del(user_data['revisionDate'])
        del(user_data['profileIconId'])
        del(user_data['summonerLevel'])
        user_cache[user_name] = dict()
        user_cache[user_name]['user_info'] = user_data
        user_cache[user_name]['user_info']['cacheDate'] = time.time()
        with open('.\\cache\\user_cache.json', 'w', encoding='utf-8') as f:
            json.dump(user_cache, f, indent='\t', ensure_ascii=False)

    return user_data

def get_user_solo_rank_info(user_name):
    user_tier = ''
    user_cache = dict()
    if os.path.isfile('.\\cache\\user_cache.json'):
        with open('.\\cache\\user_cache.json', 'r', encoding='utf-8') as f:
            user_cache = json.load(f)

    dt = datetime.timedelta()
    if user_name in user_cache and 'user_tier' in user_cache[user_name]:
        sec = time.time() - user_cache[user_name]['user_tier']['cacheDate']
        dt = datetime.timedelta(seconds = sec)

    if user_name in user_cache and 'user_tier' in user_cache[user_name] and dt < datetime.timedelta(hours = 1):
        # 찾으려고 하는 유저 티어 정보가 있고 시간이 오래되지않음(1시간)
            user_tier = user_cache[user_name]['user_tier']['tier']
    else:
        # 찾으려고 하는 유저 티어가 없거나 시간이 오래됐으면
        r = requests.get('https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/'+user_cache[user_name]['user_info']['id']+'?api_key='+API_KEY)
        data_league_list = json.loads(r.text)
        if r.status_code != 200:
            print('get_user_solo_rank_info, api error :', r.status_code)
            return r.status_code
        
        # 언랭 구별
        if len(data_league_list) == 0:
            user_tier = 'Unranked'
        # 자유랭 구별
        else:
            data_rank = data_league_list[0]
            for data_league in data_league_list:
                if data_league['queueType'] == 'RANKED_SOLO_5x5':
                    data_rank = data_league
            if data_rank['queueType'] == 'RANKED_FLEX_SR':
                user_tier += '자유 '
            user_tier = user_tier + data_rank['tier']+' '+data_rank['rank']+' '+str(data_rank['leaguePoints'])
        user_cache[user_name]['user_tier'] = dict()
        user_cache[user_name]['user_tier']['tier'] = user_tier
        user_cache[user_name]['user_tier']['cacheDate'] = time.time()
        with open('.\\cache\\user_cache.json', 'w', encoding='utf-8') as f:
            json.dump(user_cache, f, indent='\t', ensure_ascii=False)

    return user_tier

def get_current_match(encryptedId):
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
    # observers : 관전 정보
    # platformId : 게임실행되는 플랫폼 ID
    # bannedChampions : 금지된 챔피언
    # gameStartTime : 게임 시작 시간 [ms]
    # gameLength : 게임 경과 시간[s]
    r = requests.get('https://kr.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/'+encryptedId+'?api_key='+API_KEY)
    if r.status_code != 200:
        if r.status_code == 404:
            # 게임 미진행중
            return False
        # 그외 error code
        print('api error :', r.status_code)
        return r.status_code
    
    data_json = json.loads(r.text)
    return data_json

def get_champ_json():
    cache = dict()
    with open('.\\cache\\champ.json', 'r', encoding='utf-8') as f:
        cache = json.load(f)

    champ_json = dict()
    if 'champ' in cache:
        champ_json = cache['champ']
    else:
        champ_json = json.loads(requests.get('http://ddragon.leagueoflegends.com/cdn/11.2.1/data/en_US/champion.json').text)
        cache['champ'] = champ_json
        with open('.\\cache\\champ.json', 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent='\t', ensure_ascii=False)
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
    img_raw = bytes()
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
    '평균 소요시간 0.015[s]'
    img_url = 'http://ddragon.leagueoflegends.com/cdn/11.2.1/img/champion/'+champ_name+'.png'
    img_raw = requests.get(img_url).content
    return img_raw

if __name__ == '__main__':
    user_name = 'alphabet c'
    print('user name :', user_name)
    time_1 = time.time()
    user_info = get_user_json(user_name)
    print('puuid :',  user_info['puuid'])
    print('encrypedId :', user_info['id'])
    print('accountId :', user_info['accountId'])
    print(f'소요 시간 : {time.time()-time_1:0.4f}[s]')
    time_1 = time.time()
    print('user rank : ', get_user_solo_rank_info(user_name))
    print(f'소요 시간 : {time.time()-time_1:0.4f}[s]')
    time_1 = time.time()

    match_data = get_current_match(user_info['id'])
    print(f'소요 시간 : {time.time()-time_1:0.4f}[s]')
    time_1 = time.time()


    user_cache = dict()
    with open('.\\cache\\user_cache.json', 'r', encoding='utf-8') as f:
        user_cache = json.load(f)




    # for item in match_data:
    #     print(item, match_data[item])
    # for i in range(10):
    #     if match_data['participants'][i]['summonerName'] == user_name:
    #         champ_key = match_data['participants'][i]['championId']
    #         print(get_champ_name(champ_key))

