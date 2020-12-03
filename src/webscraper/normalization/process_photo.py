import os
import asyncio
import aiohttp

from logging import getLogger

from google.cloud import storage


logger = getLogger()


class UploadPhoto:

    def __init__(self):
        self.s_client = self.s_client

    def start_client_storage(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'src/resonant-forge-294511-25f7c1fc6d0f.json'
        client = storage.Client()
        return client

    def store_images(self, photos_list):
        loop = asyncio.get_event_loop()
        stored_links = loop.run_until_complete(self.create_tasks(photos_list))
        return stored_links

    async def create_tasks(self, photos_list):
        urls = photos_list
        tasks = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                task = asyncio.create_task(self.get_data(url, session))
                tasks.append(task)
            await asyncio.gather(*tasks)
        result = [item._result for item in tasks]
        return result

    async def get_data(self, url, session):
        async with session.get(url) as response:
            logger.info('Downloading photo...')

            file = await response.read()
            file_name = os.path.basename(url)

            tasks = []
            task = asyncio.create_task(self.transfer_to_db(file, file_name))
            tasks.append(task)
            await asyncio.gather(*tasks)
            for item in tasks:
                result = item._result
            return result

    async def transfer_to_db(self, file, file_name):
        logger.info('Storing photo...')

        bucket_name = 'padopia-media-files'
        blob_name = 'photos/'
        bucket = self.s_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name + file_name)
        check = storage.Blob(bucket=bucket, name=blob_name + file_name).exists(client=self.s_client)
        if check is True:
            result = blob.public_url
        else:
            blob.upload_from_string(file, content_type='image')
            blob.make_public()
            result = blob.public_url
        return result
