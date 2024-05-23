
import json

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
    await client._sync_application_commands()



class Gpt:
    def __init__(self):
        self.lisit = []

    def gpt(self, promt: str = '', img: list = None, name: str=''):

        response0 = {
            'context': [{"role": "user", "content": [{"type": "text", "text": promt}]}, ],

        }

        system = {"role": "system", "content": "Ты ассистент. Повторяй все сообщения точно и отвечай на вопросы."}

        files = []

        for file in os.listdir('.requests/'):
            files.append(file)

        if img:
            response0['context'].insert(0, system)
            for i in img:
                response0['context'][1]['content'].append({"type": "image_url", "image_url": {"url": i}})

            dir = f'{name}.json'
            if dir not in files:

                with open(f'.requests/{name}.json', 'w',encoding='UTF-8') as f:

                    json.dump(response0, f, ensure_ascii=False)

            else:

                with open(f'.requests/{name}.json','r',encoding='UTF-8') as f:
                    templates = json.load(f)
                    #print(templates)
                    templates['context'].append({"role": "user", "content": [{"type": "text", "text": promt}]})
                with open(f'.requests/{name}.json','w',encoding='UTF-8') as f:
                    json.dump(templates, f, ensure_ascii=False)

                with open(f'.requests/{name}.json',encoding='UTF-8') as f:
                    templates = json.load(f)

                    for i in img:
                        templates['context'][-1]['content'].append({"type": "image_url", "image_url": {"url": i}})
                with open(f'.requests/{name}.json','w',encoding='UTF-8') as f:
                    json.dump(templates, f, ensure_ascii=False)

            print('image')
        else:
            dir = f'{name}.json'
            if dir not in files:

                response0['context'].insert(0,system)
                with open(f'.requests/{name}.json', 'w',encoding='UTF-8') as f:
                    json.dump(response0, f,ensure_ascii=False)

            else:
                with open(f'.requests/{name}.json','r',encoding='UTF-8') as f:
                    templates = json.load(f)
                    #print(templates)
                    templates['context'].append({"role": "user", "content": [{"type": "text", "text": promt}]})
                with open(f'.requests/{name}.json','w',encoding='UTF-8') as f:
                    json.dump(templates, f, ensure_ascii=False)



        with open(f'.requests/{name}.json', 'r', encoding='UTF-8') as f:
            templates = json.load(f)
            context = templates['context']
            print(context)
        model = cursor.execute("SELECT model FROM gpt").fetchone()[0]
        request_params = {
            "model": f"{model}",
            "messages": context,
            "max_tokens": 150,
            "temperature": 0.8,
            "timeout": 25
        }


        if "stop" in request_params and request_params["stop"] is None:
            del request_params["stop"]


        completion = cliente.chat.completions.create(**request_params)

        return completion.choices[0].message.content


    async def add(self, context,name:str=''):
        with open(f'.requests/{name}.json', 'r', encoding='UTF-8') as f:
            templates = json.load(f)
        #print(templates)
        templates['context'].append({"role": "assistant", "content": [{"type": "text", "text": context}]})
        with open(f'.requests/{name}.json', 'w', encoding='UTF-8') as f:
            json.dump(templates, f, ensure_ascii=False)



    async def delete(self):
        for i in range(min(5, len(self.lisit))):
            del self.lisit[i]

    async def purge(self,name:str):
        os.remove(f'.requests/{name}.json')

gpet = Gpt()

@client.slash_command(description='Выбрать модель GPT')
@commands.has_permissions(administrator=True)
async def model(inter,model:int = commands.Param(choices=[
                                         disnake.OptionChoice("gpt-3.5-turbo", 0),
                                         disnake.OptionChoice("gpt-4o", 1)],default='gpt-3.5-turbo',description='Выбрать модель gpt')):

    if model == 0 or model == 1:
        if model == 0:
            cursor.execute("UPDATE gpt SET model = ?", ('gpt-3.5-turbo',))
            connection.commit()
            await inter.response.send_message(f"**Модель изменена на gpt-3.5-turbo**",ephemeral=True)
        elif model == 1:
            cursor.execute("UPDATE gpt SET model = ?", ('gpt-4o',))
            connection.commit()
            await inter.response.send_message(f"**Модель изменена на gpt-4o**", ephemeral=True)
    else:
        curr_model = cursor.execute("SELECT model FROM gpt").fetchone()[0]
        await inter.response.send_message(f'**Текущая модель GPT:  {curr_model}**',ephemeral=True)


@client.slash_command(description='Очистить историю чата с chatgpt.')
async def purge(inter):
    try:
        await gpet.purge(name=inter.author.name)
        await inter.response.send_message('Успешно.', delete_after=10)
    except:
        embe = disnake.Embed(title='Всё чисто!',description='')
        await inter.response.send_message(embed=embe)
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

            if message.content.replace('<@832702535080869888>','') != message.content:
                if channel_id in [1236752602213908560,1241798042387222668]:
                    await message.add_reaction('✅')
                    if url != []: await message.add_reaction('🖼️')

                    await message.channel.trigger_typing()

                    text = message.content.replace('<@832702535080869888>','').strip()

                    answer = gpet.gpt(promt=text, img=url,name=message.author.name)
                    await message.reply(answer)
                    await gpet.add(context=answer,name=message.author.name)

                else:
                    await message.reply('Чтобы использовать chatgpt в личном чате - купите подписку. ')
    else:
        await message.reply('Обработка изображений не поддерживается в gpt-3.5-turbo')

@client.slash_command()
@commands.has_permissions(administrator=True)
async def clear(inter: disnake.ApplicationCommandInteraction, amount: int = 15):
    await inter.response.defer()
    deleted_messages = await inter.channel.purge(limit=amount + 1)

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
        embe = disnake.Embed(title="**Некорректный запрос..**", description="")
        await ctx.send(embed=embe)




client.run(os.getenv('TOKEN'))


