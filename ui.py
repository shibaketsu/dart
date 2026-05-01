# ui.py
import tkinter as tk
import math
from config import SEGMENTS


class DartboardCanvas(tk.Canvas):
    def __init__(self, master, size=400, on_hit_callback=None):
        super().__init__(
            master, width=size, height=size, bg="#222", highlightthickness=0
        )
        self.size = size
        self.cx = size / 2
        self.cy = size / 2
        self.on_hit = on_hit_callback
        self.bind("<Button-1>", self.handle_click)
        self.draw_board()

    def draw_board(self):
        self.delete("all")
        self.create_oval(0, 0, self.size, self.size, fill="#333")

        R = [
            0,
            self.size * 0.03,
            self.size * 0.075,
            self.size * 0.225,
            self.size * 0.262,
            self.size * 0.4,
            self.size * 0.437,
        ]

        angle_step = 360 / 20

        for i, num in enumerate(SEGMENTS):
            angle_center = 90 - (i * angle_step)
            start_a = angle_center - (angle_step / 2)

            is_odd = i % 2 == 0
            c_base = "black" if is_odd else "#f0f0f0"
            c_accent = "#e11d48" if is_odd else "#10b981"

            self.create_arc(
                self.cx - R[6],
                self.cy - R[6],
                self.cx + R[6],
                self.cy + R[6],
                start=start_a,
                extent=angle_step,
                fill=c_accent,
                outline="white",
            )
            self.create_arc(
                self.cx - R[5],
                self.cy - R[5],
                self.cx + R[5],
                self.cy + R[5],
                start=start_a,
                extent=angle_step,
                fill=c_base,
                outline="white",
            )
            self.create_arc(
                self.cx - R[4],
                self.cy - R[4],
                self.cx + R[4],
                self.cy + R[4],
                start=start_a,
                extent=angle_step,
                fill=c_accent,
                outline="white",
            )
            self.create_arc(
                self.cx - R[3],
                self.cy - R[3],
                self.cx + R[3],
                self.cy + R[3],
                start=start_a,
                extent=angle_step,
                fill=c_base,
                outline="white",
            )

            rad_txt = R[6] + 20
            rads = math.radians(angle_center)
            tx = self.cx + rad_txt * math.cos(rads)
            ty = self.cy - rad_txt * math.sin(rads)
            self.create_text(
                tx, ty, text=str(num), fill="white", font=("Arial", 12, "bold")
            )

        self.create_oval(
            self.cx - R[2],
            self.cy - R[2],
            self.cx + R[2],
            self.cy + R[2],
            fill="#10b981",
            outline="white",
        )
        self.create_oval(
            self.cx - R[1],
            self.cy - R[1],
            self.cx + R[1],
            self.cy + R[1],
            fill="#e11d48",
            outline="white",
        )

    def handle_click(self, event):
        if not self.on_hit:
            return

        dx = event.x - self.cx
        dy = event.y - self.cy
        dist = math.sqrt(dx * dx + dy * dy)

        R = [
            0,
            self.size * 0.03,
            self.size * 0.075,
            self.size * 0.225,
            self.size * 0.262,
            self.size * 0.4,
            self.size * 0.437,
        ]

        raw = 0
        mult = 1

        if dist <= R[1]:
            raw = 25
            mult = 2
        elif dist <= R[2]:
            raw = 25
            mult = 1
        elif dist > R[6]:
            raw = 0
            mult = 1
        else:
            angle = math.degrees(math.atan2(dy, dx))
            adj_angle = angle + 90
            if adj_angle < 0:
                adj_angle += 360

            seg_index = int(((adj_angle + 9) % 360) / 18)
            raw = SEGMENTS[seg_index]

            if R[2] < dist <= R[3]:
                mult = 1
            elif R[3] < dist <= R[4]:
                mult = 3
            elif R[4] < dist <= R[5]:
                mult = 1
            elif R[5] < dist <= R[6]:
                mult = 2

        self.on_hit(raw, mult)


