import asyncio
import collections
import random
import typing as t

from .audio_source import AudioSource


class AudioQueue(asyncio.Queue[AudioSource]):
    # TODO: test the maxsize
    def _init(self, maxsize) -> None:
        # This is here for type-hints/IDE reasons
        self._queue: t.Deque[AudioSource] = collections.deque()

    def _put(self, item: AudioSource) -> None:
        if not isinstance(item, AudioSource):
            raise TypeError('AudioQueue can only hold AudioSource objects')
        self._queue.append(item)

    def clear(self) -> None:
        self._queue.clear()

    def shuffle(self) -> None:
        random.shuffle(self._queue)

    def remove(self, index: int) -> None:
        if 0 <= index < len(self._queue):
            del self._queue[index]
        else:
            raise IndexError("Index out of range")
