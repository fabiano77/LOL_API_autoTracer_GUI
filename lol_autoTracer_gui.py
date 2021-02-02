from tkinter import *
from tkinter import ttk
import tkinter.messagebox
from io import BytesIO
from PIL import Image, ImageTk
import json
import cv2
import numpy as np
import os
import sys
import time
import datetime
import lol_api
import webbrowser

'''
[This program] isn't endorsed by Riot Games and doesn't reflect the views or opinions of 
Riot Games or anyone officially involved in producing or managing Riot Games properties.
Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
''' 

def resize(src, ratio):
    src = np.asarray(bytearray(src), dtype='uint8')
    src = cv2.imdecode(src, cv2.IMREAD_COLOR)
    src = cv2.cvtColor(src, cv2.COLOR_BGR2RGB)
    src = add_edge(src, 10)
    src = cv2.resize(src, dsize=(0, 0), fx=ratio, fy=ratio,
                     interpolation=cv2.INTER_AREA)
    src = Image.fromarray(src)
    dst = ImageTk.PhotoImage(image=src)
    return dst

def add_edge(src, thickness):
    mean = cv2.mean(src)
    bordersize = thickness
    max_val = max(mean)
    # times = 200/max_val
    # new_mean = list(map(lambda x: x*times, mean))
    # # new_mean = list(map(lambda x: 255-x*times, mean))
    add_size = 200 - max_val
    new_mean = list(map(lambda x: x + add_size, mean))
    border = cv2.copyMakeBorder(
        src,
        top=bordersize,
        bottom=bordersize,
        left=bordersize,
        right=bordersize,
        borderType=cv2.BORDER_CONSTANT,
        value=[new_mean[0], new_mean[1], new_mean[2]]
        
    )
    return border

temp_api_key = ''
api_entry = None
api_win = None
def api_win_gen():
    global api_entry
    global api_win
    api_win = Tk()
    api_win.title("API KEY 입력창")
    api_win.geometry("420x130+1100+300") #나타나는 위치 + 뜨는 위치
    api_win.resizable(False, False)
    txt = ['1. 같이 열린 riot 개발자 포털 창의 우측 상단 [LOGIN] 버튼을 누르세요.', 
    '2. 자신의 롤 아이디로 로그인한 후 확인 버튼을 (3번 정도) 누르세요.',
    '3. 하단에 체크를 한 후 [REGENERATE] 버튼을 눌러 API KEY를 발급받으세요.',
    '4. 아래 창에 API KEY를 붙여넣기 후 입력 버튼을 누르세요']
    for i in range(4):
        label = Label(api_win, text = txt[i])
        label.place(x=5, y=5+23*i)

    api_entry = tkinter.Entry(api_win, width = 50)
    api_entry.place(x=10, y=100)
    # api_entry.insert(0, "발급받은 api key를 입력해주세요.")
    button = tkinter.Button(api_win, text="입력", command=save_api_key)
    button.place(x=370, y=95)
    api_win.mainloop()

def save_api_key():
    global api_entry
    global api_win
    api_key = api_entry.get()
    ret_code = lol_api.check_api(api_key)
    lol_api.last_api_error = 0
    if ret_code == 200:
        with open(lol_api.data_path('.\\api_key.dat'), 'w', encoding='utf-8') as f:
            f.write(api_key)
        lol_api.API_KEY = api_key
        tkinter.messagebox.showinfo('롤 유저 추적 프로그램', 'API KEY가 정상 인증 되었습니다.')
        api_win.destroy()
    else:
        txt = 'API KEY를 다시 입력해주세요'
        if ret_code == 403:
            txt += '\n만료되었거나 올바르지 않은 API KEY입니다. '
        tkinter.messagebox.showwarning('롤 유저 추적 프로그램', txt)

