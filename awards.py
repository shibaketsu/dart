"""Embedded, nonblocking video celebration with deterministic cleanup."""
import time
import tkinter as tk
from pathlib import Path

import av
from PIL import Image, ImageTk

from award_catalog import VIDEO_NAMES
VIDEO_DIRECTORY = Path(__file__).resolve().parent / 'media' / 'awards'


class AwardPlayer(tk.Toplevel):
    def __init__(self, master, award, player_name, on_close=None, details=()):
        super().__init__(master)
        self.withdraw()
        self.container = None
        self._job = None
        self._closed = False
        self._on_close = on_close
        self.award = award
        self.title(award)
        self.configure(bg='#050914')
        self.transient(master)
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.bind('<Escape>', lambda event: self.close())
        self.bind('<space>', lambda event: self.close())
        width = min(960, max(480, master.winfo_width()-80), self.winfo_screenwidth()-80)
        self.video_size = (width, round(width*9/16))
        x = master.winfo_rootx() + (master.winfo_width()-width)//2
        y = master.winfo_rooty() + max(0, (master.winfo_height()-self.video_size[1]-70)//2)
        self.geometry(f'+{max(0,x)}+{max(0,y)}')
        heading = f'{player_name}  /  {award}'
        if details:
            heading += '  ·  ' + ' / '.join(details)
        tk.Label(self, text=heading, wraplength=width-24, bg='#050914', fg='#fde68a',
                 font=('Arial', 14, 'bold'), pady=10).pack()
        self.screen = tk.Label(self, bg='#050914', bd=0)
        self.screen.pack()
        tk.Button(self, text='SKIP  ·  Esc / Space', command=self.close).pack(pady=8)
        self.error = None
        try:
            path = VIDEO_DIRECTORY / f'{VIDEO_NAMES[award]}.mp4'
            self.container = av.open(str(path))
            self.frames = self.container.decode(video=0)
            self.fps = float(self.container.streams.video[0].average_rate or 24)
            self.started = time.monotonic()
            self.index = 0
            self._tick()
        except (OSError, ValueError, KeyError, av.error.FFmpegError) as error:
            self._fallback(error)
        self.deiconify()
        self.grab_set()
        self.focus_set()

    def _tick(self):
        self._job = None
        if self._closed:
            return
        try:
            # Keep the movie on its timeline when native Tk image drawing is
            # slower than the video frame rate. Decode overdue frames without
            # converting or displaying them rather than slowing the movie.
            due_index = int((time.monotonic()-self.started)*self.fps)
            while self.index < due_index:
                next(self.frames)
                self.index += 1
            frame = next(self.frames)
            image = frame.to_image().resize(self.video_size, Image.Resampling.LANCZOS)
            self._photo = ImageTk.PhotoImage(image, master=self)
            self.screen.configure(image=self._photo)
            self.index += 1
            delay = max(8, round((self.started+self.index/self.fps-time.monotonic())*1000))
            self._job = self.after(delay, self._tick)
        except StopIteration:
            if self.index:
                self.close()
            else:
                self._fallback(ValueError('動画にフレームがありません。'))
        except (OSError, ValueError, av.error.FFmpegError) as error:
            self._fallback(error)

    def _fallback(self, error):
        self.error = str(error)
        if self.container:
            self.container.close()
            self.container = None
        self.screen.configure(image='', text=self.award, fg='#fde68a',
                              font=('Arial', 44, 'bold'), width=20, height=4)
        self._job = self.after(2500, self.close)

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self._job:
            self.after_cancel(self._job)
        if self.container:
            self.container.close()
        self.grab_release()
        self.destroy()
        if self._on_close:
            self._on_close()
