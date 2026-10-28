# main.py
import tkinter as tk
from tkinter import Toplevel, Entry, messagebox
import platform
import os
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, ImageTk
from members import MemberStore
from member_ui import MemberWindow
from awards import AwardPlayer, VIDEO_NAMES

try:
    from tkmacosx import Button as MacButton
except ImportError:
    MacButton = None

from models import DartsGame
from ui import DartboardCanvas, ScrollableFrame
from config import DOUBLE_OUT_TABLE


class DartsApp(tk.Tk):
    def __init__(self, data_directory=None):
        super().__init__()
        self.title("Python Darts Master")
        self.geometry("1080x800")
        self.minsize(940, 720)
        self.configure(bg="#1e293b")

        self.game = DartsGame()
        directory = data_directory or os.environ.get('DARTS_DATA_DIR') or Path(__file__).resolve().parent / 'data'
        self.member_store = MemberStore(directory)
        self.roster = [None, None]
        self.match_id = uuid.uuid4().hex
        self._saved_result = False
        self.member_window = None
        self.award_player = None
        self.awards_enabled = tk.BooleanVar(value=True)
        self._avatar_key = None
        self.protocol('WM_DELETE_WINDOW', self.close_app)

        # デフォルトのプレイヤー名リストを保持
        self.custom_names = ["PLAYER 1", "PLAYER 2", "PLAYER 3", "PLAYER 4"]

        self._init_ui()
        self.reset_game("COUNTUP")

    def create_button(self, parent, text, command, width=8, accent=False):
        bg = "#0e7490" if accent else "#334155"
        options = dict(text=text, command=command, font=("Arial", 10, "bold"))
        if platform.system() == "Darwin" and MacButton:
            return MacButton(parent, **options, bg=bg, fg="white",
                             width=width * 10, height=32, borderless=1,
                             focuscolor="#38bdf8")
        if platform.system() == "Darwin":
            return tk.Button(parent, **options, width=width,
                             highlightbackground=bg)
        return tk.Button(parent, **options, width=width, bg=bg, fg="white",
                         activebackground="#0e7490", activeforeground="white",
                         relief="flat", bd=0, pady=7, cursor="hand2")

    def _init_ui(self):
        self._score_key = None
        header = tk.Frame(self, bg="#0f172a", padx=20, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="DARTS MASTER", bg="#0f172a", fg="white",
                 font=("Helvetica", 19, "bold")).pack(side="left")
        self.mode_label = tk.Label(header, bg="#0f172a", fg="#67e8f9",
                                   font=("Arial", 11, "bold"))
        self.mode_label.pack(side="right")
        tk.Checkbutton(header, text="アワード動画", variable=self.awards_enabled,
                       bg="#0f172a", fg="#cbd5e1", selectcolor="#334155",
                       activebackground="#0f172a", activeforeground="white",
                       highlightthickness=0).pack(side="right", padx=16)

        modes = tk.Frame(self, bg="#0f172a", padx=18, pady=6)
        modes.pack(fill="x")
        self.mode_buttons = {}
        for label, mode in [("COUNTUP", "COUNTUP"), ("301", "301"),
                            ("501", "501"), ("CRICKET", "CRICKET"),
                            ("INVERSE", "CRICKET INVERSE"),
                            ("ALL CRICKET", "ALL CRICKET"),
                            ("HIDDEN", "HIDDEN CRICKET")]:
            btn = self.create_button(modes, label,
                                     lambda m=mode: self.select_mode(m), width=11)
            btn.pack(side="left", padx=2, pady=(0, 6))
            self.mode_buttons[mode] = (btn, label)

        config = tk.Frame(self, bg="#1e293b", padx=20, pady=12)
        config.pack(fill="x")
        self.p_count_var = tk.IntVar(value=2)
        self.round_var = tk.IntVar(value=8)
        self.stepper_buttons = []
        for title, variable, command in [
            ("Players", self.p_count_var, self.change_players),
            ("Rounds", self.round_var, self.change_rounds),
        ]:
            group = tk.Frame(config, bg="#1e293b")
            group.pack(side="left", padx=(0, 18))
            tk.Label(group, text=title, bg="#1e293b", fg="#cbd5e1").pack(
                side="left", padx=(0, 8))
            minus = self.create_button(group, "−", lambda c=command: c(-1), width=3)
            minus.pack(side="left")
            tk.Label(group, textvariable=variable, bg="#1e293b", fg="white",
                     width=3, font=("Arial", 11, "bold")).pack(side="left")
            plus = self.create_button(group, "+", lambda c=command: c(1), width=3)
            plus.pack(side="left")
            self.stepper_buttons.append((minus, plus))
        self.create_button(config, "MEMBERS", self.open_members).pack(side="left")
        self.create_button(config, "NAMES", self.open_name_editor, width=7).pack(side="left", padx=4)
        self.create_button(config, "NEW GAME", lambda: self.reset_game(self.game.mode),
                           width=11, accent=True).pack(side="right")

        self.hidden_bonus_var = tk.IntVar(value=1)
        self.hidden_bonus_var.trace_add("write", self.on_hidden_bonus_change)
        self.hidden_bonus_frame = tk.Frame(config, bg="#1e293b")
        tk.Label(self.hidden_bonus_frame, text="Hidden Bonus:", bg="#1e293b",
                 fg="#cbd5e1").pack(side="left", padx=(14, 4))
        for bonus in [1, 2]:
            tk.Radiobutton(self.hidden_bonus_frame, text=str(bonus),
                           variable=self.hidden_bonus_var, value=bonus,
                           bg="#1e293b", fg="white", selectcolor="#334155",
                           activebackground="#1e293b", activeforeground="white",
                           highlightthickness=0).pack(side="left")

        main = tk.Frame(self, bg="#1e293b")
        main.pack(expand=True, fill="both", padx=20, pady=(0, 16))
        main.columnconfigure(0, weight=1, minsize=360)
        main.columnconfigure(1, weight=2, minsize=500)
        main.rowconfigure(0, weight=1)
        left = tk.Frame(main, bg="#0f172a", padx=12, pady=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        active_header = tk.Frame(left, bg="#0f172a")
        active_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.avatar_label = tk.Label(active_header, bg="#0f172a")
        self.avatar_label.pack(side="left", padx=(0, 8))
        self.info_lbl = tk.Label(active_header, bg="#0f172a", fg="#67e8f9",
                                 font=("Arial", 14, "bold"), height=2,
                                 wraplength=310)
        self.info_lbl.pack(side="left", expand=True, fill="x")
        self.board = DartboardCanvas(left, size=340, on_hit_callback=self.on_board_hit)
        self.board.grid(row=1, column=0, sticky="nsew")
        tk.Label(left, text="Click the board to record a throw", bg="#0f172a",
                 fg="#94a3b8", font=("Arial", 10)).grid(row=2, column=0, pady=6)
        throws = tk.Frame(left, bg="#0f172a")
        throws.grid(row=3, column=0, pady=6, sticky="ew")
        self.throw_labels = []
        for i in range(3):
            throws.columnconfigure(i, weight=1, uniform="throws")
            lbl = tk.Label(throws, text=str(i + 1), height=2, bg="#334155",
                           fg="#cbd5e1", font=("Arial", 11, "bold"))
            lbl.grid(row=0, column=i, sticky="ew", padx=3)
            self.throw_labels.append(lbl)
        actions = tk.Frame(left, bg="#0f172a")
        actions.grid(row=4, column=0, pady=8)
        self.miss_button = self.create_button(actions, "MISS",
                                              lambda: self.on_board_hit(0, 1))
        self.undo_button = self.create_button(actions, "UNDO", self.do_undo)
        self.skip_button = self.create_button(actions, "SKIP", self.do_skip)
        for btn in (self.miss_button, self.undo_button, self.skip_button):
            btn.pack(side="left", padx=3)
        self.suggest_lbl = tk.Label(left, bg="#0f172a", fg="#38bdf8",
                                    font=("Arial", 10), wraplength=310)
        self.suggest_lbl.grid(row=5, column=0, pady=4)
        self.status_msg = ""
        self.status_lbl = tk.Label(left, bg="#0f172a", fg="#fbbf24",
                                   font=("Arial", 11, "bold"), wraplength=310)
        self.status_lbl.grid(row=6, column=0, pady=4)

        right = tk.Frame(main, bg="#1e293b")
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="SCOREBOARD", bg="#1e293b", fg="#cbd5e1",
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        self.score_view = ScrollableFrame(right)
        self.score_view.pack(fill="both", expand=True)
        self.score_view.canvas.bind("<Configure>", self._fit_all_cricket, add="+")
        self.score_container = tk.Frame(self.score_view.content, bg="#1e293b")
        self.score_container.pack(fill="both", expand=True)

    def on_hidden_bonus_change(self, *args):
        if self.game.mode == "HIDDEN CRICKET":
            self.game.hidden_cricket_bonus = self.hidden_bonus_var.get()

    def update_hidden_bonus_visibility(self):
        if self.game.mode == "HIDDEN CRICKET":
            self.hidden_bonus_frame.pack(side="left")
        else:
            self.hidden_bonus_frame.pack_forget()

    def change_players(self, delta):
        previous = self.p_count_var.get()
        new_val = max(1, min(4, previous + delta))
        if new_val == previous:
            return
        self.p_count_var.set(new_val)
        if not self.reset_game(self.game.mode):
            self.p_count_var.set(previous)

    def change_rounds(self, delta):
        previous = self.round_var.get()
        new_val = max(1, min(30, previous + delta))
        if new_val == previous:
            return
        self.round_var.set(new_val)
        if not self.reset_game(self.game.mode):
            self.round_var.set(previous)

    def select_mode(self, mode):
        previous = self.round_var.get()
        if mode == "COUNTUP":
            self.round_var.set(8)
        else:
            self.round_var.set(15)
        if not self.reset_game(mode):
            self.round_var.set(previous)

    def reset_game(self, mode):
        if not self.persist_result():
            return False
        self.dismiss_award()
        count = self.p_count_var.get()
        self.roster = (self.roster + [None]*count)[:count]
        names = []
        for i, member_id in enumerate(self.roster):
            member = self.member_store.get(member_id) if member_id else None
            names.append(member['name'] if member else self.custom_names[i])
        self.match_id = uuid.uuid4().hex
        self._saved_result = False
        self.game.setup_game(
            mode,
            self.p_count_var.get(),
            self.round_var.get(),
            player_names=names,
            hidden_cricket_bonus=self.hidden_bonus_var.get(),
        )
        self.update_hidden_bonus_visibility()
        self.status_msg = ""
        self.score_view.canvas.yview_moveto(0)
        self.update_ui()
        return True

    def open_name_editor(self):
        # 名前編集用ポップアップ
        editor = Toplevel(self)
        editor.title("Edit Player Names")
        editor.geometry(f"380x{120 + 48 * self.p_count_var.get()}")
        editor.resizable(False, False)
        editor.transient(self)
        editor.grab_set()
        editor.bind("<Escape>", lambda event: editor.destroy())
        editor.configure(bg="#1e293b")

        entries = []
        player_count = self.p_count_var.get()

        # 入力フィールドの生成
        for i in range(player_count):
            row = tk.Frame(editor, bg="#1e293b", pady=5)
            row.pack(fill="x", padx=10)

            tk.Label(
                row, text=f"Player {i+1}:", fg="white", bg="#1e293b", width=10
            ).pack(side="left")

            # 現在の名前をデフォルト値に
            current_name = (
                self.custom_names[i] if i < len(self.custom_names) else f"PLAYER {i+1}"
            )

            ent = Entry(row)
            registered = self.roster[i] if i < len(self.roster) else None
            ent.insert(0, self.game.players[i].name if registered else current_name)
            if registered:
                ent.configure(state="disabled")
            ent.pack(side="right", expand=True, fill="x")
            entries.append(ent)

        def save_names():
            # 新しい名前を保存
            for i, ent in enumerate(entries):
                if i < len(self.roster) and self.roster[i]:
                    continue
                new_name = ent.get().strip()
                if new_name:
                    if i < len(self.custom_names):
                        self.custom_names[i] = new_name
                    else:
                        # 配列が足りない場合の安全策
                        while len(self.custom_names) <= i:
                            self.custom_names.append("")
                        self.custom_names[i] = new_name

            # 現在のゲームのプレイヤー名も即座に更新
            for i in range(len(self.game.players)):
                if i < len(self.custom_names) and not self.roster[i]:
                    self.game.players[i].name = self.custom_names[i]

            self.update_ui()
            editor.destroy()

        self.create_button(editor, "SAVE", save_names, accent=True).pack(pady=20)
        editor.bind("<Return>", lambda event: save_names())
        entries[0].focus_set()
        entries[0].selection_range(0, tk.END)

    def open_members(self):
        if self.member_window and self.member_window.winfo_exists():
            self.member_window.lift()
            return
        self.dismiss_award()
        self.member_window = MemberWindow(self)

    def start_roster(self, roster):
        if not 1 <= len(roster) <= 4 or not self.persist_result():
            return False
        self.roster = list(roster)
        self.p_count_var.set(len(roster))
        return self.reset_game(self.game.mode)

    def refresh_member_names(self):
        for i, member_id in enumerate(self.roster):
            member = self.member_store.get(member_id) if member_id else None
            if member and i < len(self.game.players):
                self.game.players[i].name = member['name']
                for state in self.game.history:
                    state['players'][i].name = member['name']
                    if state['winner'] and state['winner'].id == i + 1:
                        state['winner'].name = member['name']
                if self.game.winner and self.game.winner.id == i + 1:
                    self.game.winner.name = member['name']
        self.update_ui()

    def refresh_avatar(self):
        index = self.game.current_player_idx
        mid = self.roster[index] if index < len(self.roster) else None
        member = self.member_store.get(mid) if mid else None
        path = self.member_store.photo_path(member)
        key = (mid, str(path), self.game.players[index].name, index)
        if key == self._avatar_key:
            return
        image = Image.new('RGB', (40, 40), '#334155')
        if path:
            try:
                with Image.open(path) as source:
                    image = ImageOps.fit(source.convert('RGB'), (40, 40), Image.Resampling.LANCZOS)
            except (OSError, ValueError):
                path = None
        if not path:
            draw = ImageDraw.Draw(image)
            draw.text((20, 20), f'P{index+1}', fill='white', anchor='mm')
        self._avatar = ImageTk.PhotoImage(image, master=self)
        self.avatar_label.configure(image=self._avatar)
        self._avatar_key = key

    def persist_result(self):
        try:
            if self.game.winner and not self._saved_result and any(self.roster):
                self.member_store.record_match(self.match_id, self.game, self.roster)
                self._saved_result = True
            elif not self.game.winner and self._saved_result:
                self.member_store.remove_match(self.match_id)
                self._saved_result = False
            return True
        except Exception as error:
            messagebox.showerror('成績を保存できません', str(error), parent=self)
            return False

    def present_award(self, award, player_name, details=()):
        if not self.awards_enabled.get():
            return
        self.dismiss_award()
        self.award_player = AwardPlayer(self, award, player_name,
                                        on_close=lambda: setattr(self, 'award_player', None), details=details)
        if self.award_player.error:
            self.status_msg = '動画を読み込めないため、タイトル演出を表示しています。'
            self.status_lbl.configure(text=self.status_msg)

    def dismiss_award(self):
        if self.award_player:
            self.award_player.close()
            self.award_player = None

    def on_board_hit(self, raw, mult):
        if self.game.winner or self.award_player:
            return
        player_name = self.game.players[self.game.current_player_idx].name
        award = self.game.handle_hit(raw, mult)
        self.status_msg = ' / '.join(self.game.last_awards) or award or ''
        self.update_ui()
        if award in VIDEO_NAMES:
            self.present_award(award, player_name, self.game.last_awards[1:])
        elif self.game.winner:
            self.present_award('WINNER', self.game.winner.name)

    def do_undo(self):
        self.dismiss_award()
        if self.game.undo():
            self.status_msg = ''
            self.update_ui()

    def do_skip(self):
        if self.game.winner or self.award_player:
            return
        player_name = self.game.players[self.game.current_player_idx].name
        award = self.game.skip_turn()
        self.status_msg = ' / '.join(self.game.last_awards)
        self.update_ui()
        if award in VIDEO_NAMES:
            self.present_award(award, player_name, self.game.last_awards[1:])
        elif self.game.winner:
            self.present_award('WINNER', self.game.winner.name)

    def close_app(self):
        if not self.persist_result():
            return
        self.dismiss_award()
        if self.member_window:
            self.member_window.close()
        self.member_store.close()
        self.destroy()

    def update_ui(self):
        game = self.game
        if self.hidden_bonus_var.get() != game.hidden_cricket_bonus:
            self.hidden_bonus_var.set(game.hidden_cricket_bonus)
        curr_p = game.players[game.current_player_idx]
        self.info_lbl.config(text=f"ROUND {game.round} / {game.max_rounds}\n{curr_p.name}")
        self.refresh_avatar()
        self.mode_label.config(text=game.mode)
        for mode, (button, label) in self.mode_buttons.items():
            # Text also identifies the selection on native macOS buttons.
            button.config(text=("● " if mode == game.mode else "") + label)
        for (minus, plus), value, maximum in zip(
            self.stepper_buttons, (len(game.players), game.max_rounds), (4, 30)
        ):
            minus.config(state="disabled" if value == 1 else "normal")
            plus.config(state="disabled" if value == maximum else "normal")
        self.miss_button.config(state="disabled" if game.winner else "normal")
        self.skip_button.config(state="disabled" if game.winner else "normal")
        self.undo_button.config(state="normal" if len(game.history) > 1 else "disabled")
        for i, lbl in enumerate(self.throw_labels):
            if i < len(game.current_throws):
                lbl.config(text=game.current_throws[i].display, bg="#0e7490", fg="white")
            else:
                lbl.config(text=f"{i + 1}", bg="#334155", fg="#cbd5e1")

        key = (game.mode, len(game.players), tuple(game.active_targets))
        if key != self._score_key:
            self.score_container.destroy()
            self._score_key = key
            self.score_container = tk.Frame(self.score_view.content, bg="#1e293b")
            self.score_container.pack(fill="both", expand=True)
            self.score_container.bind("<Configure>", self._fit_all_cricket)
            if "CRICKET" in game.mode:
                self.draw_cricket_board()
            else:
                self.draw_score_board()
        self.refresh_scores()
        self.score_view.set_fit_height(game.mode == "ALL CRICKET")
        self._fit_all_cricket()
        self.update_board_colors()
        self.update_suggestion(curr_p)
        self.status_lbl.config(text=(f"{game.winner.name} WINS!" if game.winner
                                     else self.status_msg))
        self.persist_result()

    def draw_score_board(self):
        self._player_widgets = []
        self._target_widgets = {}
        cols = min(2, len(self.game.players))
        for i, player in enumerate(self.game.players):
            frame = tk.Frame(self.score_container, bg="#0f172a", padx=12, pady=8,
                             highlightthickness=2)
            frame.grid(row=i // cols, column=i % cols, sticky="nsew", padx=4, pady=4)
            name = tk.Label(frame, font=("Arial", 11, "bold"), wraplength=185)
            name.pack(fill="x")
            score = tk.Label(frame, font=("Arial", 32, "bold"))
            score.pack(pady=4)
            caption = tk.Label(frame, text="POINTS" if self.game.mode == "COUNTUP"
                               else "REMAINING", font=("Arial", 9))
            caption.pack()
            self._player_widgets.append((frame, name, score, caption))
        for col in range(cols):
            self.score_container.columnconfigure(col, weight=1, uniform="players")

    def draw_cricket_board(self):
        self._player_widgets = []
        self._target_widgets = {}
        duel = len(self.game.players) == 2
        target_col = 1 if duel else 0
        self.score_container.columnconfigure(target_col, minsize=64)
        compact = len(self.game.active_targets) > 14
        for i, player in enumerate(self.game.players):
            col = (0 if i == 0 else 2) if duel else i + 1
            self.score_container.columnconfigure(col, weight=1, uniform="players")
            frame = tk.Frame(self.score_container, padx=4, pady=3, highlightthickness=1)
            frame.grid(row=0, column=col, sticky="nsew", padx=2, pady=(0, 4))
            name = tk.Label(frame, font=("Arial", 10, "bold"), wraplength=92)
            name.pack(fill="x")
            score = tk.Label(frame, font=("Arial", 18, "bold"))
            score.pack(side="left", padx=(4, 3))
            caption = tk.Label(frame, text="POINTS", font=("Arial", 8))
            caption.pack(side="left")
            self._player_widgets.append((frame, name, score, caption))
        for row, target in enumerate(self.game.active_targets, 1):
            bg = "#0f172a" if row % 2 else "#182337"
            label = tk.Label(self.score_container, bg="#334155",
                             font=("Arial", 10 if compact else 12, "bold"),
                             pady=0 if compact else 3, borderwidth=0)
            label.grid(row=row, column=target_col, sticky="nsew", padx=2, pady=1)
            marks = []
            for i in range(len(self.game.players)):
                col = (0 if i == 0 else 2) if duel else i + 1
                mark = tk.Label(self.score_container, bg=bg,
                                font=("Arial", 11 if compact else 14, "bold"),
                                pady=0, borderwidth=0)
                mark.grid(row=row, column=col, sticky="nsew", padx=2, pady=1)
                marks.append(mark)
            self._target_widgets[target] = (label, marks)
            if self.game.mode == "ALL CRICKET":
                self.score_container.rowconfigure(row, weight=1, uniform="targets")

    def _fit_all_cricket(self, event=None):
        if self.game.mode != "ALL CRICKET" or not self._target_widgets:
            return
        header_height = max(w[0].winfo_reqheight() for w in self._player_widgets) + 4
        available = self.score_view.canvas.winfo_height() - header_height
        row_height = max(1, available / len(self._target_widgets))
        # Pixel sizes track the actual viewport independently of display DPI.
        number_size = max(10, int(row_height * 0.62))
        mark_size = max(11, int(row_height * 0.70))
        for label, marks in self._target_widgets.values():
            label.configure(font=("Arial", -number_size, "bold"))
            for mark in marks:
                mark.configure(font=("Arial", -mark_size, "bold"))

    def refresh_scores(self):
        for i, (frame, name, score, caption) in enumerate(self._player_widgets):
            player = self.game.players[i]
            active = i == self.game.current_player_idx and not self.game.winner
            bg = "#243b53" if active else "#0f172a"
            frame.config(bg=bg, highlightbackground="#38bdf8" if active else bg)
            name.config(text=("▶ " if active else "") + player.name,
                        bg=bg, fg="#e2e8f0")
            score.config(text=str(player.score), bg=bg,
                         fg="#67e8f9" if active else "white")
            caption.config(bg=bg, fg="#94a3b8")
        for target, (label, marks) in self._target_widgets.items():
            revealed = (self.game.mode != "HIDDEN CRICKET"
                        or target in self.game.revealed_targets)
            closed = all(p.marks.get(target, 0) >= 3 for p in self.game.players)
            label.config(text=("BULL" if target == 25 else str(target)) if revealed else "?",
                         bg="#334155", fg="#94a3b8" if not revealed or closed else "#fbbf24")
            for i, mark in enumerate(marks):
                count = min(self.game.players[i].marks.get(target, 0), 3) if revealed else 0
                mark.config(text=("·", "/", "X", "⊗")[count],
                            fg="#64748b" if closed or not count
                            else "#fb7185" if count == 3 else "#34d399")

    def update_board_colors(self):
        game = self.game
        if "CRICKET" not in game.mode:
            self.board.set_target_states(None)
            return
        current = game.players[game.current_player_idx]
        states = {}
        for target in list(range(1, 21)) + [25]:
            # Keep every undiscovered number alike in Hidden Cricket so the
            # illustration cannot disclose the randomly selected targets.
            if game.mode == "HIDDEN CRICKET" and target in game.hidden_missed_targets:
                states[target] = "closed"
            elif game.mode == "HIDDEN CRICKET" and target not in game.revealed_targets:
                states[target] = "open"
            elif target not in game.active_targets or all(
                p.marks.get(target, 0) >= 3 for p in game.players
            ):
                states[target] = "closed"
            elif current.marks.get(target, 0) >= 3:
                states[target] = "scoring"
            else:
                states[target] = "open"
        self.board.set_target_states(states)

    def update_suggestion(self, player):
        txt = ""
        if self.game.mode in ["301", "501"] and player.score <= 170:
            guide = DOUBLE_OUT_TABLE.get(player.score)
            if guide and len(guide) <= (3 - len(self.game.current_throws)):
                txt = f"Checkout: {' > '.join(guide)}"
        self.suggest_lbl.config(text=txt)


if __name__ == "__main__":
    app = DartsApp()
    app.mainloop()
