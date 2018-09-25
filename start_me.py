import vk
from tkinter import *
from tkinter.ttk import Combobox, Label

access_token = 0
api = 0


def save_values(f):
    s_a_v_e_d__f_o_r__l_a_t_e_r = dict()

    def g(*args):
        if list(*args) not in s_a_v_e_d__f_o_r__l_a_t_e_r:
            s_a_v_e_d__f_o_r__l_a_t_e_r[list(*args)] = f(*args)
        return s_a_v_e_d__f_o_r__l_a_t_e_r[list(*args)]

    return g


def api_init():
    global api
    global access_token
    try:
        access_token = open("token").read()
        vk_session = vk.Session(access_token=access_token)
        api = vk.API(vk_session, v='5.35', lang='ru', timeout=10)
    except:
        build_auth_window()
        vk_session = vk.AuthSession(app_id='4771271', user_login=login, user_password=password, scope=4096)
        api = vk.API(vk_session, v='5.35', lang='ru', timeout=10)
        access_token = vk_session.access_token
        f = open("token", 'w')
        f.write(vk_session.access_token)
        f.close()


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


@save_values
def name_by_id(num):
    global api
    try:
        if num in names:
            return names[num]
        # a = do_vk_request({'user_ids': str(num)}, 'users.get', need_token=True)
        a = api.users.get(user_ids=num)
        # time.sleep(0.3)
        print(a)
        # now what?
        names[num] = a[0]['response'][0]['first_name'] + ' ' + a[0]['response'][0]['last_name']
        return a[0]['response'][0]['first_name'] + ' ' + a[0]['response'][0]['last_name']
    except:
        print(num, "name error")


def to_put(a):
    return a.m_id, a.user_name, len(a.body)


def grab_messages(count, offset, chat_id):
    # a = do_vk_request({'count': count, 'offset': offset, 'chat_id': chat_id}, 'messages.getHistory')
    global api
    a = api.messages.getHistory(count=count, offset=offset, chat_id=chat_id)
    try:
        a = a[0]['response']['items']
    except:
        print(a)
    ans = set()
    for i in a:
        ans.add(to_put(i))
    # time.sleep(0.9)
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
                return 0
        i += 200
        ans |= l
    print('\n\nsent\n\n')


def get_chats(recalc=True):
    global api
    if recalc:
        try:
            f = open('chats')
            chats, bchats = eval(f.readline()), eval(f.readline())
            b = len(chats)
            f.close()
            b = len(chats)
        except:
            chats = [0]
            bchats = dict()
            b = 1
        # temp = do_vk_request({'chat_id': b}, 'messages.getChat')[0]
        temp = api.messages.getChat(chat_id=b)
        print(temp)
        # now what?
        while temp['admin_id'] != 0:
            chats.append(temp['title'])
            bchats[chats[-1]] = len(chats) - 1
            b += 1
            # temp = do_vk_request({'chat_id': b}, 'messages.getChat')[0]
            temp = api.messages.getChat(chat_id=b)
            print(temp)
            # now what?
            # time.sleep(0.3)
        f = open('chats', 'w')
        f.write(str(chats) + '\n' + str(bchats))
        f.close()
        return chats, bchats
    else:
        try:
            f = open('chats')
            a, b = eval(f.readline()), eval(f.readline())
            f.close()
            return a, b
        except:
            return get_chats(recalc=True)


def update(chat_id):
    try:
        our = eval(open(str(chat_id)).read())
    except:
        our = set()
    grab_all_messages(our, chat_id)
    f = open(str(chat_id), 'w')
    f.write(str(our))
    f.close()
    return our


def get_friends(user_id=233692275):
    global api
    # res = do_vk_request({'user_id': str(id)}, 'friends.get', need_token=False)
    res = api.friends.get(user_id=user_id)
    print(res)
    # now what?
    return set(res[0]['response']['items'])


def vk_stop():
    f = open('names.txt', 'w')
    f.write(str(names))
    f.close()


def vk_full_update():
    for i in range(1, 100):
        update(i)


try:
    names = eval(open('names.txt').read())
except:
    names = dict()


def show_standart(chat_id, mess):
    global api
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
    # b.bind('<Button-1>', lambda n: do_vk_request({'chat_id': chat_id, 'message': s}, 'messages.send'))
    b.bind('<Button-1>', lambda n: api.messages.send(chat_id=chat_id, message=s))
    b.pack()

    res.mainloop()


def besedka(event):
    bes = bchats[ncb.get()]
    curr = update(bes)
    show_standart(bchats[ncb.get()], curr)


api_init()

chats, bchats = get_chats()

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
vk_stop()