class lol_tracer_Tk(Tk):
    def __init__(self, add_size):
        Tk.__init__(self)
        self.add_size = add_size
        self.now_time = 0
        # 창 생성
        self.title('롤 유저 자동 추적 프로그램 - by dhKim')
        size = "410x505+1100+400"
        size = size[:4] + str(int(size[4:7])+add_size) + size[7:]
        self.geometry(size)
        self.resizable(False, True)

        # 레이아웃을 위한 더미 프레임
        frame_dummy = Frame(self)
        frame_dummy.grid(row=0,column=0, sticky=W+E)
        for i in range(9):
            dummy = Label(frame_dummy)
            dummy.grid(row=i,column=0)
        # 닉네임 입력 프레임
        frame_users = LabelFrame(self, text='유저 닉네임 목록', padx=5, pady=5)
        frame_users.place(x=10, y=10)
        self.text_users = Text(
            frame_users, width=25, height=11, padx=5, pady=5, font=('NanumGothic', 10))
        if os.path.isfile(lol_api.data_path('.\\cache\\default_list.dat')):
            with open(lol_api.data_path('.\\cache\\default_list.dat'), 'r', encoding='utf-8') as f:
                self.user_list = f.read()
        else:
            self.user_list = '유저 닉네임을 줄단위로 입력하세요'
        self.users = self.user_list
        self.text_users.insert(END, self.users)
        self.text_users.pack()

        self.frame_top = Frame(self)
        self.frame_top.grid(row=0, column=0)

        # 새로고침 프레임
        frame_option = LabelFrame(self, text='새로고침 주기', padx=6, pady=5)
        frame_option.place(x=217, y=10)
        li = list(map(lambda x: x+'분', '12345'))
        self.combobox = ttk.Combobox(
            frame_option, height=6, width=20, values=li, state="readonly")
        self.combobox.current(0)
        self.combobox.pack()

        # 체크박스 프레임
        frame_chkbox = LabelFrame(self, padx=2, pady=1)
        frame_chkbox.place(x=217, y=67)
        self.chk_var = IntVar()
        chk_button_alert = Checkbutton(
            frame_chkbox, text='새로운 유저 발견시 알림', padx=6, pady=2, variable=self.chk_var)
        chk_button_alert.select()
        chk_button_alert.pack()

        # 갱신후 경과 시간
        self.frame_time = LabelFrame(self, text='갱신후 경과 시간', padx=7, pady=1)
        self.frame_time.place(x=217, y=106)
        self.update_time = 0
        self.label_time = Label(self.frame_time, text='00:00:00', width=22)
        self.label_time.pack()

        # 자동 갱신 버튼
        frame_button_auto = LabelFrame(self, padx=4, pady=5)
        frame_button_auto.place(x=217, y=157)
        self.button_auto = Button(frame_button_auto, text='갱신 시작', font=(
            'NanumGothic', 10), width=8, command=self.button_click_2)
        self.button_auto.pack()
        self.auto = False

        # API 발급 버튼
        frame_button_manual = LabelFrame(self, padx=4, pady=5)
        frame_button_manual.place(x=309, y=157)
        button_manual = Button(frame_button_manual, text='API 발급', font=(
            'NanumGothic', 10), width=8, command=self.button_click_1)
        button_manual.pack()

        # 현재 게임중인 유저 프레임
        # pack 배치 코드
        # self.frame_bottom = LabelFrame(self, padx=5, pady=5, text='추적 유저 목록', width=370, height=280)
        # self.frame_bottom.place(x=10, y=200)
        # self.mycanvas = Canvas(self.frame_bottom, width=350, height=260 + self.add_size)
        # self.mycanvas.pack(side="left", fill='y')
        # self.yscrollbar = ttk.Scrollbar(self.frame_bottom, orient="vertical")
        # self.yscrollbar.configure(command=self.mycanvas.yview)
        # self.yscrollbar.pack(side='right', fill='y')

        # grid 배치 코드
        self.frame_bottom = LabelFrame(self, padx=5, pady=5, text='추적 유저 목록')
        self.frame_bottom.grid(row=1, column=0, padx=10, pady=10, sticky=E+W+N+S)
        self.mycanvas = Canvas(self.frame_bottom)
        self.mycanvas.grid(row = 0, column=0, sticky= E+W+N+S)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.yscrollbar = ttk.Scrollbar(self.frame_bottom, orient="vertical")
        self.yscrollbar.configure(command=self.mycanvas.yview)
        self.yscrollbar.grid(row=0, column=1, sticky='ns')
        # 창 크기 조절 연동
        self.frame_bottom.rowconfigure(0, weight=1)
        self.frame_bottom.columnconfigure(0, weight=1)

        # 스크롤바 연동
        self.mycanvas.configure(yscrollcommand=self.yscrollbar.set)
        self.mycanvas.bind('<Configure>', lambda e: self.mycanvas.configure(
            scrollregion=self.mycanvas.bbox('all')))

        # 현재 게임중인 유저 창
        self.frame_playing_user = Frame(self.mycanvas)#, width=350)
        self.mycanvas.create_window(
            (0, 0), window=self.frame_playing_user, anchor='nw')
        self.user_icon_photo_list = []
        self.user_tier_photo_list = []

        # # 현재 게임중인 유저 창 초기화
        # self.frame_bottom_init()

        # memory 확보
        self.message_title = ''
        self.message_text = ''
        self.user_match_dict = {}
        self.icon_memory = {}
        self.tier_memory_M = {}
        self.tier_memory_S = {}
        self.tier_list = ['Bronze', 'Challenger', 'Diamond', 'Gold',
                          'Grandmaster', 'Iron', 'Master', 'Platinum', 'Silver', 'Unranked']
        for tier in self.tier_list:
            with open(lol_api.resource_path('.\\image\\medium-emblems\\Emblem_'+tier+'.png'), 'rb') as img:
                self.tier_memory_M[tier] = img.read()
        for tier in self.tier_list:
            with open(lol_api.resource_path('.\\image\\small-emblems\\Emblem_'+tier+'.png'), 'rb') as img:
                self.tier_memory_S[tier] = img.read()

        self.refresh_label_list = []

        # api 확인
        ret_code = lol_api.check_api()
        if ret_code != 200:
            print(f'API키 error {ret_code}')
            # m_title = 'API키 갱신 필요'
            # m_text = f'api error code : {ret_code}\nAPI 발급 버튼을 눌러 입력해주세요'
            # self.after(1, self.warning_message, m_title, m_text)

        self.time_refresh()

        

    def button_click_1(self):
        # # 버튼 클릭 이벤트
        # self.update()
        # api 확인
        ret_code = lol_api.check_api()
        lol_api.last_api_error = 0
        if ret_code == 200:
            m_title = '롤 유저 추적 프로그램'
            m_text = f'API KEY 발급이 필요 없는 상태입니다'
            self.after(1, self.info_message, m_title, m_text)
        else:
            webbrowser.open("https://developer.riotgames.com/")
            self.after(0, api_win_gen)

    def button_click_2(self):
        # 좌측 버튼
        if self.auto:
            self.auto = False
            self.button_auto.configure(text='갱신 시작')
        else:
            if self.update_time == 0:
                self.update()
            self.auto = True
            self.button_auto.configure(text='갱신 끄기')

        # self.time_min = int(self.combobox.get()[0])
        # self.auto_update()

        # 테스트 기능
        # self.show_user_info('knightzz')

    def clear_win(self):
        self.frame_playing_user.destroy()
        self.mycanvas.destroy()
        self.yscrollbar.destroy()
        self.frame_bottom.destroy()

        # place 배치 코드
        # self.frame_bottom = LabelFrame(self, padx=5, pady=5, text=f'추적 유저 목록', width=370, height=280)
        # self.frame_bottom.place(x=10, y=200)
        # self.mycanvas = Canvas(self.frame_bottom, width=350, height=260 + self.add_size)
        # self.mycanvas.pack(side="left")
        # self.yscrollbar = ttk.Scrollbar(self.frame_bottom, orient="vertical")
        # self.yscrollbar.configure(command=self.mycanvas.yview)
        # self.yscrollbar.pack(side='right', fill='y')

        # grid 배치 코드
        self.frame_bottom = LabelFrame(self, padx=5, pady=5, text='추적 유저 목록')
        self.frame_bottom.grid(row=1, column=0, padx=10, pady=10, sticky=E+W+N+S)
        self.mycanvas = Canvas(self.frame_bottom)
        self.mycanvas.grid(row = 0, column=0, sticky= E+W+N+S)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.yscrollbar = ttk.Scrollbar(self.frame_bottom, orient="vertical")
        self.yscrollbar.configure(command=self.mycanvas.yview)
        self.yscrollbar.grid(row=0, column=1, sticky='ns')
        # 창 크기 조절 연동
        self.frame_bottom.rowconfigure(0, weight=1)
        self.frame_bottom.columnconfigure(0, weight=1)

        self.mycanvas.configure(yscrollcommand=self.yscrollbar.set)
        self.mycanvas.bind('<Configure>', lambda e: self.mycanvas.configure(
            scrollregion=self.mycanvas.bbox('all')))

        self.frame_playing_user = Frame(self.mycanvas, width=350)
        self.mycanvas.create_window(
            (0, 0), window=self.frame_playing_user, anchor='nw')

    def frame_bottom_init(self):
        # 유저 프레임 초기화
        self.clear_win()
        self.user_icon_photo_dict = dict()
        self.user_tier_photo_dict = dict()
        self.user_champ_photo_dict = dict()
        self.refresh_label_list = list()

    def time_refresh(self):
        # 1초마다 시간을 갱신.
        self.after(1000, self.time_refresh)
        # 시간 종속적인 객체 갱신
        self.now_time = time.time()
        over_time = 0
        for item in self.refresh_label_list:
            if item['startTime'] == 9999999999.999:
                time_str =  '00분00초'
            else:
                time_str = time.strftime('%M분%S초', time.localtime(
                    self.now_time - item['startTime']))
            item['label'].configure(text=time_str)
        # 최근 갱신 시간
        if self.update_time == 0:
            time_str = ''
        else:
            over_time = self.now_time - self.update_time
            time_str = time.strftime("%M분 %S초", time.localtime(over_time))
        self.label_time.configure(text=time_str)
        # api 에러 체크 후 메시지 출력
        self.check_api_error()
        # auto update 로직 변경
        self.time_min = int(self.combobox.get()[0])
        if self.auto and datetime.timedelta(seconds=over_time) >= datetime.timedelta(minutes=self.time_min):
            # print('time_refresh: call update')
            self.update()

    def check_api_error(self):
        api_error = lol_api.last_api_error
        if api_error == 0:
            return
        # 에러 코드 초기화
        lol_api.last_api_error = 0
        print(f'check_api_error: {api_error}')
        m_title = 'API 요청 에러'
        m_text = f'error code : {api_error}\n'
        if api_error == 400:
            m_text += '잘못된 요청입니다.'
        elif api_error == 401:
            m_text += 'API KEY키가 없습니다. API 발급 버튼을 누르세요.'
        elif api_error == 403:
            m_text += '만료된 API KEY입니다. API KEY를 재발급 받으세요.\n'
            m_text += '개인용 API KEY는 24시간마다 재발급 받아야 합니다.'
        elif api_error == 404:
            m_text += '존재하지 않는 유저입니다.'
            for user in lol_api.non_user_list:
                m_text += f'\n  {user}'
        elif api_error == 405:
            m_text += 'None'
        elif api_error == 429:
            m_text += '요청 횟수를 초과하였습니다. 1분 후 시도하세요.'
        self.after(10, self.warning_message, m_title, m_text)
        
    # def auto_update(self):
    #     print(f'call: auto_update, period : {self.time_min}[min]')
    #     self.update()
    #     # (?)ms후에 다시 갱신
    #     self.after(self.time_min * 60 * 1000, self.auto_update)

    def warning_message(self, title, text):
        tkinter.messagebox.showwarning(title, text)
    
    def info_message(self, title, text):
        tkinter.messagebox.showinfo(title, text)

    def update(self):
        self.update_time = time.time()
        # 유저 리스트 입력받음
        self.user_list = self.text_users.get("1.0", END).rstrip()
        with open(lol_api.data_path('.\\cache\\default_list.dat'), 'w', encoding='utf-8') as f:
            f.write(self.user_list)
        self.user_list = self.user_list.rstrip().split('\n')
        self.user_list = [user_name.replace(
            " ", "").lower() for user_name in self.user_list]
        if len(self.user_list) > 50:
            m_title = 'error'
            m_text = '유저 수를 초과하였습니다 (50 이상)'
            self.after(10, self.warning_message, m_title, m_text)
        # 유저 창 프레임 초기화
        self.frame_bottom_init()
        print('update: '+time.strftime('%H:%M:%S', time.localtime(self.update_time)), end=', ')

        # 유저 정보 갱신
        self.user_memory = dict()
        self.user_cache = lol_api.async_get_user_cache(self.user_list)
        for user_name in self.user_list:
            if user_name not in self.user_cache:
                self.user_list.remove(user_name)
        self.last_user_match_dict = self.user_match_dict
        self.user_match_dict = lol_api.fast_get_match_list(self.user_cache, self.user_list)
        self.search_user(self.user_list)
        if self.chk_var.get() == 1:
            self.after(10, self.check_new_gamer)
        print(f'정보 갱신 시간 {time.time() - self.update_time:.2f}[s]', end=', ')

        playing_users = []
        # 게임 중인 유저 표시
        for user_name in self.user_list:
            if self.user_memory[user_name]['game_state'] == True:
                if self.user_memory[user_name]['match_data']['gameStartTime'] == 0:
                    self.user_memory[user_name]['match_data']['gameStartTime'] = 9999999999999
                playing_users.append(self.user_memory[user_name])
                # self.show_user_info(user_name)
        playing_users.sort(key=lambda x: x['match_data']['gameStartTime'])
        for user_item in playing_users:
            # self.show_user_info(user_name))
            self.show_user_info(user_item['user_data']['name'].replace(" ", "").lower())
        # 게임 안하는 유저 표시
        for user_name in self.user_list:
            if self.user_memory[user_name]['game_state'] == False:
                self.show_user_info(user_name)
        self.frame_bottom.configure(text = f'추적 유저 목록 ({len(playing_users)}/{len(self.user_list)})')
        print(f'총 소요시간 {time.time() - self.update_time:.2f}[s]')

    def check_new_gamer(self):
        for user in self.user_list:
            if user in self.user_match_dict and user in self.last_user_match_dict:
                # 두 번의 데이터가 있고
                if self.user_match_dict[user] != False and self.last_user_match_dict[user] == False:
                    # 게임 중이 아니였던 유저가 게임에 중일 경우 이벤트 발생.
                    name = self.user_cache[user]['user_info']['name']
                    print(f'\t\tcheck_new_gamer: 새로 게임하는 {name} 발견')
                    m_title = '롤 유저 자동 추적 프로그램'
                    m_text = f'새로 게임하는 {name} 발견'
                    self.after(0, self.info_message, m_title, m_text)
                elif self.user_match_dict[user] == False and self.last_user_match_dict[user] != False:
                    # 게임 중이던 유저가 끝난 경우
                    name = self.user_cache[user]['user_info']['name']
                    print(f'\t\tcheck_new_gamer: {name} 의 게임이 끝남.')

    def search_user(self, user_list):
        for user_name in user_list:
            self.user_memory[user_name] = {}
            # riot API로부터 user정보 받아오기
            self.user_memory[user_name]['user_data'] = self.user_cache[user_name]['user_info']
            # 유저 랭크 티어 정보 (티어, 계급, 점수) ex. SILVER 4
            if 'rank_info' in self.user_cache[user_name]:
                self.user_memory[user_name]['rank_data'] = self.user_cache[user_name]['rank_info']['data']
            else:
                self.user_memory[user_name]['rank_data'] = []
            # riot APi로부터 현재 진행중인 게임 정보 받아오기
            self.user_memory[user_name]['match_data'] = self.user_match_dict[user_name]
            # 유저 티어 정보 (티어)
            if self.user_memory[user_name]['match_data'] == False:
                self.user_memory[user_name]['game_state'] = False
            else:
                self.user_memory[user_name]['game_state'] = True

    def load_icon_img(self, icon_key):
        icon_img = bytes()
        if icon_key not in self.icon_memory:
            print('icon: 이미지를 새로 불러옵니다.')
            icon_img = lol_api.get_profileIcon(icon_key)
            self.icon_memory[icon_key] = icon_img
        else:
            print('icon: 캐싱된 이미지를 사용합니다.')
            icon_img = self.icon_memory[icon_key]
        return icon_img

    def show_user_info(self, user_name):
        # 정보 불러오기
        user_data = self.user_memory[user_name]['user_data']
        rank_data = self.user_memory[user_name]['rank_data']
        match_data = self.user_memory[user_name]['match_data']
        # 유저 티어 정보 (티어)
        user_rank_tier_data = lol_api.get_user_solo_rank_info(rank_data)
        user_tier = user_rank_tier_data.split()[0]
        if user_tier == '자유':
            user_tier = user_rank_tier_data.split()[1]
        user_tier = user_tier.lower().capitalize()

        # 게임(on/off) 에 따른 정보 출력
        if match_data == False:
            # bground = 'SystemButtonFace' # 기본 배경색
            bground = 'light cyan'

            # 유저 게임 비 진행중
            # 유저 개인 Frame 생성
            frame_user = LabelFrame(
                self.frame_playing_user, width=350, height=35, padx=5, pady=3, bg=bground)
            frame_user.pack(side='top')
            # 유저 닉네임 출력
            label_name = Label(frame_user, text=user_data['name'], bg=bground)
            label_name.place(x=2, y=0)
            # 유저 랭크 티어 정보 출력
            label_name = Label(
                frame_user, text=user_rank_tier_data, bg=bground)
            label_name.place(x=150, y=0)
            # 유저 승패 정보 출력
            label_wins = Label(frame_user, text=lol_api.get_win_cnt(
                rank_data), font=("D2Coding", 9), bg=bground)
            label_wins.place(x=253, y=0)
            # 유저 티어 아이콘 출력
            self.user_tier_photo_dict[user_name] = PhotoImage(
                data=self.tier_memory_S[user_tier])
            label_tier = Label(
                frame_user, image=self.user_tier_photo_dict[user_name], bg=bground)
            label_tier.place(x=120, y=-2)
        else:
            bground = 'lavender'
            # 유저 게임 중 상태
            # 유저 개인 Frame 생성
            frame_user = LabelFrame(self.frame_playing_user, width=350, height=70, padx=5, pady=3, bg=bground)
            frame_user.pack(side='top')
            # 유저 닉네임 출력
            label_name = Label(frame_user, text=user_data['name'], bg=bground)
            label_name.place(x=2, y=5)
            # 유저 랭크 티어 정보 출력
            label_name = Label(frame_user, text=user_rank_tier_data, bg=bground)
            label_name.place(x=2, y=30)
            # 게임 중, 게임유형정보
            label_match = Label(frame_user, text=lol_api.get_queue_type(match_data), bg=bground)
            label_match.place(x=185, y=5)
            # 게임 진행 시간
            match_start_time = match_data['gameStartTime']/1000
            # time_str = time.strftime('%M분%S초', time.localtime(self.now_time - match_start_time))
            label_time_length = Label(frame_user, bg=bground)
            label_time_length.place(x=185, y=30)
            item = dict()
            item['label'] = label_time_length
            item['startTime'] = match_start_time
            self.refresh_label_list.append(item)
            # 유저 챔피언
            champ_name = ''
            for i in range(len(match_data['participants'])):
                if match_data['participants'][i]['summonerName'].replace(" ", "").lower() == user_name.replace(" ", "").lower():
                    champ_key = match_data['participants'][i]['championId']
                    champ_name = lol_api.get_champ_name(champ_key)
            champ_img = lol_api.get_champ_image(champ_name)
            img = resize(champ_img, 0.33)
            self.user_champ_photo_dict[user_name] = img
            label_champ = Label(
                frame_user, image=self.user_champ_photo_dict[user_name], bg=bground)
            label_champ.place(x=275, y=5)
            # 유저 티어 아이콘 출력
            self.user_tier_photo_dict[user_name] = PhotoImage(
                data=self.tier_memory_M[user_tier])
            label_tier = Label(
                frame_user, image=self.user_tier_photo_dict[user_name], bg=bground)
            label_tier.place(x=120, y=0)


if __name__ == '__main__':
    if not os.path.exists(lol_api.data_path('')):
        os.makedirs(lol_api.data_path(''))
    if not os.path.exists(lol_api.data_path('cache\\')):
        os.makedirs(lol_api.data_path('cache\\'))
    additional_size = 150
    win = lol_tracer_Tk(additional_size)
    win.mainloop()
