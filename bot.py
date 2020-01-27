import sys
import asyncio
import telepot
from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import pave_event_space, per_chat_id, create_open
from PIL import Image

class MessageCounter(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(MessageCounter, self).__init__(*args, **kwargs)
        self._count = 0

    async def on_chat_message(self, msg):
        self._count += 1
        await self.sender.sendMessage(self._count)

class PhotoEditor(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(PhotoEditor, self).__init__(*args, **kwargs)

    def edit(self, image_filename):
            try:
                image = Image.open(image_filename + '.png')
                # GrayScale
                print("Start GrayScaling")
                import numpy as np
                img_array = np.array(image)
                print(img_array)
                for row in img_array:
                    for pixel in row:
                        grayscale = (0.3 * pixel[0]) + (0.59 * pixel[1]) + (0.11 * pixel[2])
                        pixel = [grayscale, grayscale, grayscale]
                print("Done GrayScaling Start Saving")

                image = Image.fromarray(img_array, 'RGB')
                image.save(image_filename + 'edited.png')
            except Exception as e:
                print("FUCK")
                print(e)

    async def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        
        if content_type == 'photo':
            print("Yo")
            await bot.download_file(msg['photo'][-1]['file_id'], './' + str(chat_id) + '.png')
            print("dafuq")
            self.edit(str(chat_id))
            await bot.sendPhoto(chat_id, open(str(chat_id) + 'edited.png'))
        else:
            print(content_type)
            bot.sendMessage(chat_id, 'Yo')

TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.aio.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, PhotoEditor, timeout=10),
])

loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())
print('Listening ...')

loop.run_forever()