class CricketScoreBoard(tk.Frame):
    """
    Cricket スコアボード
    レイアウト:  [P1マーク] | [数字] | [P2マーク]
    各行に水平区切り線を入れ、どの行のマークか一目でわかるようにする。
    """

    NUMBERS = [20, 19, 18, 17, 16, 15, "B"]
    MARK_SYMBOLS = ["", "/", "X", "X/", "X X", "X X/", "X X X"]

    # ---- 色定数 ------------------------------------------------
    BG = "#1a1a2e"  # 全体背景
    HDR_BG = "#16213e"  # ヘッダー背景
    HDR_FG = "#e0e0e0"  # ヘッダー文字
    NUM_BG = "#0f3460"  # 数字セル背景
    NUM_FG = "#f0c040"  # 数字セル文字
    MARK_BG = "#1a1a2e"  # マークセル背景
    MARK_FG = "#10b981"  # マーク文字（緑）
    CLOSED_BG = "#2a2a2a"  # クローズ済み行の背景
    CLOSED_FG = "#555555"  # クローズ済み行の文字
    DIVIDER = "#3a3a5c"  # 区切り線の色
    SCORE_FG = "#e11d48"  # スコア数字（赤）

    def __init__(self, master, player_names=("Player 1", "Player 2"), **kwargs):
        super().__init__(master, bg=self.BG, **kwargs)
        self.player_names = player_names
        self.marks = [{n: 0 for n in self.NUMBERS} for _ in range(2)]
        self.scores = [0, 0]
        self._row_frames = []  # 各数字行のフレームを保持
        self._build()

    # ------------------------------------------------------------------ #
    #  構築
    # ------------------------------------------------------------------ #
    def _build(self):
        # ヘッダー
        hdr = tk.Frame(self, bg=self.HDR_BG)
        hdr.pack(fill="x", pady=(0, 2))
        self._header_labels = []
        cols = [
            (self.player_names[0], 0, "e"),
            ("", 1, "center"),  # 数字列（空ヘッダー）
            (self.player_names[1], 2, "w"),
        ]
        hdr.columnconfigure(0, weight=1)
        hdr.columnconfigure(1, minsize=60)
        hdr.columnconfigure(2, weight=1)
        for text, col, anchor in cols:
            lbl = tk.Label(
                hdr,
                text=text,
                bg=self.HDR_BG,
                fg=self.HDR_FG,
                font=("Arial", 11, "bold"),
                padx=10,
                pady=6,
            )
            lbl.grid(row=0, column=col, sticky="nsew")
            self._header_labels.append(lbl)

        # スコア行（ヘッダー直下）
        score_frame = tk.Frame(self, bg=self.HDR_BG)
        score_frame.pack(fill="x", pady=(0, 4))
        score_frame.columnconfigure(0, weight=1)
        score_frame.columnconfigure(1, minsize=60)
        score_frame.columnconfigure(2, weight=1)
        self._score_lbl = [None, None]
        for i, side in enumerate([0, 2]):
            lbl = tk.Label(
                score_frame,
                text="0",
                bg=self.HDR_BG,
                fg=self.SCORE_FG,
                font=("Arial", 16, "bold"),
                padx=10,
                pady=2,
            )
            lbl.grid(row=0, column=side, sticky="nsew")
            self._score_lbl[i] = lbl
        tk.Label(
            score_frame,
            text="PTS",
            bg=self.HDR_BG,
            fg=self.HDR_FG,
            font=("Arial", 8),
        ).grid(row=0, column=1)

        # 区切り線
        tk.Frame(self, bg=self.DIVIDER, height=2).pack(fill="x")

        # 数字ごとの行
        self._mark_lbl = [{}, {}]  # player -> {number -> Label}
        self._row_frame = {}  # number -> Frame（背景色変更用）

        for idx, num in enumerate(self.NUMBERS):
            row_bg = self.BG

            outer = tk.Frame(self, bg=row_bg)
            outer.pack(fill="x")
            outer.columnconfigure(0, weight=1)
            outer.columnconfigure(1, minsize=60)
            outer.columnconfigure(2, weight=1)
            self._row_frame[num] = outer

            # P1 マーク（右寄せ）
            m0 = tk.Label(
                outer,
                text="",
                bg=row_bg,
                fg=self.MARK_FG,
                font=("Arial", 13, "bold"),
                anchor="e",
                padx=14,
                pady=5,
            )
            m0.grid(row=0, column=0, sticky="nsew")
            self._mark_lbl[0][num] = m0

            # 数字（中央）
            nl = tk.Label(
                outer,
                text=str(num),
                bg=self.NUM_BG,
                fg=self.NUM_FG,
                font=("Arial", 14, "bold"),
                width=4,
                pady=5,
            )
            nl.grid(row=0, column=1, sticky="nsew", padx=4, pady=2)

            # P2 マーク（左寄せ）
            m1 = tk.Label(
                outer,
                text="",
                bg=row_bg,
                fg=self.MARK_FG,
                font=("Arial", 13, "bold"),
                anchor="w",
                padx=14,
                pady=5,
            )
            m1.grid(row=0, column=2, sticky="nsew")
            self._mark_lbl[1][num] = m1

            # 行の下に区切り線
            tk.Frame(self, bg=self.DIVIDER, height=1).pack(fill="x")

    # ------------------------------------------------------------------ #
    #  公開 API
    # ------------------------------------------------------------------ #
    def add_mark(self, player: int, number, count: int = 1):
        """プレイヤー(0 or 1)の指定数字にマークを追加する。"""
        if number not in self.NUMBERS:
            return
        self.marks[player][number] = min(self.marks[player][number] + count, 6)
        self._refresh_row(number)

    def add_score(self, player: int, points: int):
        """プレイヤーのスコアを加算する。"""
        self.scores[player] += points
        self._score_lbl[player].config(text=str(self.scores[player]))

    def reset(self):
        """全状態をリセットする。"""
        for p in range(2):
            for n in self.NUMBERS:
                self.marks[p][n] = 0
            self.scores[p] = 0
            self._score_lbl[p].config(text="0")
        for n in self.NUMBERS:
            self._refresh_row(n)

    # ------------------------------------------------------------------ #
    #  内部
    # ------------------------------------------------------------------ #
    def _refresh_row(self, number):
        both_closed = all(self.marks[p][number] >= 3 for p in range(2))
        row_bg = self.CLOSED_BG if both_closed else self.BG

        outer = self._row_frame[number]
        outer.config(bg=row_bg)

        for p in range(2):
            cnt = self.marks[p][number]
            sym = self.MARK_SYMBOLS[min(cnt, 6)]
            fg = self.CLOSED_FG if both_closed else self.MARK_FG
            lbl = self._mark_lbl[p][number]
            lbl.config(text=sym, bg=row_bg, fg=fg)
