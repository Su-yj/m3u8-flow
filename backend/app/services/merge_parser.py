import asyncio
import subprocess
from pathlib import Path
import tempfile

import m3u8

from app.interfaces.merge_parser import BaseMergeParser


class MergeParser(BaseMergeParser):
    async def merge(
        self,
        segments: list[Path],
        output_path: Path,
        playlist: m3u8.M3U8,
    ):
        if not segments:
            return
        sorted_segments = sorted(segments, key=lambda x: int(x.stem))
        file_list_content = "\n".join(
            [f"file '{segment.absolute()}'" for segment in sorted_segments]
        )
        # 兼容性：避免使用 stdin 作为 concat 列表输入（在部分 ffmpeg/平台组合下会被解析为 fd: URL，导致无法打开文件）。
        # 改为落盘临时列表文件再传给 ffmpeg。
        output_path.parent.mkdir(parents=True, exist_ok=True)
        list_file_path = Path(
            tempfile.mkstemp(prefix="m3u8-concat-", suffix=".txt")[1]
        )
        try:
            list_file_path.write_text(file_list_content, encoding="utf-8")
            cmd = [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file_path),
                "-c",
                "copy",
                str(output_path),
            ]
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode != 0:
                stderr_text = result.stderr.decode(errors="replace")
                raise RuntimeError(f"Failed to merge segments: {stderr_text}")
        finally:
            try:
                list_file_path.unlink(missing_ok=True)
            except Exception:
                pass
