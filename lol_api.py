import requests
import json
import os
import sys
import time
import datetime
import asyncio
'''
[This program] isn't endorsed by Riot Games and doesn't reflect the views or opinions of 
Riot Games or anyone officially involved in producing or managing Riot Games properties.
Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
''' 

def data_path(relative_path):
    # ---디버깅용---
    # try:
    #     base_path = sys._MEIPASS
    # except Exception:
    #     base_path = os.path.abspath(".")
    # ---배포용---
    relative_path = relative_path.lstrip('.\\')
    base_path = os.path.expanduser('~\\lol_autoTracer_gui\\')
    return os.path.join(base_path, relative_path)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

non_user_list = []
last_api_error = 0
API_KEY = ''        # web site getting API key : https://developer.riotgames.com/
if os.path.isfile(data_path('api_key.dat')):
    with open(data_path('api_key.dat'), 'r') as f:
        API_KEY = f.readline()
# print('api key =', API_KEY)
# print(data_path('api_key.dat'))

api_cnt = int()
def check_api(key = API_KEY):
    global last_api_error
    'return status code'
    r = requests.get('https://kr.api.riotgames.com/lol/status/v4/platform-data?api_key='+key)
    if r.status_code != 200:
        last_api_error = r.status_code
        print('check_api:', r.status_code)
    return r.status_code

