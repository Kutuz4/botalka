print(0)
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import config
import asyncio
import database
import logging
import geolocation
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
print(6)
logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.TOKEN)
print(3)
dp = Dispatcher(bot, storage=MemoryStorage())
print(4)
print(2)
class States(StatesGroup):
    MEETING = State()
    NAME = State()
    FORM = State()
    SUBJECT = State()
    LEVEL = State()
    ADRESS = State()
    ANKETA = State()
    CHECK = State()
    WORKING = State()
    
SENDS = {'start':'Привет! Я боталка 2.0, помогаю людям найти себе соратников для борьбы с прокрастинацией или просто хороших друзей. Приступим к знакомству?',
         'name':'Как тебя зовут?',
         'form':'Сколько тебе лет?',
         'subject': 'Какой предмет тебя интересует?',
         'level': 'Ты хочешь подтянуть что-то западающее, подготовиться к экзаменам или олимпиадам?',
         'adress':'Напиши мне свой адрес в формате: номер дома, корпус(если есть), улица, город. \nПример: 6, корпус 2, улица Маршала Жукова, Москва',
         'anketa': 'Расскажи немного о себе!',
         'ok?': 'Посмотри, это твоя анкета. Перейдем к работе или хочешь что-то исправить?',
         'ready': 'Напиши мне что угодно, чтобы приступить к поиску',
         'error':'Ой, случилась какая-то ошибка'}
def form_inline_keyboard(name, buttons_info):
    keyboard = InlineKeyboardMarkup()
    for i in range(len(buttons_info)):
        keyboard.row(InlineKeyboardButton(buttons_info[i], callback_data=name+'_'+buttons_info[i]))
    return keyboard

meeting_kb = form_inline_keyboard('meeting', ['Да', 'Нет'])
yes_button = InlineKeyboardButton('Да', callback_data='work_yes')
no_button = InlineKeyboardButton('Нет', callback_data='work_no')
refresh_anketa = InlineKeyboardButton('Хочу заполнить анкету заново', callback_data='work_new_anketa')
working_keyboard = InlineKeyboardMarkup().row(yes_button).row(no_button).row(refresh_anketa)
subjects_keyboard = form_inline_keyboard('subject', ['Математика', 'Русский язык', 'Физика', 'Информатика', 'Литература', 'Биология', 'Химия', 'География'])
level_keyboard = form_inline_keyboard('level', ['Подтянуть', 'ОГЭ/ЕГЭ/Вступительные', 'Олимпиады'])
ok_keyboard = form_inline_keyboard('ok', ['Перейти к поиску', 'Заполнить анкету заново'])
subjects_dict = {0:'Математика', 1:'Русский язык', 2:'Физика', 3:'Информатика', 4:'Литература', 5:'Биология', 6:'Химия', 7:'География'}
levels_dict = {0:'Подтянуть', 1:'ОГЭ/ЕГЭ/Вступительные', 2:'Олимпиады'}
@dp.message_handler(commands=['start'], state='*')
async def welcome(msg: types.Message):
    await States.MEETING.set()
    await bot.send_message(msg.from_user.id, SENDS['start'], reply_markup=meeting_kb)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('meeting'), state='*')
async def start_anketa(callback: types.CallbackQuery):
    if 'Да' in callback.data:
        await States.next()
        await bot.send_message(callback.from_user.id, SENDS['name'])
    else:
        await bot.send_message(callback.from_user.id, 'Если передумаешь, то просто нажми "Да"')

