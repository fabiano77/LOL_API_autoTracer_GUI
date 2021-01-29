from tkinter import *
from tkinter import ttk
from io import BytesIO
from PIL import Image, ImageTk
import time
import lol_api

class lol_tracer_Tk(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.label = Label(self, text="", font=("System", 20))
        self.label.pack()
        self.now_time = 0
        # 창 생성
        self.title('롤 유저 자동 추적 프로그램 - by dhKim')
        self.geometry("410x505+1500+700")
        self.resizable(False, False)

        # 닉네임 입력 프레임
        frame_users = LabelFrame(self, text = '소환사 닉네임 목록', padx = 5, pady = 5)
        frame_users.place(x=10,y=10)
        self.text_users = Text(frame_users, width = 25, height = 11, padx = 5, pady = 5, font = ('NanumGothic', 10))
        self.users = "26세고졸무직공익\nAlphabetC\n엉덩국 갱승제로\ntransname"#\n불버거\n웃대의님아\n호량느\nzhongdanhuangdi\n김개미"
        self.text_users.insert(END, self.users)
        self.text_users.pack()

        # 기본 유저 리스트
        self.user_list = self.users.split('\n')

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
        self.frame_bottom = LabelFrame(self, padx = 5, pady = 5, text = '현재 게임중인 유저', width = 370, height = 280)#, bg = "white")
        self.frame_bottom.place(x=10, y=200)
        self.mycanvas = Canvas(self.frame_bottom, bg = 'white', width = 350)
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
        self.tier_memory = {}
        self.playing_user_cnt = 0
        self.tier_list = ['Bronze', 'Challenger', 'Diamond', 'Gold', 'Grandmaster', 'Iron', 'Master', 'Platinum', 'Silver']
        for tier in self.tier_list:
            with open('.\\image\\ranked-emblems\\Emblem_'+tier+'.png', 'rb') as img:
                self.tier_memory[tier] = img.read()

        # 지속적인 정보 갱신(시간 동기화)
        # self.update()
    

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


    def update(self):
        print('call: update,', end=' ')
        # 유저 창 프레임 초기화
        self.frame_user_init()
        self.playing_user_cnt
        # 최근 갱신 시간
        self.now_time = time.strftime("%H:%M:%S")
        self.label_time.configure(text=self.now_time)
        print(self.now_time)

        # 유저 정보 갱신
        for user_num, user_name in enumerate(self.user_list):
            self.show_user_info(user_num, user_name)

        # (?)ms후에 다시 갱신
        self.after(30000, self.update) # 30초


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
        print('call: show_user_info,', end = ' ')
        print(order, user_name)
        # riot API로부터 user정보 받아오기
        user_data = lol_api.get_user_json(user_name)
        # riot APi로부터 현재 진행중인 게임 정보 받아오기
        match_data = lol_api.get_current_match(user_name)
        if match_data == 404:
            print('게임 진행 중이 않습니다.')
            pass
        # 유저 랭크 티어 정보 (티어, 계급, 점수) ex. SILVER 4
        user_rank_tier_data = lol_api.get_user_solo_rank_info(user_data['id'])
        # 유저 티어 정보 (티어)
        user_tier = user_rank_tier_data.split()[0]
        if user_tier == '자유':
            user_tier = user_rank_tier_data.split()[1]
        user_tier = user_tier.lower().capitalize()

        # 유저 개인 Frame 생성
        frame_user = LabelFrame(self.frame_playing_user, width = 350, height = 70, padx = 5, pady = 3)
        frame_user.pack(side='top')
        # 유저 닉네임 출력
        label_name = Label(frame_user, text = user_name)
        label_name.place(x=2, y=5)
        # 유저 랭크 티어 정보 출력
        label_name = Label(frame_user, text = user_rank_tier_data)
        label_name.place(x=2, y=30)
        # 유저 매치 정보 출력
        if match_data == False:
            # 게임 중이 아님
            label_match = Label(frame_user, text = '현재 게임 중이 아닙니다.')
            label_match.place(x=180, y=20)
        else:
            self.playing_user_cnt += 1
            # 게임 중
            label_match = Label(frame_user, text = '현재 게임 중입니다.')
            label_match.place(x=180, y=30)
            # 게임 진행 시간
            match_timeLength = match_data['gameLength']
            match_timeLength += 300
            label_time_length = Label(frame_user, text = '진행 시간 {}분{}초'.format(match_timeLength//60, match_timeLength%60))
            label_time_length.place(x=180, y=5)
            # 유저 챔피언
            champ_name = ''
            for i in range(10):
                if match_data['participants'][i]['summonerName'] == user_name:
                    champ_key = match_data['participants'][i]['championId']
                    champ_name = lol_api.get_champ_name(champ_key)
            champ_img = lol_api.get_champ_image(champ_name)
            self.user_champ_photo_list.append(PhotoImage(data = champ_img).zoom(1).subsample(3)) # zoom과 subsample로 크기조절
            label_champ = Label(frame_user, image = self.user_champ_photo_list[self.playing_user_cnt-1])
            label_champ.place(x=295, y=8)



        # user정보를 이용하여 소환사 아이콘 img 다운
        # user_icon_img = self.load_icon_img(user_data['profileIconId'])
        # 유저 프로필 아이콘 출력
        # self.user_icon_photo_list.append(PhotoImage(data = user_icon_img).zoom(1).subsample(6)) # zoom과 subsample로 크기조절
        # label_icon = Label(frame_user, image = self.user_icon_photo_list[order])
        # label_icon.place(x=120, y=4)

        # 유저 티어 아이콘 출력
        self.user_tier_photo_list.append(PhotoImage(data = self.tier_memory[user_tier]).zoom(1).subsample(10)) # zoom과 subsample로 크기조절
        label_tier = Label(frame_user, image = self.user_tier_photo_list[order])
        label_tier.place(x=120, y=0)


        
        


if __name__ == '__main__':
    win=lol_tracer_Tk()
    win.mainloop()
