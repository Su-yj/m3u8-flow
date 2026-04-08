from tortoise import migrations
from tortoise.migrations import operations as ops
import functools
from app.interfaces.task import TaskStatus
from json import dumps, loads
from uuid import uuid4
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='GlobalConfig',
            fields=[
                ('download_dir', fields.TextField(default='downloads', description='下载目录', unique=False)),
                ('concurrency', fields.IntField(default=1, description='协程并发数')),
                ('speed_limit', fields.BigIntField(null=True, description='下载速度限制，单位：字节/秒，None 表示不限速')),
                ('chunk_size', fields.BigIntField(null=True, description='下载分块大小，单位：字节')),
                ('proxy', fields.TextField(null=True, description='代理地址', unique=False)),
                ('headers', fields.JSONField(null=True, description='请求头', encoder=functools.partial(dumps, separators=(',', ':')), decoder=loads)),
                ('merge_video', fields.BooleanField(default=True, description='是否合并视频，仅当任务完成后合并')),
                ('delete_cache', fields.BooleanField(default=True, description='是否删除缓存，仅当任务完成后删除')),
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True, description='全局配置ID')),
                ('task_concurrency', fields.IntField(default=1, description='任务并发数')),
                ('ffmpeg_path', fields.TextField(null=True, description='FFmpeg 路径', unique=False)),
            ],
            options={'table': 'global_config', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseConfig'],
        ),
        ops.CreateModel(
            name='Task',
            fields=[
                ('download_dir', fields.TextField(default='downloads', description='下载目录', unique=False)),
                ('concurrency', fields.IntField(default=1, description='协程并发数')),
                ('speed_limit', fields.BigIntField(null=True, description='下载速度限制，单位：字节/秒，None 表示不限速')),
                ('chunk_size', fields.BigIntField(null=True, description='下载分块大小，单位：字节')),
                ('proxy', fields.TextField(null=True, description='代理地址', unique=False)),
                ('headers', fields.JSONField(null=True, description='请求头', encoder=functools.partial(dumps, separators=(',', ':')), decoder=loads)),
                ('merge_video', fields.BooleanField(default=True, description='是否合并视频，仅当任务完成后合并')),
                ('delete_cache', fields.BooleanField(default=True, description='是否删除缓存，仅当任务完成后删除')),
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True, description='任务ID')),
                ('hash_id', fields.CharField(db_index=True, description='任务哈希ID', max_length=64)),
                ('name', fields.CharField(description='任务名称', max_length=255)),
                ('m3u8_url', fields.TextField(description='M3U8 URL', unique=False)),
                ('status', fields.CharEnumField(default=TaskStatus.PENDING, description='任务状态', enum_type=TaskStatus, max_length=11)),
                ('total_segments', fields.IntField(default=0, description='总片段数')),
                ('downloaded_segments', fields.IntField(default=0, description='已下载片段数')),
                ('failed_segments', fields.IntField(default=0, description='失败片段数')),
                ('total_size', fields.BigIntField(default=0, description='已下载文件大小')),
                ('total_duration', fields.FloatField(default=0, description='总时长')),
                ('speed', fields.BigIntField(default=0, description='速度，单位：字节/秒')),
                ('progress', fields.FloatField(default=0, description='进度，单位：%')),
                ('eta', fields.FloatField(null=True, description='预计剩余时间，单位：秒')),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'task', 'app': 'models', 'pk_attr': 'id'},
            bases=['BaseConfig'],
        ),
    ]
