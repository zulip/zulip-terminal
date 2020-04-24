# Generated by Django 1.10.5 on 2017-03-09 05:23
import io
import logging
import os
import urllib
from mimetypes import guess_type
from typing import Dict, Optional, Tuple, Union

import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
from django.db import migrations, models
from django.db.backends.postgresql_psycopg2.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps
from PIL import Image, ImageOps
from requests import ConnectionError, Response


def force_str(s: Union[str, bytes], encoding: str = 'utf-8') -> str:
    """converts a bytes type to a string"""
    if isinstance(s, str):
        return s
    elif isinstance(s, bytes):
        return s.decode(encoding)
    else:
        raise TypeError("force_str expects a string type")


class Uploader:
    def __init__(self) -> None:
        self.path_template = "{realm_id}/emoji/{emoji_file_name}"
        self.emoji_size = (64, 64)

    def upload_files(self, response: Response, resized_image: bytes,
                     dst_path_id: str) -> None:
        raise NotImplementedError()

    def get_dst_path_id(self, realm_id: int, url: str, emoji_name: str) -> Tuple[str, str]:
        _, image_ext = os.path.splitext(url)
        file_name = ''.join((emoji_name, image_ext))
        return file_name, self.path_template.format(realm_id=realm_id, emoji_file_name=file_name)

    def resize_emoji(self, image_data: bytes) -> Optional[bytes]:
        im = Image.open(io.BytesIO(image_data))
        format_ = im.format
        if format_ == 'GIF' and im.is_animated:
            return None
        im = ImageOps.fit(im, self.emoji_size, Image.ANTIALIAS)
        out = io.BytesIO()
        im.save(out, format_)
        return out.getvalue()

    def upload_emoji(self, realm_id: int, image_url: str,
                     emoji_name: str) -> Optional[str]:
        file_name, dst_path_id = self.get_dst_path_id(realm_id, image_url, emoji_name)
        if image_url.startswith("/"):
            # Handle relative URLs.
            image_url = urllib.parse.urljoin(settings.EXTERNAL_HOST, image_url)
        try:
            response = requests.get(image_url, stream=True)
        except ConnectionError:
            return None
        if response.status_code != 200:
            return None
        try:
            resized_image = self.resize_emoji(response.content)
        except OSError:
            return None
        self.upload_files(response, resized_image, dst_path_id)
        return file_name


class LocalUploader(Uploader):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def mkdirs(path: str) -> None:
        dirname = os.path.dirname(path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    def write_local_file(self, path: str, file_data: bytes) -> None:
        self.mkdirs(path)
        with open(path, 'wb') as f:
            f.write(file_data)

    def upload_files(self, response: Response, resized_image: bytes,
                     dst_path_id: str) -> None:
        dst_file = os.path.join(settings.LOCAL_UPLOADS_DIR, 'avatars', dst_path_id)
        if resized_image:
            self.write_local_file(dst_file, resized_image)
        else:
            self.write_local_file(dst_file, response.content)
        self.write_local_file('.'.join((dst_file, 'original')), response.content)


class S3Uploader(Uploader):
    def __init__(self) -> None:
        super().__init__()
        conn = S3Connection(settings.S3_KEY, settings.S3_SECRET_KEY)
        bucket_name = settings.S3_AVATAR_BUCKET
        self.bucket = conn.get_bucket(bucket_name, validate=False)

    def upload_to_s3(self, path: str, file_data: bytes,
                     headers: Optional[Dict[str, str]]) -> None:
        key = Key(self.bucket)
        key.key = path
        key.set_contents_from_string(force_str(file_data), headers=headers)

    def upload_files(self, response: Response, resized_image: bytes,
                     dst_path_id: str) -> None:
        headers: Optional[Dict[str, str]] = None
        content_type = response.headers.get("Content-Type") or guess_type(dst_path_id)[0]
        if content_type:
            headers = {'Content-Type': content_type}
        if resized_image:
            self.upload_to_s3(dst_path_id, resized_image, headers)
        else:
            self.upload_to_s3(dst_path_id, response.content, headers)
        self.upload_to_s3('.'.join((dst_path_id, 'original')), response.content, headers)

def get_uploader() -> Uploader:
    if settings.LOCAL_UPLOADS_DIR is None:
        return S3Uploader()
    return LocalUploader()


def upload_emoji_to_storage(apps: StateApps, schema_editor: DatabaseSchemaEditor) -> None:
    realm_emoji_model = apps.get_model('zerver', 'RealmEmoji')
    uploader: Uploader = get_uploader()
    for emoji in realm_emoji_model.objects.all():
        file_name = uploader.upload_emoji(emoji.realm_id, emoji.img_url, emoji.name)
        if file_name is None:
            logging.warning("ERROR: Could not download emoji %s; please reupload manually" %
                            (emoji,))
        emoji.file_name = file_name
        emoji.save()


class Migration(migrations.Migration):
    dependencies = [
        ('zerver', '0076_userprofile_emojiset'),
    ]

    operations = [
        migrations.AddField(
            model_name='realmemoji',
            name='file_name',
            field=models.TextField(db_index=True, null=True),
        ),
        migrations.RunPython(upload_emoji_to_storage),
        migrations.RemoveField(
            model_name='realmemoji',
            name='img_url',
        ),
    ]