def get_user_json(user_name):
    global last_api_error
    user_name = user_name.replace(" ", "").lower()
    user_cache = dict()
    user_data = dict()
    # 캐시파일 불러오기
    if os.path.isfile(data_path('.\\cache\\user_cache.json')):
        with open(data_path('.\\cache\\user_cache.json'), 'r', encoding='utf-8') as f:
            user_cache = json.load(f)

    if user_name in user_cache and 'user_info' in user_cache[user_name] : # and cacheDate와 시간차이 확인
        # 찾으려고 하는 유저 정보가 있다면
        user_data = user_cache[user_name]['user_info']
    else:
        # 찾으려고 하는 유저 정보가 없다면
        print('use API')
        r = requests.get('https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user_name+'?api_key='+API_KEY)
        if r.status_code != 200:
            # api 에러 코드
            last_api_error = r.status_code
            print(f'get_user_json, user_name:{user_name}, api error :', r.status_code)
            return r.status_code

        user_data = json.loads(r.text)
        # 캐시파일에 저장
        del(user_data['revisionDate'])
        del(user_data['profileIconId'])
        del(user_data['summonerLevel'])
        user_cache[user_name] = dict()
        user_cache[user_name]['user_info'] = user_data
        user_cache[user_name]['user_info']['cacheDate'] = time.time()
        with open(data_path('.\\cache\\user_cache.json'), 'w', encoding='utf-8') as f:
            json.dump(user_cache, f, indent='\t', ensure_ascii=False)

    return user_data

def get_rank_json(user_name):
    global last_api_error
    user_name = user_name.replace(" ", "").lower()
    user_cache = dict()
    if os.path.isfile(data_path('.\\cache\\user_cache.json')):
        with open(resource_path('.\\cache\\user_cache.json'), 'r', encoding='utf-8') as f:
            user_cache = json.load(f)

    dt = datetime.timedelta()
    if user_name in user_cache and 'rank_info' in user_cache[user_name]:
        dt = datetime.timedelta(seconds = time.time() - user_cache[user_name]['rank_info']['cacheDate'])
        if  dt < datetime.timedelta(hours = 1):
            # 찾으려고 하는 유저 티어 정보가 있고 시간이 오래되지않음(1시간)
            return user_cache[user_name]['rank_info']['data']
    
    # 찾으려고 하는 유저 티어가 없거나 시간이 오래됐으면
    r = requests.get('https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/'+user_cache[user_name]['user_info']['id']+'?api_key='+API_KEY)
    rank_data = json.loads(r.text)
    if r.status_code != 200:
        print('get_user_solo_rank_info, api error :', r.status_code)
        last_api_error = r.status_code
        return r.status_code
    
    user_cache[user_name]['rank_info'] = dict()
    user_cache[user_name]['rank_info']['data'] = rank_data
    user_cache[user_name]['rank_info']['cacheDate'] = time.time()
    with open(data_path('.\\cache\\user_cache.json'), 'w', encoding='utf-8') as f:
            json.dump(user_cache, f, indent='\t', ensure_ascii=False)
    return rank_data

def get_user_solo_rank_info(rank_list):
    # 언랭 구별
    user_tier = ''
    if len(rank_list) == 0:
        user_tier = 'Unranked'
    # 자유랭 구별
    else:
        data_rank = rank_list[0]
        for data_league in rank_list:
            # 솔로랭크 우선 순위
            if data_league['queueType'] == 'RANKED_SOLO_5x5':
                data_rank = data_league
        if data_rank['queueType'] == 'RANKED_FLEX_SR':
            user_tier += '자유 '
        user_tier = user_tier + data_rank['tier'].lower().capitalize()+' '+data_rank['rank']+' '+str(data_rank['leaguePoints'])
    return user_tier

def get_current_match(encryptedId):
    global last_api_error
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
        last_api_error = r.status_code
        print('api error :', r.status_code)
        return r.status_code
    
    data_json = json.loads(r.text)
    return data_json

def get_champ_json():
    cache = dict()
    if os.path.isfile(data_path('.\\cache\\champ.json')):
        with open(data_path('.\\cache\\champ.json'), 'r', encoding='utf-8') as f:
            cache = json.load(f)

    champ_json = dict()
    if 'champ' in cache:
        champ_json = cache['champ']
    else:
        champ_json = json.loads(requests.get('http://ddragon.leagueoflegends.com/cdn/11.2.1/data/en_US/champion.json').text)
        cache['champ'] = champ_json
        with open(data_path('.\\cache\\champ.json'), 'w', encoding='utf-8') as f:
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
    file_path_name = data_path('.\\cache\\profile_icon\\'+icon_key+'.png')
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

def get_queue_type(match_data):
    if 'gameQueueConfigId' not in match_data:
        return '  Custom '
    queue_id = match_data['gameQueueConfigId']
    if queue_id == 420:
        return '솔로 랭크'
    elif queue_id == 430:
        return '일반 게임'
    elif queue_id == 440:
        return '자유 랭크'
    elif queue_id == 450:
        return '칼바람 나락'
    elif queue_id == 400:
        return '일반 선택'
    elif queue_id == 900:
        return ' URF 모드'
    elif queue_id//100 == 8:
        return ' bot 전투'
    elif queue_id == 0:
        return '  Custom '
    else:
        return ' Unknown '

def get_win_cnt(rank_data):
    # 찐 코드
    if len(rank_data) == 0:
        # 기록 없음
        ret = '기록 없음'
        return f'{ret:>7s}'
    data = rank_data[0]
    for item in rank_data:
        # 솔랭 우선순위
        if item['queueType'] == 'RANKED_SOLO_5x5':
            data = item
            break
    
    wins = data['wins']
    losses = data['losses']
    win_loss = f'{wins:>3d}승{losses:>3d}패'
    return f'{win_loss:>9s}'

async def __async_get_user_info(user_name):
    global loop
    global api_cnt
    global last_api_error
    api_cnt += 1
    # data = await loop.run_in_executor(None, get_func, user_name)    # run_in_executor 사용
    # 대신 request 하는 것으로.

    user_name = user_name.replace(" ", "").lower()
    user_data = dict()
    url = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user_name+'?api_key='+API_KEY
    r = await loop.run_in_executor(None, requests.get, url)    # run_in_executor 사용
    if r.status_code != 200:
        # api 에러 코드
        print(f'async_get_user_info, user_name:{user_name}, api error :', r.status_code)
        if r.status_code == 404:
            non_user_list.append(user_name)
        last_api_error = r.status_code
        return r.status_code

    user_data = json.loads(r.text)
    return user_data

async def __async_get_user_rank(user_name):
    global loop
    global user_cache
    global api_cnt
    api_cnt += 1

    user_name = user_name.replace(" ", "").lower()
    user_data = dict()
    if user_name not in user_cache:
        return 404
    url = 'https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/'+user_cache[user_name]['user_info']['id']+'?api_key='+API_KEY
    r = await loop.run_in_executor(None, requests.get, url)    # run_in_executor 사용
    if r.status_code != 200:
        # api 에러 코드
        print(f'async_get_user_rank, user_name:{user_name}, api error :', r.status_code)
        return r.status_code

    user_data = json.loads(r.text)
    return user_data

async def __async_get_user(user_list):
    global user_cache
    global api_cnt
    user_cache = dict()

    if os.path.isfile(data_path('.\\cache\\user_cache.json')):
        # 캐시 불러오기
        with open(data_path('.\\cache\\user_cache.json'), 'r', encoding='utf-8') as f:
            user_cache = json.load(f)

    new_info_user_list = []
    new_rank_user_list = []
    for user in user_list:
        user = user.replace(" ", "").lower()
        if user not in user_cache:
            # 데이터베이스에 없다면
            new_info_user_list.append(user)
            new_rank_user_list.append(user)
        else:
            if 'user_info' not in user_cache[user]:
                new_info_user_list.append(user)
            if 'rank_info' not in user_cache[user]:
                new_rank_user_list.append(user)
            else:
                dt = datetime.timedelta(seconds = time.time() - user_cache[user]['rank_info']['cacheDate'])
                if  dt > datetime.timedelta(hours = 1):
                    new_rank_user_list.append(user)
            
    new_info_datas = []
    if new_info_user_list:
        new_info_user_list_chunked = list_chunk(new_info_user_list, 19)
        new_info_datas_chunked = []
        futures_info = []
        for num, lst in enumerate(new_info_user_list_chunked):
            for user_name in lst:
                futures_info.append(asyncio.ensure_future(__async_get_user_info(user_name)))
            new_info_datas_chunked.append(await asyncio.gather(*futures_info))
            # print('new_info_user_list', len(new_info_user_list), 'new_info_user_list_chunked', len(new_info_user_list_chunked))
            if len(new_info_user_list+new_rank_user_list) >= 20:
                time.sleep(1.2)
        for lst in new_info_datas_chunked:
            new_info_datas += lst
        # if num%10 == 9:
        #     time.sleep(1)
        # new_info_datas = await asyncio.gather(*futures_info)                # 결과를 한꺼번에 가져옴
        for data in new_info_datas:
            if type(data) == int:
                continue
            user_name = data['name'].replace(" ", "").lower()
            if user_name not in user_cache:
                user_cache[user_name] = {}
            user_cache[user_name]['user_info'] = data
            user_cache[user_name]['user_info']['cacheDate'] = time.time()
    
    new_rank_datas = []
    if new_rank_user_list:
        new_rank_user_list_chunked = list_chunk(new_rank_user_list, 19)
        new_rank_datas_chunked = []
        futures_rank = []
        for num, lst in enumerate(new_rank_user_list_chunked):
            for user_name in lst:
                futures_rank.append(asyncio.ensure_future(__async_get_user_rank(user_name)))
            new_rank_datas_chunked.append(await asyncio.gather(*futures_rank))
            # print('new_rank_user_list', len(new_rank_user_list), 'new_rank_user_list_chunked', len(new_info_datas_chunked))
            if len(new_rank_user_list) >= 20 and num != len(new_rank_user_list_chunked):
                time.sleep(1.2)
        for lst in new_rank_datas_chunked:
            new_rank_datas += lst
        # new_rank_datas = await asyncio.gather(*futures_rank)                # 결과를 한꺼번에 가져옴
        for data in new_rank_datas:
            if type(data) == int:
                continue
            if len(data):
                user_name = data[0]['summonerName'].replace(" ", "").lower()
                user_cache[user_name]['rank_info'] = {}
                user_cache[user_name]['rank_info']['data'] = data
                user_cache[user_name]['rank_info']['cacheDate'] = time.time()
    
    for user in new_rank_user_list:
        user = user.replace(" ", "").lower()
        if user not in user_cache:
            continue
        if 'rank_info' not in user_cache[user]:
            user_cache[user]['rank_info'] = {}
            user_cache[user]['rank_info']['data'] = []
            user_cache[user]['rank_info']['cacheDate'] = time.time()
        else:
            dt = datetime.timedelta(seconds = time.time() - user_cache[user]['rank_info']['cacheDate'])
            if dt > datetime.timedelta(hours = 1):
                user_cache[user]['rank_info'] = {}
                user_cache[user]['rank_info']['data'] = []
                user_cache[user]['rank_info']['cacheDate'] = time.time()

    total_list = new_info_user_list + new_rank_user_list
    total_list = list(set(total_list)-set(non_user_list))
    if total_list:
        print('[cache refresh]:', end=' ')
        for user in total_list:
            print(user, end = ' ')
        print()
        with open(data_path('.\\cache\\user_cache.json'), 'w', encoding='utf-8') as f:
                json.dump(user_cache, f, indent='\t', ensure_ascii=False)
                
    if api_cnt > 0:
        time.sleep(1.2)
        
def async_get_user_cache(user_list):
    global loop
    global api_cnt
    api_cnt = 0
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()          # 이벤트 루프를 얻음
    loop.run_until_complete(__async_get_user(user_list))          # main이 끝날 때까지 기다림
    loop.close()                             # 이벤트 루프를 닫음
    del loop 
    print(f'use API {api_cnt} times', end=', ')
    return user_cache

async def __async_get_user_match(user_id):
    global loop
    global last_api_error
    global api_cnt
    api_cnt += 1
    url = 'https://kr.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/'+user_id+'?api_key='+API_KEY
    r = await loop.run_in_executor(None, requests.get, url)    # run_in_executor 사용
    if r.status_code != 200:
        if r.status_code == 404:
            # 게임 미진행중
            return False
        # 그외 error code
        last_api_error = r.status_code
        print('api error :', r.status_code, user_id)
        return False
    
    match = json.loads(r.text)
    return match

async def __async_get_match_list(user_id_list):
    global match_data_list
    user_id_list_chunked = list_chunk(user_id_list, 19)
    match_data_list = []
    start_time = time.time()
    match_data_list_chunked = []
    for num, lst in enumerate(user_id_list_chunked):
        futures = []
        for user_id in lst: 
            futures.append(asyncio.ensure_future(__async_get_user_match(user_id)))
        match_data_list_chunked.append(await asyncio.gather(*futures))                # 결과를 한꺼번에 가져옴
        # print(f"{len(user_id_list_chunked[num])}개 수행 end시간 {time.time()-start_time}[s]")
        if len(user_id_list_chunked) >= 2 and num != len(user_id_list_chunked)-1 :
            # print(f'{1.5}초쉬어갑니다.')
            time.sleep(1.5)
    for lst in match_data_list_chunked:
        match_data_list += lst
    # futures = [asyncio.ensure_future(__async_get_user_match(user_id)) for user_id in user_id_list] # 태스크(퓨처) 객체를 리스트로 만듦
    # match_data_list = await asyncio.gather(*futures)                # 결과를 한꺼번에 가져옴

def async_get_match_data(user_id_list):
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()          # 이벤트 루프를 얻음
    loop.run_until_complete(__async_get_match_list(user_id_list))          # main이 끝날 때까지 기다림
    loop.close()                             # 이벤트 루프를 닫음
    del loop 
    return match_data_list

def fast_get_match_list(user_cache, user_list):
    global api_cnt
    api_cnt = 0
    user_id_list = [user_cache[user_name]['user_info']['id'] for user_name in user_list]
    match_raw = async_get_match_data(user_id_list)
    total_match_data = {}
    for order, user_name in enumerate(user_list):
        total_match_data[user_name] = match_raw[order]
    print(f'use API {api_cnt} times', end=', ')
    return total_match_data


def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

if __name__ == '__main__':
    user_list = ['타잔'] 
    
    begin = time.time()
    user_cache = async_get_user_cache(user_list)
    data = fast_get_match_list(user_cache, user_list)
    end = time.time()
    with open('.\\test.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent='\t', ensure_ascii=False)
    print(f'소요시간 : {end-begin:.3f}[s]')
