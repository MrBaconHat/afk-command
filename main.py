import discord
import re
import json
from discord.ext import commands
from datetime import datetime, timedelta

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
intents.message_content = True


BOT_TOKEN = 'your bot token here'


def saveDataToJson(ctx, reason):
    with open('user_data.json') as load_file:
        data_json = json.load(load_file)

    if ctx.author.id in data_json['afk_data']:
        raise ValueError("Your afk is already set!")

    data_json['afk_data'][str(ctx.author.id)] = {
        'author_name': ctx.author.name,
        'author_id': ctx.author.id,
        'reason': reason,
        "afkSessionCreatedAt": int(datetime.now().timestamp()),
        'mentionMonitor': []
    }

    with open('user_data.json', 'w') as write_file:
        json.dump(data_json, write_file, indent=4)


def storePingerInformation(author_obj: discord.Message, ping_receiver):
    with open('user_data.json', 'r') as read_file:
        data_json = json.load(read_file)

    pinger_information_dictionary = {
        'username': author_obj.author.global_name,
        'sendAt': int(datetime.now().timestamp()),
        'messageLink': f'https://discord.com/channels/{author_obj.guild.id}/{author_obj.channel.id}/{author_obj.id}'
    }

    data_json["afk_data"][str(ping_receiver)]["mentionMonitor"].append(pinger_information_dictionary)

    with open('user_data.json', 'w') as write_file:
        json.dump(data_json, write_file, indent=4)


def clearUserFromAFK(user_id):
    with open("user_data.json", 'r') as read_file:
        data_json = json.load(read_file)

    del data_json["afk_data"][str(user_id)]

    with open("user_data.json", 'w') as write_file:
        json.dump(data_json, write_file, indent=4)


class dispMentions(discord.ui.View):

    def __init__(self, collection: list, number1, number2, button_press_counts=0):
        super().__init__()

        self.total_pings = len(collection) // 6
        self.total_button_press_count = button_press_counts
        self.data_list = collection
        self.number1 = number1
        self.number2 = number2

        if button_press_counts >= self.total_pings:
            self.forward_button.disabled = True
            self.forward_button.style = discord.ButtonStyle.gray

        if button_press_counts <= 0:
            self.back_button.disabled = True
            self.back_button.style = discord.ButtonStyle.gray

    @discord.ui.button(label="←", style=discord.ButtonStyle.blurple)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.button):
        if button:
            pass

        self.total_button_press_count -= 1

        number_1 = self.number1 - 6
        number_2 = self.number2 - 6

        embed = self.create_embed(number1=number_1, number2=number_2)

        view = dispMentions(collection=self.data_list, button_press_counts=self.total_button_press_count,
                            number1=number_1, number2=number_2)

        await interaction.response.edit_message(view=view, embed=embed)

    @discord.ui.button(label="→", style=discord.ButtonStyle.blurple)
    async def forward_button(self, interaction: discord.Interaction, button: discord.ui.button):
        if button:
            pass

        number_1 = self.number2
        number_2 = self.number2 + 6

        self.total_button_press_count += 1

        embed = self.create_embed(number1=number_1, number2=number_2)

        view = dispMentions(collection=self.data_list, button_press_counts=self.total_button_press_count,
                            number1=number_1, number2=number_2)

        await interaction.response.edit_message(view=view, embed=embed)

    def create_embed(self, number1, number2):

        embed = discord.Embed(
            title=f"You received {len(self.data_list)} mentions",
            description=None,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"({self.total_button_press_count}/{self.total_pings})")
        for data in self.data_list[number1:number2]:
            embed.add_field(
                name=f"{data.get("username")}, <t:{data.get("sendAt")}:R>",
                value=f"[Click to view message]({data.get("messageLink")})"
            )
        return embed


@bot.command()
async def afk(ctx, reason='AFK'):

    saveDataToJson(ctx, reason)

    embed = discord.Embed(
        title="AFK Set!",
        description=f"I have marked you as AFK in all servers, with reason: {reason}",
        color=discord.Color.blurple()
    )
    embed.set_author(icon_url=ctx.author.avatar, name=ctx.author.name)

    await ctx.send(embed=embed)


@bot.event
async def on_message(message: discord.Message):

    with open('user_data.json', 'r') as read_file:
        data_json = json.load(read_file)

    if str(message.author.id) in data_json["afk_data"]:

        mentions_list = data_json["afk_data"][f"{message.author.id}"]["mentionMonitor"]
        sessionCreatedAt = data_json["afk_data"][f"{message.author.id}"]["afkSessionCreatedAt"]

        afk_active_duration = int(datetime.now().timestamp()) - sessionCreatedAt

        active_duration_timing = timedelta(seconds=afk_active_duration)

        timing_text = ''

        year = (active_duration_timing.days // 365)
        month = (active_duration_timing.days // 30) % 30
        week = (active_duration_timing.days // 7) % 7
        day = active_duration_timing.days // 86400

        hour = (active_duration_timing.seconds // 3600) % 24
        minutes = (active_duration_timing.seconds // 60) % 60
        seconds = (active_duration_timing.seconds % 60)

        timing_text_msgs = [
            (year, 'year', 'years'),
            (month, 'month', 'months'),
            (week, 'week', 'weeks'),
            (day, 'day', 'days'),
            (hour, 'hour', 'hours'),
            (minutes, 'minute', 'minutes'),
            (seconds, 'second', 'seconds')
        ]

        for value, string, strings in timing_text_msgs:
            if value >= 1:
                timing_text = f'{value} {strings if value > 1 else string}'
                break

        embed = discord.Embed(
            title=f"You received {len(mentions_list)} mentions",
            description=None,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"(0/{len(mentions_list) // 6})")
        for ping_data in mentions_list[0:6]:
            embed.add_field(
                name=f"**{ping_data.get("username", None)}** <t:{ping_data.get("sendAt")}:R>",
                value=f"[Click to view message]({ping_data.get("messageLink", None)})"
            )

        view = dispMentions(collection=mentions_list, number2=6, number1=0)
        await message.reply(content=f"Welcome back, {message.author.name}! I removed your AFK. "
                                           f"You were AFK for {timing_text}",
                                   view=view if len(mentions_list) > 0 else None,
                                   embed=embed if len(mentions_list) > 0 else None)
        clearUserFromAFK(message.author.id)

    user_id_from_ping = re.search(r"<@(\d+)>", message.content)

    await bot.process_commands(message)

    if not user_id_from_ping:
        return

    user_id = user_id_from_ping.group(1)

    if not user_id:
        return

    if user_id in data_json["afk_data"]:

        username = data_json["afk_data"][f"{message.author.id}"]["author_name"]
        reason = data_json["afk_data"][f"{message.author.id}"]["reason"]
        storePingerInformation(message, ping_receiver=user_id)

        await message.reply(content=f"{username} is AFK globally: {reason}")
        return


@bot.event
async def on_ready():
    print("Successfully logged in as:", bot.user.name)

try:
    bot.run(BOT_TOKEN)
except discord.errors.LoginFailure:
    print("\nYou've provided incorrect token. Please enter the correct bot token.\n")