@dp.message_handler(state=States.NAME)
async def name(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        print(data)
        data['id'] = msg.from_user.id
        data['name'] = msg.text
        data['username'] = msg.from_user.username
        print(data)
        print(dir(msg.from_user))
        await database.delete_by_id(data['id'])
    await state.update_data(name=msg.text)
    await States.next()
    await bot.send_message(msg.from_user.id, SENDS['form'])

@dp.message_handler(state=States.FORM)
async def form(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['form'] = msg.text
    await States.next()
    await bot.send_message(msg.from_user.id, SENDS['subject'], reply_markup=subjects_keyboard)

@dp.callback_query_handler(lambda c:c.data and c.data.startswith('subject'), state=States.SUBJECT)
async def level(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        dt = str(callback.data)
        dt = dt[dt.index('_') + 1:]
        data['subject'] = dt        
    await States.next()
    await bot.send_message(callback.from_user.id, SENDS['level'], reply_markup=level_keyboard)

@dp.callback_query_handler(lambda x: x.data and x.data.startswith('level'), state=States.LEVEL)
async def adress(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        dt = str(callback.data)
        dt = dt[dt.index('_') + 1:]
        data['level'] = dt
    await States.next()
    await bot.send_message(callback.from_user.id, SENDS['adress'])

@dp.message_handler(state=States.ADRESS)
async def location(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['adress'] = msg.text
        data['lat'], data['long'] = geolocation.adress_to_geo(msg.text)
    await States.next()
    await bot.send_message(msg.from_user.id, SENDS['anketa'])

@dp.message_handler(state=States.ANKETA)
async def anketa(msg: types.Message, state: FSMContext):
    txt = ''
    async with state.proxy() as data:
        data['anketa'] = msg.text
        for key in data.keys():
            if key != 'username' and key != 'long' and key != 'lat' and key != 'id':
                txt += str(data[key]) + '\n'
    await States.next()
    await bot.send_message(msg.from_user.id, txt)
    await bot.send_message(msg.from_user.id, SENDS['ok?'], reply_markup=ok_keyboard)

@dp.callback_query_handler(lambda x: x.data and x.data.startswith('ok'), state=States.CHECK)
async def ok(callback: types.CallbackQuery, state: FSMContext):
    if 'Перейти' in str(callback.data):
        async with state.proxy() as data:
            info = {}
            for key in data.keys():
                info[key] = data[key]
            await database.create_new_user(info)
        await States.next()
        await bot.send_message(callback.from_user.id, SENDS['ready'])
    else:
        await database.delete_by_id(callback.from_user.id)
        await States.NAME.set()
        await bot.send_message(callback.from_user.id, SENDS['name'])

@dp.message_handler(state=States.WORKING)
async def start_work(msg: types.Message, state: FSMContext):
    similar = database.find_similar(msg.from_user.id)
    async with state.proxy() as data:
        data['last_similar_id'] = similar[0]
    if similar:
        print(similar)
        print(type(similar))
        txt = ''
        for key in range(len(list(similar))):
            if key != 0 and key != 7 and key != 8 and key != 2 and key != 10:
                if key == 4:
                    txt += subjects_dict[similar[key]] + '\n'
                elif key == 5:
                    txt += levels_dict[similar[key]] + '\n'
                else:
                    txt += str(similar[key]) + '\n'
        text = 'Смотри кого для тебя нашел:\n' + txt + 'Нравится?'
    else:
        text = SENDS['error']
    await bot.send_message(msg.from_user.id, text, reply_markup=working_keyboard)

@dp.callback_query_handler(lambda x: x.data and x.data.startswith('work'), state=States.WORKING)
async def working(msg: types.CallbackQuery, state: FSMContext):
    if "yes" in msg.data:
        txt = 'Желаю продуктивного и приятного общения! Вот твой соратник:\n @'
        async with state.proxy() as data:
            await database.get_liked(msg.from_user.id, data['last_similar_id'])
            txt += str(database.get_user(data['last_similar_id'])[2]) + '\n'
        await bot.send_message(msg.from_user.id, txt)
        await bot.send_message(msg.from_user.id, 'Предложить кого-то ещё?')
    elif 'no' in msg.data:
        similar = find_similar(msg.from_user.id)
        async with state.proxy() as data:
            await database.get_liked(msg.from_user.id, data['last_similar_id'])
            data['last_similar_id'] = similar[0]
        if similar:
            txt = ''
            for key in range(len(list(similar))):
                if key != 0 and key != 7 and key != 8 and key != 2 and key != 10:
                    if key == 4:
                        txt += subjects_dict[similar[key]] + '\n'
                    elif key == 5:
                        txt += levels_dict[similar[key]] + '\n'
                    else:
                        txt += str(similar[key]) + '\n'
            text = 'Смотри кого для тебя нашел:\n' + txt + 'Нравится?'
        else:
            text = SENDS['error']
        await bot.send_message(msg.from_user.id, text, reply_markup=working_keyboard)
    else:
        await database.delete_by_id(callback.from_user.id)
        await States.NAME.set()
        await bot.send_message(msg.from_user.id, SENDS['name'])
        
@dp.message_handler(lambda x: 'Алёнка' == x.text, state='*')
async def serdce(msg: types.Message):
    await bot.send_message(msg.from_user.id, 'Сердечко типо')
    for i in range(20):
        await bot.send_message(msg.from_user.id, chr(int('1F497', 16)))

print(1)
if __name__ == '__main__':
    executor.start_polling(dp)
