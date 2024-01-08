import asyncio
import collections
import random
import typing as t
from discord.ext import commands
from .audio_source import AudioSource


class AudioQueue(asyncio.Queue[AudioSource]):
    # TODO: test the maxsize
    def _init(self, maxsize) -> None:
        self._queue: t.Deque[AudioSource] = collections.deque()

    def _put(self, item: AudioSource | tuple[commands.Context, str]) -> None:
        if isinstance(item, AudioSource):
            self._queue.append(item)
            return
        if isinstance(item, tuple[commands.Context, str]):
            source = AudioSource.create_source(item[0], item[1])
            self._queue.append(source)
        raise TypeError(f'Cannot store type {type(item)} in this queue')

    def clear(self) -> None:
        self._queue.clear()

    def shuffle(self) -> None:
        random.shuffle(self._queue)

    def remove(self, index: int) -> None:
        if 0 <= index < len(self._queue):
            del self._queue[index]
        else:
            raise IndexError("Index out of range")
