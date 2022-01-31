import discord
from discord.ext import commands
import transcriber
from transcriber import *
import json
import time
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
load_dotenv()

CMD_PREFIX = '!'
client = commands.Bot(command_prefix=CMD_PREFIX, help_command=None)

@client.event
async def on_ready():
    print('Logged in as', client.user.name)

@client.command()
async def setvideo(ctx, url):
    if not valid_youtube_url(url):
        await ctx.send('Invalid YouTube link')
        return
    await ctx.send(":yellow_circle: Your video will begin being processed for a transcription. You will get notified when the process is complete")
    try:
        save_transcript(url)
    except:
        await ctx.send('An error occurred while processing your video. Try running the command again')
        return
    await ctx.send(f':green_circle: {ctx.message.author.mention} Finished processing video. Run !transcribe to transcribe any segment of the video')

@client.command()
async def transcribe(ctx, start_timestamp, end_timestamp):
    if TRANSCRIPT_FILENAME not in os.listdir():
        await ctx.send('You have not supplied a video to transcribe. Run !setvideo')
        return

    transcript = retrieve_transcript()
    if len(transcript) == 0:
        await ctx.send('The transcript for this video is empty')
        return

    word_start_values = [word['start'] for word in transcript]
    word_end_values = [word['end'] for word in transcript]
    start_milliseconds = timestamp_to_milliseconds(start_timestamp)
    end_milliseconds = timestamp_to_milliseconds(end_timestamp)
    first_word_start = min(word_start_values, key=lambda i: abs(i - start_milliseconds))
    last_word_end = min(word_end_values, key=lambda i: abs(i - end_milliseconds))

    msg_builder = ''
    for word in transcript:
        if first_word_start <= word['start'] <= last_word_end:
            msg_builder += word['text'] + ' '
    if len(msg_builder) > 2000:
        await ctx.send('The transcript you requested is too large to send over Discord')
        return
    await ctx.send(msg_builder)

@client.command()
async def help(ctx):
    embed = discord.Embed(
        title='Help',
        color=discord.Color.red()
    )
    embed.add_field(name=f'{CMD_PREFIX}setvideo [YouTube URL]', value='Set the YouTube video you want to transcribe')
    embed.add_field(name=f'{CMD_PREFIX}transcribe [start timestamp] [end timestamp]', value='Transcribe a segment of the video', inline=False)

    await ctx.send(embed=embed)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Missing required argument(s)')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You are missing the required permissions to run this command')
    else:
        print('Error not caught')
        print(error)

def retrieve_transcript():
    with open(TRANSCRIPT_FILENAME, 'r') as file:
        transcript = file.read()
        return json.loads(transcript)

def valid_youtube_url(url):
    try:
        url_id = parse_qs(urlparse(url).query)['v'][0]
    except:
        return False
    request = requests.get('https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v=' + url_id)
    return request.status_code == 200

def timestamp_to_milliseconds(timestamp):
    timestamp_split = timestamp.split(':')
    minutes = int(timestamp_split[0])
    seconds = int(timestamp_split[1])
    return abs((minutes * 60 + seconds) * 1000)

if __name__ == '__main__':
    for file in os.listdir():
        if file.endswith('.txt'):
            os.remove(file)
    client.run(os.getenv('DISCORD_TOKEN'))
