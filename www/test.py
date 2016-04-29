import orm
from models import User, Blog, Comment
import asyncio


@asyncio.coroutine
def test(loop):
    yield from orm.create_pool(loop=loop,user = 'www-data', password = 'www-data', db = 'awesome')

    user = User(id='ni',name = 'Coco Shi',email = '23@kkk', passwd = '102033', image = 'blank')

    yield from user.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
