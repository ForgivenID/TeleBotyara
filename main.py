import asyncio

from misc import *
from threading import Thread, Lock

from aiogram import Bot, Dispatcher, executor, types
from path import Path
import pickle as pk

import random as rn


class User:
    def __init__(self, _id):
        self.id: str = _id
        self.engaged: None | str = None
        self.searching: bool = False
        self.history = {}

    def save(self):
        with open(f'history/{self.id}.shpk', 'wb+') as file:
            pk.dump(self, file)

    def load(self):
        if Path(f'history/{self.id}.shpk').exists():
            with open(f'history/{self.id}.shpk', 'rb') as file:
                self.history = pk.load(file)

    def send_message(self, text):
        executor.start(dp, bot.send_message(self.id, text))

    def disengaged(self):
        self.send_message(PRE_DISENGAGED)
        self.send_message(rn.choice(DISENGAGED_PROMPTS))
        self.send_message(POST_DISENGAGE)
        self.engaged = None

    def disengage(self):
        if self.searching:
            self.searching = False
            self.send_message(STOP_SEARCH)
        if self.engaged is None:
            return
        self.disengage()
        [user.disengaged() for user in users.values() if user.engaged == self.id]
        self.send_message(PRE_DISENGAGE)
        self.send_message(rn.choice(DISENGAGE_PROMPTS))
        self.send_message(POST_DISENGAGE)
        self.engaged = None

    def search(self):
        self.searching = True

    def found(self, _id):
        self.send_message(FOUND)
        self.searching = False
        self.engaged = _id


# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
users: dict[str, User] = {}
users_lock = Lock()



@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.chat.id not in users:
        with users_lock:
            users[message.chat.id] = User(message.chat.id)
        await message.reply(WELCOME)
        return
    await message.reply(ALREADY_WELCOME)


@dp.message_handler(commands=['new'])
async def new_engagement(message: types.Message):
    if message.chat.id not in users:
        await message.reply("Слушай, ты даже еще не Чукча, ты бы /start прописал, а не выпендривался.")
        return
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    users[message.chat.id].disengage()
    await message.reply("Ищем Чукчу для Чукчи...")
    users[message.chat.id].search()


@dp.message_handler(commands=['stop'])
async def disengage(message: types.Message):
    if message.chat.id not in users:
        await message.reply("Слушай, ты даже еще не Чукча, ты бы /start прописал, а не выпендривался.")
        return
    users[message.chat.id].disengage()


@dp.message_handler()
async def echo(message: types.Message):
    if message.chat.id not in users:
        await message.reply("Слушай, ты даже еще не Чукча, ты бы /start прописал, а не выпендривался.")
        return
    if not users[message.chat.id].engaged:
        await message.answer("Сорян, Чукча, но я с тобой уж точно разговаривать не буду.")
        return
    users[users[message.chat.id].engaged].send_message(message.text)

async def searching():
    while True:
        await asyncio.sleep(3)
        with users_lock:
            in_search = [user for user in users.values() if user.searching]
            if len(in_search) > 1:
                user1 = in_search[0]
                user2 = rn.choice(in_search[1:])
                user1.found(user2.id)
                user2.found(user1.id)

def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(searching())
    main()
