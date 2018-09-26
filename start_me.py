from time import sleep
from tkinter import *
from tkinter.ttk import Combobox, Label

import vk

access_token = 0
api = 0
names = dict()
ncb = 0


def _():
    sleep(1)


def api_init():
    global api, access_token, names
    try:
        # DB!
        access_token = open("token").read()
        vk_session = vk.Session(access_token=access_token)
    except:
        build_auth_window()
        vk_session = vk.AuthSession(app_id='4771271', user_login=login, user_password=password, scope=4096)
        access_token = vk_session.access_token

    api = vk.API(vk_session, v='5.35', lang='ru', timeout=10)

    # DB!
    f = open("token", 'w')
    f.write(vk_session.access_token)
    f.close()

    try:
        # DB!
        names = eval(open('names.txt').read())
    except:
        names = dict()


def enter(event):
    global login, password
    login = e1.get()
    password = e2.get()
    root.destroy()


def build_auth_window():
    global root, e1, e2
    root = Tk()
    root.geometry("400x400")
    a = Label(root, text="Логин:")
    a.place(x=70, y=0)
    b = Label(root, text="Пароль:")
    b.place(x=63, y=20)
    e1 = Entry(root)
    e1.pack()
    e2 = Entry(root)
    e2.pack()
    b = Button(root, text="Войти")
    b.bind("<Button-1>", enter)
    b.pack()
    root.mainloop()


def name_by_id(num):
    global api, names
    try:
        if num not in names:
            a = api.users.get(user_ids=num)
            _()
            names[num] = a[0]['first_name'] + ' ' + a[0]['last_name']

        return names[num]
    except:
        print(num, "name error")


def to_put(a):
    return a['id'], name_by_id(a['user_id']), len(a['body'])


def grab_messages(count, offset, chat_id):
    global api
    a = api.messages.getHistory(count=count, offset=offset, chat_id=chat_id)
    _()
    a = a['items']
    ans = set()
    for i in a:
        ans.add(to_put(i))
    return ans


def grab_all_messages(ans, chat_id):
    i = 0
    l = [0]
    while len(l) != 0:
        print(i)
        l = grab_messages(200, i, chat_id)
        for elem in l:
            if elem in ans:
                ans |= l
                return
        i += 200
        ans |= l


def get_chats():
    global api
    try:
        # DB!
        f = open('chats')
        a, b = eval(f.readline()), eval(f.readline())
        f.close()

        return a, b
    except:

        chats = [0]
        bchats = dict()
        b = len(chats)
        temp = api.messages.getChat(chat_id=b)
        _()
        while True:
            chats.append(temp['title'])
            bchats[chats[-1]] = len(chats) - 1
            b += 1
            try:
                temp = api.messages.getChat(chat_id=b)
                _()
            except:
                break

        # DB!
        f = open('chats', 'w', encoding='utf-8')
        f.write(str(chats) + '\n' + str(bchats))
        f.close()

        return chats, bchats


def update(chat_id):
    try:
        # DB!
        our = eval(open(str(chat_id)).read())
    except:
        our = set()
    grab_all_messages(our, chat_id)

    # DB!
    f = open(str(chat_id), 'w', encoding='utf-8')
    f.write(str(our))
    f.close()

    return our


def vk_stop():
    # DB!
    global names
    f = open('names.txt', 'w')
    f.write(str(names))
    f.close()


def vk_full_update():
    for i in range(1, 100):
        update(i)


def show_standart(chat_id, mess):
    global api, cb
    res = Tk()
    res.geometry('400x800')
    our = dict()
    ans = []
    for e in mess:
        if e[1] not in our:
            our[e[1]] = len(ans)
            ans.append([0, 0, e[1]])
        ans[our[e[1]]][0] += 1
        ans[our[e[1]]][1] += e[2]
    temp = cb.get()
    if temp == "По количеству сообщений":
        f = lambda n: n[0]
    elif temp == "По количеству символов":
        f = lambda n: n[1]
    else:
        f = lambda n: round(n[1] / n[0], 3)
    ans.sort(reverse=True, key=f)
    s = ''
    for elem in ans:
        s += str(elem[2]) + ' ' + str(f(elem)) + '\n'
    t = Label(res, text=s)
    t.pack()

    b = Button(res, text='Послать в беседу')
    b.bind('<Button-1>', lambda n: api.messages.send(chat_id=chat_id, message=s))
    b.pack()

    res.mainloop()


def besedka(event):
    global ncb
    bes = bchats[ncb.get()]
    curr = update(bes)
    show_standart(bchats[ncb.get()], curr)


def show_main_window():
    global ncb, cb
    main = Tk()
    main.geometry('500x500')
    b5 = Button(main, text='Запуск')
    b5.bind('<Button-1>', besedka)
    b5.pack()
    cb = Combobox(main, values=['По количеству сообщений', 'По средней длине сообщения', 'По количеству символов'],
                  height=20, width=30)
    cb.set('По количеству сообщений')
    cb.pack()
    ncb = Combobox(main, values=chats[1:], height=20, width=30)
    ncb.set('Яичница')
    ncb.pack()
    main.mainloop()


api_init()
chats, bchats = get_chats()
show_main_window()
vk_stop()
