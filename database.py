import sqlite3
import geolocation
conn = sqlite3.connect('DB.db')
cursor = conn.cursor()
subject_dict = {'Математика':0, 'Русский язык':1, 'Физика':2, 'Информатика':3, 'Литература':4, 'Биология':5, 'Химия':6, 'География':7}
level_dict = {'Подтянуть':0, 'ОГЭ/ЕГЭ/Вступительные':1, 'Олимпиады':2}

async def delete_by_id(idd):
    cursor.execute("DELETE FROM Users WHERE Id = {0}".format(idd))
    conn.commit()
    
async def create_new_user(user_dict):
    subject = subject_dict[user_dict['subject']]
    level = level_dict[user_dict['level']]
    msc_length = 15#round(geolocation.moscow_length([user_dict['lat'], user_dict['long']]) / 1000, 2)
    cursor.execute("INSERT INTO Users VALUES ({0}, '{1}', '{2}', {3}, {4}, {5}, '{6}', {7}, {8}, '{9}', {10})".format(
        user_dict['id'], user_dict['name'], user_dict['username'], user_dict['form'], subject, level,
        user_dict['adress'], user_dict['lat'], user_dict['long'], user_dict['anketa'], msc_length))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM Users WHERE Id = {0}".format(user_id))
    answer = cursor.fetchone()
    return answer

async def get_liked(id_1, id_2):
    ids = [(id_1, id_2), (id_2, id_1)]
    cursor.executemany("INSERT INTO Liked VALUES (?, ?)", ids)
    conn.commit()

def find_similar(idd):
    user = get_user(idd)
    sql = "SELECT * FROM Users WHERE Id NOT IN (SELECT Id_1 from Liked WHERE Id_2 = {0}) AND Id != {0} AND Subject = {1} AND Moscow_length - {2} BETWEEN -7 AND 7 AND AGE - {3} BETWEEN -2 AND 2".format(
        idd, user[4], user[-1], user[3])
    cursor.execute(sql)
    similars = cursor.fetchall()
    if len(similars) == 0:
        return ('Никого не найдено :(')
    routes = []
    for sim in similars:
        dist, route = geolocation.calculate_route([user[7], user[8]], [sim[7], sim[8]])
        print(sim[6], dist)
        routes.append([sim, route, dist])
    routes.sort(key=lambda x: x[1])
    print(routes[0])
    return list(routes[0][0]) + [str(int(routes[0][1]/60)) + ' минут на общественном транспорте']
    
#user_1 = {'id':10, 'name':'Nick', 'username':'AncestorsOfGods', 'form':17,
#          'subject':'Математика', 'level':'Олимпиады', 'adress':'6 корпус 2 улица Седова Москва', 'lat':1, 'long':2, 'anketa':'Я молодой и самый умный'}
#create_new_user(user_1)
