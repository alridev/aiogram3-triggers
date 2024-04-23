
#  *-+-+-+-+ +-+-+ +-+-+-+-+-+-+-+-+-+-* #
#  |S|o|f|t| |b|y| |@|z|c|x|w|_|l|o|l|z| #
#  *-+-+-+-+ +-+-+ +-+-+-+-+-+-+-+-+-+-* #


from aiogram import Bot, Dispatcher, F, Router, types

# Import aiogram3 triggers
from aiogram3_triggers import TRouter

API_TOKEN = 'Bot Secret'


# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)


dp = Dispatcher()

# create routers

router = Router()

# create aiogram3 triggers router
trouter = TRouter()


@trouter.triggers_handler(1)
async def trigger_print(dispatcher: Dispatcher, bot: Bot):
    print("Trigger on")


@router.message(F.text == 'hello')
async def send_hello(message: types.Message):
    await message.reply("Hi!\nI'm Triggers Bot!\nPowered by zcxw.")

if __name__ == '__main__':
    dp.include_routers(router, trouter)
    dp.run_polling(bot)
