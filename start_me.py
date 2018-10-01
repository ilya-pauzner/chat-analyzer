# -*- encoding: utf-8 -*-
import logging
import sqlite3
from time import sleep
from tkinter import *
from tkinter.ttk import Combobox, Label

import vk


def logger(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if "place" in kwargs:
            logging.info("{}\t{}".format(func.__name__, kwargs["place"]))
        else:
            logging.info("{}".format(func.__name__))
        logging.debug("{} {} {}".format(func.__name__, args, kwargs))
        sys.stdout.flush()
        return res

    return wrapper


@logger
def vk_timeout(place, *args, **kwargs):
    sleep(1)


@logger
def db_init():
    global connection
    connection = sqlite3.connect('chat_data.db', isolation_level=None)
    result = list(connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='token_table'"))
    if not result:
        # first-time
        connection.execute('CREATE TABLE token_table (value text)')
    result = list(connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='userid_to_username'"))
    if not result:
        # first-time
        connection.execute('CREATE TABLE userid_to_username (id text, name text)')
    result = list(connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chatid_to_chatname'"))
    if not result:
        # first-time
        connection.execute('CREATE TABLE chatid_to_chatname (id text, name text)')


@logger
def api_init():
    global api, connection
    db_init()
    tokens = list(connection.execute('SELECT * from token_table'))
    if len(tokens) == 0:
        build_auth_window()
        vk_session = vk.AuthSession(app_id='4771271', user_login=login, user_password=password, scope=4096)
        connection.execute('INSERT INTO token_table VALUES (?)', (vk_session.access_token,))
    elif len(tokens) == 1:
        vk_session = vk.Session(access_token=tokens[0])
    else:
        logging.error('More than one token in database')
        vk_session = None

    api = vk.API(vk_session, v='5.35', lang='ru', timeout=10)
    assert api is not None


@logger
def enter(event):
    global login, password
    login = e1.get()
    password = e2.get()
    root.destroy()


@logger
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


@logger
def name_by_id(num):
    global api, connection
    result = list(connection.execute("SELECT name FROM userid_to_username WHERE id=(?)", (num,)))
    if result == []:
        # first-time this guy
        a = api.users.get(user_ids=num)
        vk_timeout(place="name by id")
        name = a[0]['first_name'] + ' ' + a[0]['last_name']
        connection.execute('INSERT INTO userid_to_username VALUES (?, ?)', (num, name))
        return name
    return result[0][0]


@logger
def to_put(a):
    return (a['id'], a['user_id'], len(a['body']))


@logger
def grab_messages(count, offset, chat_id):
    global api
    messages = api.messages.getHistory(count=count, offset=offset, chat_id=chat_id)
    vk_timeout(place="grab messages")
    messages = messages['items']
    return set(map(to_put, messages))


@logger
def grab_all_messages(chat_id):
    i = 0
    l = [0]
    table_name = " 'chat" + str(chat_id) + "' "
    result = list(connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=" + table_name))
    if not result:
        # first-time
        connection.execute('CREATE TABLE' + table_name + '(message_id integer, username text, length integer)')
        border = 0
    try:
        border = int(connection.execute('SELECT MAX(message_id) FROM' + table_name).fetchone()[0])
    except:
        border = 0
    bad = False
    while len(l) != 0 and not bad:
        l = grab_messages(200, i, chat_id)
        bad = False
        for elem in l:
            if elem[0] <= border:
                bad = True
                # return
            else:
                connection.execute('INSERT INTO' + table_name + 'VALUES (?, ?, ?)', elem)
        i += 200


# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\


@logger
def get_chats():
    global api
    try:
        # DB!
        f = open('chats', encoding='utf-8')
        a, b = eval(f.readline()), eval(f.readline())
        f.close()

        return a, b
    except:
        chats = []
        bchats = dict()
        while True:
            try:
                temp = api.messages.getChat(chat_id=len(chats) + 1)
                vk_timeout(place="get chats while true", cnt=len(chats) + 1)
            except:
                break
            chats.append(temp['title'])
            bchats[chats[-1]] = len(chats)

        # DB!
        f = open('chats', 'w', encoding='utf-8')
        f.write(str(chats) + '\n' + str(bchats))
        f.close()

        return chats, bchats


@logger
def vk_full_update():
    for i in range(1, 100):
        grab_all_messages(i)


@logger
def show_standart(chat_id):
    global api, cb, connection
    res = Tk()
    res.geometry('400x800')
    temp = cb.get()
    if temp == "По количеству сообщений":
        ans = list(connection.execute('SELECT username, COUNT(length) FROM chat' + str(
            chat_id) + ' GROUP BY username ORDER BY COUNT(length) DESC'))
    elif temp == "По количеству символов":
        ans = list(connection.execute(
            'SELECT username, SUM(length) FROM chat' + str(chat_id) + ' GROUP BY username ORDER BY SUM(length) DESC'))
    else:
        ans = list(connection.execute(
            'SELECT username, AVG(length) FROM chat' + str(chat_id) + ' GROUP BY username ORDER BY AVG(length) DESC'))
    s = ''
    for elem in ans:
        s += str(name_by_id(elem[0])) + ' ' + str(elem[1]) + '\n'
    t = Label(res, text=s)
    t.pack()

    b = Button(res, text='Послать в беседу')
    b.bind('<Button-1>', lambda n: api.messages.send(chat_id=chat_id, message=s))
    b.pack()

    res.mainloop()


@logger
def besedka(event):
    global ncb
    bes = bchats[ncb.get()]
    grab_all_messages(bes)
    show_standart(bchats[ncb.get()])


@logger
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


ncb = 0

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

api_init()
chats, bchats = get_chats()
show_main_window()
