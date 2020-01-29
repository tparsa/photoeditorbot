import sys
import asyncio
import telepot
from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import pave_event_space, per_chat_id, create_open
from PIL import Image
from psycopg2.pool import ThreadedConnectionPool

STARTING_NUM_OF_EDITS = 5

DNS = "postgresql://postgres:342|Klw,QSzk+@localhost/coloring_bot_db"
db_tcp = ThreadedConnectionPool(1, 30, DNS)

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
                for row_idx, row in enumerate(img_array):
                    for pixel_idx, pixel in enumerate(row):
                        grayscale = (0.3 * pixel[0]) + (0.59 * pixel[1]) + (0.11 * pixel[2])
                        img_array[row_idx][pixel_idx] = [grayscale, grayscale, grayscale]
                print("Done GrayScaling Start Saving")

                image = Image.fromarray(img_array, 'RGB')
                image.save(image_filename + 'edited.png')
            except Exception as e:
                print("FUCK")
                print(e)

    def _register(self, chat_id):
        conn = db_tcp.getconn()
        c = conn.cursor()

        c.execute("""SELECT count(*) from users WHERE chat_id = '{0}'""".format( chat_id ))
        count = c.fetchone()
        print("Count: ", count)
        if count[0] == 0:
            c.execute("""INSERT INTO users(chat_id, edits_left) VALUES('{0}', {1})""".format(chat_id, STARTING_NUM_OF_EDITS))
            conn.commit()

    def _get_edits_left(self, chat_id):
        conn = db_tcp.getconn()
        c = conn.cursor()

        c.execute("""SELECT edits_left from users WHERE chat_id = '{0}'""".format(chat_id))
        edits_left = c.fetchone()
        return edits_left[0]

    def handle_text(self, chat_id, msg):
        if msg['text'] == '/start':
            self._register(str(chat_id))
            return bot.sendMessage(chat_id, 'به بات رنگی کننده عکس خوش آمدید')
        elif msg['text'] == '/edits_left':
            return bot.sendMessage(chat_id, str(self._get_edits_left(chat_id)))

    def _decrease_remaining_edits(self, chat_id):
        conn = db_tcp.getconn()
        c = conn.cursor()
        c.execute("""UPDATE users SET edits_left = edits_left - 1 WHERE chat_id = '{0}'""".format(chat_id))
        conn.commit()

    async def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id, msg)

        if content_type == 'text':
            await self.handle_text(chat_id, msg)
        elif content_type == 'photo':
            if self._get_edits_left(chat_id) <= 0:
                await bot.sendMessage(chat_id, 'متاسفانه شما از تمام اعتبار خود استفاده کرده اید. برای افزایش اعتبار می توانید از لینک زیر دوستان خود را دعوت کنید')
            else:
                print("Yo")
                await bot.download_file(msg['photo'][-1]['file_id'], './' + str(chat_id) + '.png')
                print("dafuq")
                self.edit(str(chat_id))
                await bot.sendPhoto(chat_id, open(str(chat_id) + 'edited.png', 'rb'))
                self._decrease_remaining_edits(chat_id)
        else:
            print(content_type)
            await bot.sendMessage(chat_id, 'Yo')

if __name__ == "__main__":
    TOKEN = sys.argv[1]  # get token from command-line

    bot = telepot.aio.DelegatorBot(TOKEN, [
        pave_event_space()(
            per_chat_id(), create_open, PhotoEditor, timeout=10),
    ])

    loop = asyncio.get_event_loop()
    loop.create_task(MessageLoop(bot).run_forever())

    print('Listening ...')

    loop.run_forever()
