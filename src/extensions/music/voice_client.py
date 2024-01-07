import asyncio
import typing as t

import discord
from async_timeout import timeout

import custom_errors as ce

from .audio_queue import AudioQueue
from .audio_source import AudioSource


class CustomVoiceClient(discord.VoiceClient):
    def __init__(self, client, channel,
            timeout: int = 180,
            on_play_callback: t.Callable[[t.Any, t.Any], t.Awaitable[t.Any]] = None,
            on_play_callback_kwargs: dict = None
    ) -> None:
        super().__init__(client, channel)
        
        self.timeout = timeout
        if on_play_callback is None:
            on_play_callback = self._default_on_play_callback
        if on_play_callback_kwargs is None:
            on_play_callback_kwargs = {}
        self.on_play_callback = on_play_callback
        self.on_play_kwargs = on_play_callback_kwargs
        
        self.queue = AudioQueue(20)
        self.next_event = asyncio.Event()
        self.looping = False
        self.current_audio: AudioSource = None

        
        self.audio_player_task = self.client.loop.create_task(self.audio_player())

    async def audio_player(self):
        while True:
            self.next_event.clear()
            if not self.looping:
                # Try to get the next song within 3 minutes.
                # If no song is added to the queue in time, the player will disconnect due to performance reasons.
                try:
                    async with timeout(self.timeout):
                        self.current_audio = await self.queue.get()
                except asyncio.TimeoutError:
                    self.client.loop.create_task(self.disconnect())
                    return

            # TODO: check and understand this volume part
            # self.current_audio.volume = self.volume
            self.play(self.current_audio, after=self.play_next)
            await self.on_play_callback(**self.on_play_kwargs)
            await self.next_event.wait()

    def play_next(self, error=None):
        if error:
            raise ce.VoiceError(str(error))
        self.next_event.set()

    def skip(self):
        if self.is_playing():
            # Stopping the current audio will trigger the play_next method and start the next song if any available on the queue
            self.stop()

    async def disconnect(self, *, force: bool = False) -> None:
        # TODO: check what happens if the queue if not cleared before disconnecting
        self.queue.clear()
        return await super().disconnect(force=force)

    async def _default_on_play_callback(self, **kwargs):
        # TODO add args too (not only kwargs)
        return

    def __del__(self):
        self.audio_player_task.cancel()
