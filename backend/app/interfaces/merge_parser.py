from abc import ABC, abstractmethod
from pathlib import Path

import m3u8


class BaseMergeParser(ABC):
    @abstractmethod
    async def merge(
        self,
        segments: list[Path],
        output_path: Path,
        playlist: m3u8.M3U8,
    ):
        """
        合并视频片段

        :param segments: 视频片段列表
        :type segments: list[Path]
        :param output_path: 输出路径
        :type output_path: Path
        :param playlist: M3U8 播放列表
        :type playlist: m3u8.M3U8
        """
        raise NotImplementedError
