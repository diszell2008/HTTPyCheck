import asyncio
import aiohttp
import yaml
from telegram.ext import Updater
from telegram.ext import CommandHandler
from ping3 import ping

with open("config.yaml", 'r') as yamlfile:
    config = yaml.safe_load(yamlfile)

telegram_group = config['telegram']['group']
http_timeout = aiohttp.ClientTimeout(total=config['http']['timeout'])

if isinstance(config['telegram']['proxy'], dict):
    REQUEST_KWARGS = {'proxy_url': config['telegram']['proxy']['proxy_url'],
                      'urllib3_proxy_kwargs': {
                          'username': config['telegram']['proxy']['username'],
                          'password': config['telegram']['proxy']['password'],
                      }
                      }
    updater = Updater(token=config['telegram']['token'], use_context=True, request_kwargs=REQUEST_KWARGS)
else:
    updater = Updater(token=config['telegram']['token'], use_context=True)
dispatcher = updater.dispatcher


async def check_icmp():
    while True:
        for host in config['icmp']['hosts']:
            req = ping(host, config['icmp']['timeout'], unit='ms')
            if req is None:
                updater.bot.send_message(chat_id=config['telegram']['group'], text=f'Loz Bot {host} Chết Cmn zòi')
            elif req > config['icmp']['timedelay']:
                updater.bot.send_message(chat_id=config['telegram']['group'],
                                         text=f'Knot {host} с delay ICMP= ' + str(req))
        await asyncio.sleep(config['main']['delay'])


def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Hello, I'm a monitoring bot! Your (group) ID = "
                                  + str(update.message.chat_id))


def list_group(update, context):
    message = 'The following sites are being monitored (HTTP):\n'
    if config['http']['sites'] is not None:
        for host in config['http']['sites']:
            if isinstance(host, dict):
                message = message + str(host['site']) + '\n'
            else:
                message = message + str(host) + '\n'
    message = message +'\nThe following resources are being monitored (ICMP):\n'
    if config['icmp']['hosts'] is not None:
        for host in config['icmp']['hosts']:
            message = message + str(host) + '\n'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('list', list_group))
updater.start_polling()

try:
    if config['icmp']['hosts'] is not None:
        asyncio.run(check_icmp())
except Exception as e:
    print(f"Error: [Exception] {type(e).__name__}: {e}")
