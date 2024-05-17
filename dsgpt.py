import disnake
from disnake.ext import commands

from openai import OpenAI

import sqlite3

from dotenv import load_dotenv
import os

load_dotenv()

client = commands.Bot(command_prefix='/',
                      help_command=None,command_sync_flags=commands.CommandSyncFlags.all(),
                      intents=disnake.Intents.all())

client.remove_command("help")


cliente = OpenAI(
  api_key=os.getenv('KEY')
)

connection = sqlite3.connect('gpt.db')
cursor = connection.cursor()

@client.event
async def on_ready():


    cursor.execute("""CREATE TABLE IF NOT EXISTS gpt(
        temperature BIGINT,
        model TEXT
    )""")
    cursor.execute("SELECT model FROM gpt")
    result = cursor.fetchone()


    if result is None:
        cursor.execute("INSERT INTO gpt VALUES(4,'gpt-3.5-turbo')")
        #cursor.execute('INSERT INTO gpt (model) VALUES (?)', ('gpt-3.5-turbo',))
        connection.commit()


    await client.change_presence(activity=disnake.Game(name="Chat"))
    print(f".discord bot connect: {client.user}")
    #await client._sync_application_commands()



class Gpt:
    def __init__(self):
        self.lisit = []

    def gpt(self, promt: str, img: list = None):


        response = {
                "role": "user",
                "content": [
                    {"type": "text", "text": promt}

                ]
            }

        if img:
            for i in img:
                response['content'].append({"type": "image_url", "image_url": {"url": i}})
            self.lisit.append(response)
            print(self.lisit)
            print('image')
        else:
            self.lisit.append({"role": "user", "content": [{"type": "text", "text": promt}]})
            print('text')

        model= cursor.execute("SELECT model FROM gpt").fetchone()[0]
        request_params = {
            "model": f"{model}",
            "messages": self.lisit,
            "max_tokens": 150,
            "temperature": 0.8,
            "timeout": 25
        }


        if "stop" in request_params and request_params["stop"] is None:
            del request_params["stop"]


        completion = cliente.chat.completions.create(**request_params)

        return completion.choices[0].message.content


    async def add(self, context):
        # if self.lisit[0]['content'][1]["image_url"]['url'] is not None:
        #     self.lisit.append({
        #         "role": "assistant",
        #         "content": [
        #             {"type": "text", "text": context},
        #             {"type": "image_url", "image_url": {"url":image}}
        #         ]
        #     })
        #     print(self.lisit)
        # else:
        self.lisit.append({"role": "assistant", "content": [{"type": "text", "text": context}]})
        print(self.lisit)

    async def delete(self):
        for i in range(min(5, len(self.lisit))):
            del self.lisit[i]

    async def purge(self):
        self.lisit = []

gpet = Gpt()

@client.slash_command(description='Выбрать модель gpt.')
@commands.has_permissions(administrator=True)
async def model(inter: disnake.ApplicationCommandInteraction, model: str = None):

    if model not in ['gpt-3.5-turbo', 'gpt-4o'] or model == None:
        curr_model = cursor.execute("SELECT model FROM gpt").fetchone()[0]

        await inter.response.send_message(f'**Текущая модель GPT:  {curr_model}**',ephemeral=True)
    else:

        role = disnake.utils.get(inter.guild.roles, name='tester')
        if role in inter.author.roles:

            cursor.execute("UPDATE gpt SET model = ?",(model,))
            connection.commit()
            #await inter.followup.send(f"'**Модель изменена на {model}**",ephemeral=True)
            await inter.response.send_message(f'**Модель изменена на {model}**',ephemeral=True)
        else:
            await inter.response.send_message('**Ты не можешь менять модель GPT**',ephemeral=True)
@client.slash_command(description='Очистить историю чата с chatgpt.')
async def purge(inter):
    print(gpet.lisit)
    await gpet.purge()
    print(gpet.lisit)
    await inter.response.send_message('Успешно.', delete_after=10)

@client.event
async def on_message(message):
    channel_id = message.channel.id
    model = cursor.execute("SELECT model FROM gpt").fetchone()[0]
    url = []
    for attachment in message.attachments:
        if attachment.filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            url.append(attachment.url)
    if url == [] and model == 'gpt-3.5-turbo' or url != [] and model =='gpt-4o' or url == [] and model =='gpt-4o':
        if not message.author.bot:
            if message.content.startswith('<@1085887506710548551>'):
                if channel_id == 1236752602213908560:
                    await message.channel.trigger_typing()
                    text = message.content.replace('<@1085887506710548551>','').strip()
                    print(text)
                    await message.add_reaction('✅')

                    if len(gpet.lisit) >= 16:
                        await gpet.delete()



                    answer = gpet.gpt(promt=text, img=url)
                    await message.reply(answer)
                    await gpet.add(context=answer)

                else:
                    await message.reply('Чтобы использовать chatgpt в личном чате - купите подписку. ')
    else:
        await message.reply('Обработка изображений не поддерживается в gpt-3.5-turbo')

@client.slash_command()
@commands.has_permissions(administrator=True)
async def clear(inter: disnake.ApplicationCommandInteraction, amount: int = 15):
    await inter.response.defer()
    deleted_messages = await inter.channel.purge(limit=amount + 1)
    #await inter.followup.send(f"{len(deleted_messages)} сообщений удалено.")

@clear.error
async def clear_error(inter, error):
    if isinstance(error, commands.MissingPermissions):
        embe = disnake.Embed(title="",description="У бота недостаточно прав для использования этой команды.")

        await inter.response.send_message(embed=embe,ephemeral=True)

@client.slash_command(description='Сгенерировать изображение.')
@commands.has_permissions(administrator=True)
async def dall(ctx, promt: str):
    embe = disnake.Embed(title='', description='Ожидание ответа от dall-e', colour=disnake.Colour(0x2b2d31))
    await ctx.send(embed=embe)
    try:
        generation_response = cliente.images.generate(
            model="dall-e-2",
            prompt=promt,
            n=1,
            size="256x256",
            response_format="url",
        )

        emb = disnake.Embed(title=f'> {ctx.author.name}', description='', colour=disnake.Colour(0x2b2d31))
        emb.set_image(url=f"{generation_response.data[0].url}")
        emb.add_field(name='promt:', value=f'```{promt}```')
        await ctx.send(embed=emb)
    except:
        await ctx.send('Некорректный запрос..')
@dall.error
async def dall_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embe = disnake.Embed(title="",description="")
        embe.set_image(url="https://i.pinimg.com/originals/0d/74/f9/0d74f9c0803f68e49380a134acc028db.gif")
        await ctx.send(embed=embe)


client.run(os.getenv('TOKEN'))


