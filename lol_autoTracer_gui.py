from tkinter import *
from tkinter import ttk
from io import BytesIO
from PIL import Image, ImageTk
import time
import datetime
import lol_api

class lol_tracer_Tk(Tk):
    def __init__(self, add_size):
        Tk.__init__(self)
        self.add_size = add_size
        self.label = Label(self, text="", font=("System", 20))
        self.label.pack()
        self.now_time = 0
        # 창 생성
        self.title('롤 유저 자동 추적 프로그램 - by dhKim')
        size = "410x505+1500+700"
        size = size[:4] + str(int(size[4:7])+add_size) + size[7:]
        self.geometry(size)
        self.resizable(False, False)

        # 닉네임 입력 프레임
        frame_users = LabelFrame(self, text = '소환사 닉네임 목록', padx = 5, pady = 5)
        frame_users.place(x=10,y=10)
        self.text_users = Text(frame_users, width = 25, height = 11, padx = 5, pady = 5, font = ('NanumGothic', 10))
        self.users = "T1 Canna\n26세고졸무직공익\nAlphabetC\ntransname\n불버거\n웃대의님아\n호량느\nzhongdanhuangdi\n김개미"
        self.text_users.insert(END, self.users)
        self.text_users.pack()

        # 새로고침 프레임
        frame_option = LabelFrame(self, text = '새로고침 주기', padx = 6, pady = 5)
        frame_option.place(x=217, y=10)
        li = list(map(int, '13579'))
        combobox = ttk.Combobox(frame_option, height = 6, width = 20, values = li)
        combobox.set("선택")
        combobox.pack()

        # 체크박스 프레임
        frame_chkbox = LabelFrame(self, padx = 2, pady = 1)
        frame_chkbox.place(x=217, y=67)
        chk_button_alert = Checkbutton(frame_chkbox, text = '새로운 유저 발견시 알림', padx = 6, pady= 2)
        chk_button_alert.pack()

        # 최근 갱신 시간
        self.frame_time = LabelFrame(self, text = '최근 갱신 시각', padx = 7, pady = 1)
        self.frame_time.place(x=217, y=103)
        self.label_time = Label(self.frame_time, text='00:00:00', width = 22)
        self.label_time.pack()

        # 자동 추적 버튼
        frame_button_auto = LabelFrame(self, padx = 4, pady = 5)
        frame_button_auto.place(x=217, y=152)
        button_auto = Button(frame_button_auto, text='자동 추적', font=("System", 18), width = 8)
        button_auto.pack()

        # 수동 갱신 버튼
        frame_button_manual = LabelFrame(self, padx = 4, pady = 5)
        frame_button_manual.place(x=309, y=152)
        button_manual = Button(frame_button_manual, text='수동 갱신', font=("System", 18), width = 8, command = self.button_click_1)
        button_manual.pack()

        # 현재 게임중인 유저 프레임
        self.frame_bottom = LabelFrame(self, padx = 5, pady = 5, text = '추적 유저 목록', width = 370, height = 280)#, bg = "white")
        self.frame_bottom.place(x=10, y=200)
        self.mycanvas = Canvas(self.frame_bottom, bg = 'white', width = 350, height = 260+add_size)
        self.mycanvas.pack(side="left")

        # 스크롤바 추가
        self.yscrollbar = ttk.Scrollbar(self.frame_bottom, orient="vertical", command=self.mycanvas.yview)
        self.yscrollbar.pack(side='right', fill='y')

        # 스크롤바 연동
        self.mycanvas.configure(yscrollcommand=self.yscrollbar.set)
        self.mycanvas.bind('<Configure>',lambda e: self.mycanvas.configure(scrollregion = self.mycanvas.bbox('all')))

        # 현재 게임중인 유저 창
        self.frame_playing_user = Frame(self.mycanvas, width = 350)
        self.mycanvas.create_window((0, 0), window=self.frame_playing_user, anchor='nw')
        self.user_icon_photo_list = []
        self.user_tier_photo_list = []


        # 현재 게임중인 유저 창 초기화
        self.frame_user_init()

        # memory 확보
        self.icon_memory = {}
        self.tier_memory_M = {}
        self.tier_memory_S = {}
        self.playing_user_cnt = 0
        self.tier_list = ['Bronze', 'Challenger', 'Diamond', 'Gold', 'Grandmaster', 'Iron', 'Master', 'Platinum', 'Silver', 'Unranked']
        for tier in self.tier_list:
            with open('.\\image\\medium-emblems\\Emblem_'+tier+'.png', 'rb') as img:
                self.tier_memory_M[tier] = img.read()
        for tier in self.tier_list:
            with open('.\\image\\small-emblems\\Emblem_'+tier+'.png', 'rb') as img:
                self.tier_memory_S[tier] = img.read()

        self.update()
    

    def button_click_1(self):
        # 버튼 클릭 이벤트
        self.update()


    def frame_user_init(self):
        # 유저 프레임 초기화
        self.frame_playing_user = Frame(self.mycanvas, width = 350)
        self.mycanvas.create_window((0, 0), window=self.frame_playing_user, anchor='nw')
        self.user_icon_photo_list = []
        self.user_tier_photo_list = []
        self.user_champ_photo_list = []


    def auto_update(self):
        print('call: auto_update,', end=' ')
        # (?)ms후에 다시 갱신
        self.after(30000, self.update) # 30초

    def update(self):
        start_time = time.time()
        print('call: update,', end=' ')
        # 유저 창 프레임 초기화
        self.frame_user_init()
        self.playing_user_cnt = 0
        # 최근 갱신 시간
        self.now_time = time.time()
        time_str = time.strftime("%H:%M:%S", time.localtime(self.now_time))
        self.label_time.configure(text=time_str)
        print(time_str)

        # api 확인
        if lol_api.check_api() != 200:
            print("API키를 체크해주세요")
            return

        # 유저 리스트 입력받음
        self.user_list = self.text_users.get("1.0", END).rstrip().split('\n')

        # 유저 정보 갱신
        for user_num, user_name in enumerate(self.user_list):
            self.show_user_info(user_num, user_name)
        print(f'소요시간 {time.time()-start_time:.2f}[s]')

        


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


    def show_user_info(self, order, user_name):
        start_time = time.time()
        print('call: show_user_info,', end = ' ')
        print(order, user_name)
        # riot API로부터 user정보 받아오기
        user_data = lol_api.get_user_json(user_name)
        # riot APi로부터 현재 진행중인 게임 정보 받아오기
        match_data = lol_api.get_current_match(user_data['id'])
        # 유저 랭크 티어 정보 (티어, 계급, 점수) ex. SILVER 4
        user_rank_tier_data = lol_api.get_user_solo_rank_info(user_name)
        # 유저 티어 정보 (티어)
        user_tier = user_rank_tier_data.split()[0]
        if user_tier == '자유':
            user_tier = user_rank_tier_data.split()[1]
        user_tier = user_tier.lower().capitalize()
        
        # 게임(on/off) 에 따른 정보 출력
        if match_data == False:
            # 유저 게임 비 진행중
            # 유저 개인 Frame 생성
            frame_user = LabelFrame(self.frame_playing_user, width = 350, height = 35, padx = 5, pady = 3)
            frame_user.pack(side='top')
            # 유저 닉네임 출력
            label_name = Label(frame_user, text = user_data['name'])
            label_name.place(x=2, y=0)
            # 유저 랭크 티어 정보 출력
            label_name = Label(frame_user, text = user_rank_tier_data)
            label_name.place(x=150, y=0)
            # 유저 승패 정보 출력
            label_wins = Label(frame_user, text = lol_api.get_win_cnt(user_name), font = ("D2Coding",9))
            label_wins.place(x=253, y=0)
            # 유저 티어 아이콘 출력
            self.user_tier_photo_list.append(PhotoImage(data = self.tier_memory_S[user_tier])) # zoom과 subsample로 크기조절
            label_tier = Label(frame_user, image = self.user_tier_photo_list[order])
            label_tier.place(x=120, y=-2)
        else:
            # 유저 게임 중 상태
            self.playing_user_cnt += 1
            # 유저 개인 Frame 생성
            frame_user = LabelFrame(self.frame_playing_user, width = 350, height = 70, padx = 5, pady = 3)
            frame_user.pack(side='top')
            # 유저 닉네임 출력
            label_name = Label(frame_user, text = user_data['name'])
            label_name.place(x=2, y=5)
            # 유저 랭크 티어 정보 출력
            label_name = Label(frame_user, text = user_rank_tier_data)
            label_name.place(x=2, y=30)
            # 게임 중, 게임유형정보
            label_match = Label(frame_user, text = lol_api.get_queue_type(match_data))
            label_match.place(x=180, y=30)
            # 게임 진행 시간
            match_start_time = match_data['gameStartTime']/1000
            time_str = time.strftime('%M분%S초', time.localtime(self.now_time - match_start_time))
            label_time_length = Label(frame_user, text = time_str)
            label_time_length.place(x=180, y=5)
            # 유저 챔피언
            champ_name = ''
            for i in range(10):
                if match_data['participants'][i]['summonerName'].replace(" ", "") == user_name.replace(" ", ""):
                    champ_key = match_data['participants'][i]['championId']
                    champ_name = lol_api.get_champ_name(champ_key)
            champ_img = lol_api.get_champ_image(champ_name)
            self.user_champ_photo_list.append(PhotoImage(data = champ_img).zoom(1).subsample(3)) # zoom과 subsample로 크기조절
            label_champ = Label(frame_user, image = self.user_champ_photo_list[self.playing_user_cnt-1])
            label_champ.place(x=280, y=8)
            # 유저 티어 아이콘 출력
            self.user_tier_photo_list.append(PhotoImage(data = self.tier_memory_M[user_tier])) # zoom과 subsample로 크기조절
            label_tier = Label(frame_user, image = self.user_tier_photo_list[order])
            label_tier.place(x=120, y=0)

        print(f'소요시간 {time.time()-start_time:.2f}[s]')

        # user정보를 이용하여 소환사 아이콘 img 다운
        # user_icon_img = self.load_icon_img(user_data['profileIconId'])
        # 유저 프로필 아이콘 출력
        # self.user_icon_photo_list.append(PhotoImage(data = user_icon_img).zoom(1).subsample(6)) # zoom과 subsample로 크기조절
        # label_icon = Label(frame_user, image = self.user_icon_photo_list[order])
        # label_icon.place(x=120, y=4)

        


        
        


if __name__ == '__main__':
    additional_size = 100
    win=lol_tracer_Tk(additional_size)
    win.mainloop()
