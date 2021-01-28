from tkinter import *
from tkinter import ttk
import time
 
class lol_tracer_Tk(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.label = Label(self, text="", font=("System", 20))
        self.label.pack()
        self.now_time = 0
    def update(self):
        now = time.strftime("%H:%M:%S")
        self.label.configure(text=now)
        self.after(1000, self.update)

win = lol_tracer_Tk()
win.title('롤 유저 자동 추적 프로그램')
win.geometry("410x505+1500+700")
win.resizable(False, False)

# 닉네임 입력 프레임
frame_users = LabelFrame(win, text = '소환사 닉네임 목록', padx = 5, pady = 5)
frame_users.place(x=10,y=10)
text_users = Text(frame_users, width = 25, height = 11, padx = 5, pady = 5)
users = "26세고졸무직공익\nAlphabetC\ntransname\n불버거\n웃대의님아\nzhongdanhuangdi\ncesemonacar\n김개미"
text_users.insert(END, users)
text_users.pack()

# 새로고침 프레임
frame_option = LabelFrame(win, text = '새로고침 주기', padx = 6, pady = 5)
frame_option.place(x=217, y=10)
li = list(map(int, '13579'))
combobox = ttk.Combobox(frame_option, height = 6, width = 20, values = li)
combobox.set("선택")
combobox.pack()

# 체크박스 프레임
frame_time = LabelFrame(win, padx = 2, pady = 1)
frame_time.place(x=217, y=67)
# label_time = Label(frame_time, text='12:20:06', width = 22)
# label_time.pack()

chk_button_alert = Checkbutton(frame_time, text = '새로운 유저 발견시 알림', padx = 6, pady= 2)
chk_button_alert.pack()

# 최근 갱신 시간
frame_time = LabelFrame(win, text = '최근 갱신 시각', padx = 7, pady = 1)
frame_time.place(x=217, y=103)
label_time = Label(frame_time, text='00:00:00', width = 22)
label_time.pack()

# 자동 추적 버튼
frame_button_auto = LabelFrame(win, padx = 4, pady = 5)
frame_button_auto.place(x=217, y=152)
button_auto = Button(frame_button_auto, text='자동 추적', font=("System", 18), width = 8)
button_auto.pack()

# 수동 갱신 버튼
frame_button_manual = LabelFrame(win, padx = 4, pady = 5)
frame_button_manual.place(x=309, y=152)
button_manual = Button(frame_button_manual, text='수동 갱신', font=("System", 18), width = 8)
button_manual.pack()

# 현재 게임중인 유저 창
frame_bottom = LabelFrame(win, padx = 5, pady = 5, text = '현재 게임중인 유저', width = 370, height = 280)#, bg = "white")
frame_bottom.place(x=10, y=200)

# 스크롤바 추가
mycanvas = Canvas(frame_bottom, bg = 'white', width = 350)
mycanvas.pack(side="left")
yscrollbar = ttk.Scrollbar(frame_bottom, orient="vertical", command=mycanvas.yview)
yscrollbar.pack(side='right', fill='y')
mycanvas.configure(yscrollcommand=yscrollbar.set)
mycanvas.bind('<Configure>',lambda e: mycanvas.configure(scrollregion = mycanvas.bbox('all')))
frame_playing_user = Frame(mycanvas, width = 350)
mycanvas.create_window((0, 0), window=frame_playing_user, anchor='nw')

import lol_api
from io import BytesIO
from PIL import Image, ImageTk
img_url = "http://ddragon.leagueoflegends.com/cdn/11.2.1/img/champion/Ahri.png" # 아리 이미지 
img_raw = lol_api.get_image(img_url).content
img = Image.open(BytesIO(img_raw))
img = img.resize((50, 50), Image.ANTIALIAS)
photo = PhotoImage(data=img_raw).zoom(2).subsample(5) # zoom과 subsample로 크기조절

for i in range(50):
    f = Frame(frame_playing_user, width = 350, height = 70)
    f.pack(side='top')
    l = Label(f, text='username - '+ str(i))
    l.place(x=10, y=30)
    l2 = Label(f, image=photo)
    l2.place(x=100, y=5)

win.mainloop()
