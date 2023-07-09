import random
import disnake
from disnake.ext import commands
import json
import pymongo
import time

# Установите вашу MongoDB URI
MONGODB_URI = 'mongodb+srv://CoffIMakYT:V0r0na22@cluster0.vfg3n8j.mongodb.net/'

intents = disnake.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or('/'), intents=intents)
allowed_user_ids = [339413294341423105, 638220065095024640]  # ID пользователя Discord, которому разрешено использовать команду

# Подключение к MongoDB
mongo_client = pymongo.MongoClient(MONGODB_URI)
db = mongo_client['BankDB']
collection = db['BankDB']

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.slash_command()
async def create_profile(ctx, minecraft_nick: str, balance: float, discord_id: disnake.User):
    # Ответить с задержкой
    await ctx.response.defer()
    # Проверка Discord ID пользователя
    if ctx.author.id not in allowed_user_ids:
        await ctx.send('У вас нет разрешения на использование этой команды.')
        return

    # Получение текущего значения bid
    last_profile = collection.find_one(sort=[('bid', pymongo.DESCENDING)])
    if last_profile:
        last_bid = last_profile.get('bid', 0000)
    else:
        last_bid = 0000

    # Увеличение значения bid на 1
    bid = last_bid + 1

    # Генерация случайного 4-значного числа для bid_transaction
    bid_transaction = random.randint(1000, 9999)

    # Создание профиля пользователя в формате JSON
    profile = {
        'minecraft_nick': minecraft_nick,
        'balance': balance,
        'discord_id': discord_id.id,
        'bid': bid,
        'bid_transaction': bid_transaction
    }

    # Запись профиля пользователя в базу данных JSON
    with open('profiles.json', 'r+') as file:
        data = json.load(file)
        data.append(profile)
        file.seek(0)
        json.dump(data, file, indent=4)

    # Запись профиля пользователя в MongoDB
    collection.insert_one(profile)

    await ctx.send('Профиль успешно создан и сохранен в базе данных!')
    
@bot.slash_command()
async def delete_profile(ctx, minecraft_nick: str):
    # Ответить с задержкой
    await ctx.response.defer()
    # Проверка Discord ID пользователя
    if ctx.author.id not in allowed_user_ids:
        await ctx.send('У вас нет разрешения на использование этой команды.')
        return

    # Поиск профиля пользователя по Minecraft-никнейму
    profile = collection.find_one({'minecraft_nick': minecraft_nick})
    if not profile:
        await ctx.send(f'Профиль с никнеймом {minecraft_nick} не найден.')
        return

    # Удаление профиля из базы данных JSON
    with open('profiles.json', 'r+') as file:
        data = json.load(file)
        data = [entry for entry in data if entry['minecraft_nick'] != minecraft_nick]
        file.seek(0)
        json.dump(data, file, indent=4)

    # Удаление профиля из MongoDB
    collection.delete_one({'minecraft_nick': minecraft_nick})

    await ctx.send(f'Профиль с никнеймом {minecraft_nick} успешно удален из базы данных!')

@bot.slash_command(
    name="increase_balance",
    description="Увеличить баланс профиля",
    options=[
        disnake.Option(
            name="minecraft_nick",
            description="Никнейм Minecraft",
            type=disnake.OptionType.string,
            required=True
        ),
        disnake.Option(
            name="amount",
            description="Сумма увеличения",
            type=disnake.OptionType.number,
            required=True
        ),
        disnake.Option(
            name="comment",
            description="Комментарий",
            type=disnake.OptionType.string,
            required=False
        )
    ]
)
async def increase_balance(ctx, minecraft_nick: str, amount: float, comment: str):
    # Ответить с задержкой
    await ctx.response.defer()

    # Поиск профиля пользователя по Minecraft-никнейму
    profile = collection.find_one({'minecraft_nick': minecraft_nick})
    if not profile:
        await ctx.send(f'Профиль с никнеймом {minecraft_nick} не найден.')
        return

    # Увеличение баланса
    new_balance = profile['balance'] + amount
    collection.update_one({'minecraft_nick': minecraft_nick}, {'$set': {'balance': new_balance}})

    if comment:
        await ctx.send(f'Баланс профиля {minecraft_nick} успешно увеличен на {amount}. Комментарий: {comment}.')

        # Отправка уведомления в личные сообщения
        user = await bot.fetch_user(profile['discord_id'])
        if user:
            await user.send(f'Ваш баланс был увеличен на {amount}. Причина: {comment}. Обновленный баланс: {new_balance}.')
    else:
        await ctx.send(f'Баланс профиля {minecraft_nick} успешно увеличен на {amount}.')

@bot.slash_command(
    name="decrease_balance",
    description="Уменьшить баланс профиля",
    options=[
        disnake.Option(
            name="minecraft_nick",
            description="Никнейм Minecraft",
            type=disnake.OptionType.string,
            required=True
        ),
        disnake.Option(
            name="amount",
            description="Сумма уменьшения",
            type=disnake.OptionType.number,
            required=True
        ),
        disnake.Option(
            name="comment",
            description="Комментарий",
            type=disnake.OptionType.string,
            required=False
        )
    ]
)
async def decrease_balance(ctx, minecraft_nick: str, amount: float, comment: str):
    # Ответить с задержкой
    await ctx.response.defer()

    # Поиск профиля пользователя по Minecraft-никнейму
    profile = collection.find_one({'minecraft_nick': minecraft_nick})
    if not profile:
        await ctx.send(f'Профиль с никнеймом {minecraft_nick} не найден.')
        return

    # Уменьшение баланса
    new_balance = profile['balance'] - amount
    collection.update_one({'minecraft_nick': minecraft_nick}, {'$set': {'balance': new_balance}})

    if comment:
        await ctx.send(f'Баланс профиля {minecraft_nick} успешно уменьшен на {amount}. Комментарий: {comment}.')

        # Отправка уведомления в личные сообщения
        user = await bot.fetch_user(profile['discord_id'])
        if user:
            await user.send(f'Ваш баланс был уменьшен на {amount}. Причина: {comment}. Обновленный баланс: {new_balance}.')
    else:
        await ctx.send(f'Баланс профиля {minecraft_nick} успешно уменьшен на {amount}.')
  
@bot.event
async def on_transaction_insert(change):
    # Получение новой транзакции
    transaction = change['fullDocument']

    # Получатель транзакции
    recipient = transaction.get('recipient')

    # Поиск профиля получателя по Minecraft-никнейму
    profile = collection.find_one({'minecraft_nick': recipient})
    if not profile:
        return

    # Отправка уведомления в личные сообщения получателя
    user = await bot.fetch_user(profile['discord_id'])
    if user:
        await user.send(f'Вы получили транзакцию на сумму {transaction["amount"]} от {transaction["sender"]}.')

    async def watch_transactions():
        while True:
            # Проверка наличия новых изменений
            change = collection.watch().next()
            if change['operationType'] == 'insert':
                await on_transaction_insert(change)
        
            # Пауза между проверками изменений
            time.sleep(1)

    #Запуск отслеживания транзакций
    bot.loop.create_task(watch_transactions())

bot.run('MTExMjcyOTgyNzE3MTExOTEzNQ.GA1Gx8.5TYp0uQ179E4kd7B_m2okdkwvJR6mHlgvjemUU')
