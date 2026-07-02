# main.py
import tkinter as tk
from tkinter import messagebox, Toplevel, Entry, Label, Button
import platform

try:
    from tkmacosx import Button as MacButton
except ImportError:
    MacButton = None

from models import DartsGame
from ui import DartboardCanvas
from config import DOUBLE_OUT_TABLE


class DartsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Darts Master")
        self.geometry("1024x768")
        self.configure(bg="#1e293b")

        self.game = DartsGame()

        # デフォルトのプレイヤー名リストを保持
        self.custom_names = ["PLAYER 1", "PLAYER 2", "PLAYER 3", "PLAYER 4"]

        self._init_ui()
        self.reset_game("COUNTUP")

    def _init_ui(self):
        is_mac = platform.system() == "Darwin"

        def create_btn(parent, text, cmd, bg_col, fg_col, width=8):
            if is_mac and MacButton:
                return MacButton(
                    parent,
                    text=text,
                    command=cmd,
                    bg=bg_col,
                    fg=fg_col,
                    font=("Arial", 10, "bold"),
                    width=width * 10,
                    borderless=1,
                    focuscolor="",
                )
            elif is_mac:
                return tk.Button(
                    parent,
                    text=text,
                    command=cmd,
                    font=("Arial", 10, "bold"),
                    highlightbackground=bg_col,
                )
            else:
                return tk.Button(
                    parent,
                    text=text,
                    command=cmd,
                    bg=bg_col,
                    fg=fg_col,
                    font=("Arial", 10, "bold"),
                    width=width,
                )

        # -- Header --
        header_frame = tk.Frame(self, bg="#0f172a", pady=10)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="DARTS MASTER",
            bg="#0f172a",
            fg="white",
            font=("Helvetica", 16, "bold"),
        )
        title_lbl.pack(side="left", padx=20)

        # Mode Buttons
        modes_frame = tk.Frame(header_frame, bg="#0f172a")
        modes_frame.pack(side="right", padx=20)

        row1 = tk.Frame(modes_frame, bg="#0f172a")
        row1.pack(anchor="e")
        for m in ["COUNTUP", "301", "501", "CRICKET"]:
            btn = create_btn(
                row1,
                text=m,
                cmd=lambda mode=m: self.select_mode(mode),
                bg_col="#334155",
                fg_col="white",
                width=8,
            )
            btn.pack(side="left", padx=2, pady=2)

        row2 = tk.Frame(modes_frame, bg="#0f172a")
        row2.pack(anchor="e")
        extra_modes = [
            ("INVERSE", "CRICKET INVERSE"),
            ("ALL CRICKET", "ALL CRICKET"),
            ("HIDDEN", "HIDDEN CRICKET"),
        ]
        for label, mode_key in extra_modes:
            btn = create_btn(
                row2,
                text=label,
                cmd=lambda mode=mode_key: self.select_mode(mode),
                bg_col="#475569",
                fg_col="#a5f3fc",
                width=12,
            )
            btn.pack(side="left", padx=2, pady=2)

        # Config Panel
        config_frame = tk.Frame(self, bg="#1e293b", pady=5)
        config_frame.pack(fill="x")

        self.p_count_var = tk.IntVar(value=2)
        tk.Label(config_frame, text="Players:", bg="#1e293b", fg="#94a3b8").pack(
            side="left", padx=(20, 5)
        )
        tk.Button(config_frame, text="-", command=lambda: self.change_players(-1)).pack(
            side="left"
        )
        tk.Label(
            config_frame,
            textvariable=self.p_count_var,
            bg="#1e293b",
            fg="white",
            width=3,
        ).pack(side="left")
        tk.Button(config_frame, text="+", command=lambda: self.change_players(1)).pack(
            side="left"
        )

        # 名前編集ボタンを追加
        tk.Button(
            config_frame,
            text="NAMES",
            command=self.open_name_editor,
            bg="#334155",
            fg="white",
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=10)

        self.round_var = tk.IntVar(value=8)
        tk.Label(config_frame, text="Rounds:", bg="#1e293b", fg="#94a3b8").pack(
            side="left", padx=(20, 5)
        )
        tk.Button(config_frame, text="-", command=lambda: self.change_rounds(-1)).pack(
            side="left"
        )
        tk.Label(
            config_frame, textvariable=self.round_var, bg="#1e293b", fg="white", width=3
        ).pack(side="left")
        tk.Button(config_frame, text="+", command=lambda: self.change_rounds(1)).pack(
            side="left"
        )

        self.hidden_bonus_var = tk.IntVar(value=1)
        tk.Label(
            config_frame,
            text="Hidden Bonus:",
            bg="#1e293b",
            fg="#94a3b8",
        ).pack(side="left", padx=(20, 5))
        for bonus in [1, 2]:
            tk.Radiobutton(
                config_frame,
                text=str(bonus),
                variable=self.hidden_bonus_var,
                value=bonus,
                bg="#1e293b",
                fg="white",
                selectcolor="#334155",
                activebackground="#1e293b",
                activeforeground="white",
                highlightthickness=0,
            ).pack(side="left")

        # -- Main Content --
        main_frame = tk.Frame(self, bg="#1e293b")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        left_panel = tk.Frame(main_frame, bg="#1e293b")
        left_panel.pack(side="left", fill="y")

        self.info_lbl = tk.Label(
            left_panel,
            text="ROUND 1/8\nPLAYER 1",
            bg="#334155",
            fg="#fb7185",
            font=("Arial", 14, "bold"),
            width=30,
            pady=10,
        )
        self.info_lbl.pack(pady=(0, 10))

        self.board = DartboardCanvas(
            left_panel, size=340, on_hit_callback=self.on_board_hit
        )
        self.board.pack()

        throws_frame = tk.Frame(left_panel, bg="#1e293b", pady=10)
        throws_frame.pack()
        self.throw_labels = []
        for i in range(3):
            lbl = tk.Label(
                throws_frame,
                text=str(i + 1),
                width=4,
                height=2,
                bg="#334155",
                fg="gray",
                font=("Arial", 12, "bold"),
                relief="flat",
            )
            lbl.pack(side="left", padx=5)
            self.throw_labels.append(lbl)

        # Actions
        actions_frame = tk.Frame(left_panel, bg="#1e293b", pady=10)
        actions_frame.pack()

        create_btn(
            actions_frame,
            "MISS",
            lambda: self.on_board_hit(0, 1),
            "#ef4444",
            "white",
            6,
        ).pack(side="left", padx=5)
        create_btn(actions_frame, "UNDO", self.do_undo, "#eab308", "black", 6).pack(
            side="left", padx=5
        )
        create_btn(actions_frame, "SKIP", self.do_skip, "#475569", "white", 6).pack(
            side="left", padx=5
        )

        self.suggest_lbl = tk.Label(
            left_panel, text="", bg="#1e293b", fg="#38bdf8", font=("Arial", 10)
        )
        self.suggest_lbl.pack(pady=5)

        self.status_msg = ""
        self.status_lbl = tk.Label(
            left_panel,
            text="",
            bg="#1e293b",
            fg="#f59e0b",
            font=("Arial", 10, "bold"),
        )
        self.status_lbl.pack(pady=(0, 5))

        right_panel = tk.Frame(main_frame, bg="#1e293b", padx=20)
        right_panel.pack(side="right", expand=True, fill="both")

        self.score_container = tk.Frame(right_panel, bg="#1e293b")
        self.score_container.pack(fill="both", expand=True)

        tk.Label(right_panel, text="GAME LOG", bg="#1e293b", fg="#94a3b8").pack(
            anchor="w"
        )
        self.log_list = tk.Listbox(
            right_panel, bg="#0f172a", fg="#cbd5e1", height=6, relief="flat"
        )
        self.log_list.pack(fill="x", pady=5)

    def change_players(self, delta):
        new_val = max(1, min(4, self.p_count_var.get() + delta))
        self.p_count_var.set(new_val)
        self.reset_game(self.game.mode)

    def change_rounds(self, delta):
        new_val = max(1, min(30, self.round_var.get() + delta))
        self.round_var.set(new_val)
        self.reset_game(self.game.mode)

    def select_mode(self, mode):
        if mode == "COUNTUP":
            self.round_var.set(8)
        else:
            self.round_var.set(15)
        self.reset_game(mode)

    def reset_game(self, mode):
        # 名前リストを渡して初期化
        self.game.setup_game(
            mode,
            self.p_count_var.get(),
            self.round_var.get(),
            player_names=self.custom_names,
            hidden_cricket_bonus=self.hidden_bonus_var.get(),
        )
        self.status_msg = ""
        self.update_ui()

    def open_name_editor(self):
        # 名前編集用ポップアップ
        editor = Toplevel(self)
        editor.title("Edit Player Names")
        editor.geometry("300x300")
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
            ent.insert(0, current_name)
            ent.pack(side="right", expand=True, fill="x")
            entries.append(ent)

        def save_names():
            # 新しい名前を保存
            for i, ent in enumerate(entries):
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
                if i < len(self.custom_names):
                    self.game.players[i].name = self.custom_names[i]

            self.update_ui()
            editor.destroy()

        tk.Button(
            editor, text="SAVE", command=save_names, bg="#10b981", fg="white"
        ).pack(pady=20)

    def on_board_hit(self, raw, mult):
        award = self.game.handle_hit(raw, mult)
        if award:
            self.show_award(award)
        self.update_ui()
        if self.game.winner:
            messagebox.showinfo("WINNER", f"{self.game.winner.name} WINS!")

    def do_undo(self):
        if self.game.undo():
            self.update_ui()

    def do_skip(self):
        self.game.change_turn()
        self.update_ui()

    def show_award(self, text):
        self.status_msg = text

    def update_ui(self):
        curr_p = self.game.players[self.game.current_player_idx]
        self.info_lbl.config(
            text=f"ROUND {self.game.round}/{self.game.max_rounds}\n{curr_p.name}"
        )

        for i, lbl in enumerate(self.throw_labels):
            if i < len(self.game.current_throws):
                t = self.game.current_throws[i]
                lbl.config(text=t.display, bg="#fb7185", fg="white")
            else:
                lbl.config(text=str(i + 1), bg="#334155", fg="gray")

        for widget in self.score_container.winfo_children():
            widget.destroy()

        if self.game.mode == "HIDDEN CRICKET":
            self.draw_cricket_board()
        elif "CRICKET" in self.game.mode:
            self.draw_cricket_board()
        else:
            self.draw_score_board()

        self.update_suggestion(curr_p)
        self.status_lbl.config(text=self.status_msg)
        self.status_msg = ""
        self.log_list.delete(0, tk.END)
        for entry in self.game.game_log:
            self.log_list.insert(tk.END, entry)

    def draw_score_board(self):
        players = self.game.players
        cols = 2 if len(players) > 1 else 1

        for i, p in enumerate(players):
            is_active = i == self.game.current_player_idx
            bg = "#334155" if is_active else "#1e293b"
            fg = "#fb7185" if is_active else "white"

            frame = tk.Frame(self.score_container, bg=bg, bd=2, relief="groove")
            frame.grid(row=i // cols, column=i % cols, sticky="nsew", padx=2, pady=2)

            tk.Label(frame, text=p.name, bg=bg, fg="gray", font=("Arial", 10)).pack()
            tk.Label(
                frame, text=str(p.score), bg=bg, fg=fg, font=("Arial", 24, "bold")
            ).pack()

        for c in range(cols):
            self.score_container.grid_columnconfigure(c, weight=1)

    def draw_cricket_board(self):
        # レイアウト設定
        hidden_mode = self.game.mode == "HIDDEN CRICKET"
        targets = self.game.active_targets
        players = self.game.players
        num_players = len(players)

        # ヘッダーとスコア表示用のコンテナ
        # プレイヤーが2人の場合は [P1][Target][P2] の順、それ以外は [Target][P1][P2]...
        is_duel = num_players == 2

        # --- スコア・名前ヘッダー ---
        header_frame = tk.Frame(self.score_container, bg="#1e293b")
        header_frame.pack(fill="x", pady=(0, 10))

        # グリッドの重み設定
        if is_duel:
            header_frame.columnconfigure(0, weight=1)  # P1
            header_frame.columnconfigure(1, minsize=60)  # Target
            header_frame.columnconfigure(2, weight=1)  # P2
        else:
            header_frame.columnconfigure(0, minsize=60)
            for i in range(num_players):
                header_frame.columnconfigure(i + 1, weight=1)

        for i, p in enumerate(players):
            is_active = i == self.game.current_player_idx
            col = 0 if is_duel and i == 0 else 2 if is_duel else i + 1

            p_frame = tk.Frame(
                header_frame,
                bg="#334155" if is_active else "#1e293b",
                bd=1,
                relief="flat",
            )
            p_frame.grid(row=0, column=col, sticky="nsew", padx=2)

            tk.Label(
                p_frame, text=p.name, fg="gray", bg=p_frame["bg"], font=("Arial", 9)
            ).pack()
            tk.Label(
                p_frame,
                text=str(p.score),
                fg="#fb7185" if is_active else "white",
                bg=p_frame["bg"],
                font=("Arial", 18, "bold"),
            ).pack()

        # --- 中央数字 & マークエリア ---
        marks_frame = tk.Frame(self.score_container, bg="#0f172a", padx=5, pady=5)
        marks_frame.pack(fill="both", expand=True)

        if is_duel:
            marks_frame.columnconfigure(0, weight=1)
            marks_frame.columnconfigure(1, minsize=60)  # 中央
            marks_frame.columnconfigure(2, weight=1)
        else:
            marks_frame.columnconfigure(0, minsize=60)
            for i in range(num_players):
                marks_frame.columnconfigure(i + 1, weight=1)

        for r, target in enumerate(targets):
            # 行全体の背景（誰かがクローズしているか等の視覚効果用）
            row_bg = "#1e293b" if r % 2 == 0 else "#161e2e"

            # 中央の数字ラベル
            is_revealed = not hidden_mode or target in self.game.revealed_targets
            t_text = "BULL" if target == 25 else str(target)
            t_fg = "#f0c040"
            if hidden_mode and not is_revealed:
                t_text = "?"
                t_fg = "#94a3b8"
            target_lbl = tk.Label(
                marks_frame,
                text=t_text,
                bg="#334155",
                fg=t_fg,
                font=("Arial", 12, "bold"),
                width=5,
                pady=4,
            )

            target_col = 1 if is_duel else 0
            target_lbl.grid(row=r, column=target_col, pady=1, padx=2)

            # 各プレイヤーのマーク
            for i, p in enumerate(players):
                marks = p.marks.get(target, 0) if is_revealed else 0
                # マークの記号化
                mark_str = (
                    "⦻"
                    if marks >= 3
                    else "X" if marks == 2 else "/" if marks == 1 else ""
                )

                # 色：3本ならピンク(Closed)、それ以外は緑
                m_fg = "#fb7185" if marks >= 3 else "#10b981"
                m_col = (0 if i == 0 else 2) if is_duel else i + 1

                m_lbl = tk.Label(
                    marks_frame,
                    text=mark_str,
                    bg=row_bg,
                    fg=m_fg,
                    font=("Arial", 14, "bold"),
                )
                m_lbl.grid(row=r, column=m_col, sticky="nsew", pady=1)
        targets = self.game.active_targets
        is_large_mode = len(targets) > 10
        target_font = ("Arial", 9 if is_large_mode else 12, "bold")
        mark_font = ("Arial", 10 if is_large_mode else 14, "bold")

        headers = ["TARGET"] + [p.name[:3] for p in self.game.players]
        for col, text in enumerate(headers):
            tk.Label(
                self.score_container,
                text=text,
                bg="#1e293b",
                fg="gray",
                font=("Arial", 9),
            ).grid(row=0, column=col, padx=5, sticky="s")

        for r, target in enumerate(targets):
            is_revealed = not hidden_mode or target in self.game.revealed_targets
            t_label = "BULL" if target == 25 else str(target)
            if hidden_mode and not is_revealed:
                t_label = "?"
            tk.Label(
                self.score_container,
                text=t_label,
                bg="#1e293b",
                fg="#94a3b8" if hidden_mode and not is_revealed else "white",
                font=target_font,
            ).grid(row=r + 1, column=0, pady=1 if is_large_mode else 2)

            for c, p in enumerate(self.game.players):
                marks = p.marks.get(target, 0) if is_revealed else 0
                mark_str = "・"
                if marks == 1:
                    mark_str = "/"
                elif marks == 2:
                    mark_str = "X"
                elif marks >= 3:
                    mark_str = "⦻"

                fg = "#fb7185" if marks >= 3 else "#10b981"
                bg_col = (
                    "#334155"
                    if p.id == self.game.players[self.game.current_player_idx].id
                    else "#1e293b"
                )

                lbl = tk.Label(
                    self.score_container,
                    text=mark_str,
                    bg=bg_col,
                    fg=fg,
                    font=mark_font,
                )
                lbl.grid(row=r + 1, column=c + 1, sticky="nsew", padx=1)

        score_row = len(targets) + 1
        tk.Label(
            self.score_container,
            text="SCORE",
            bg="#1e293b",
            fg="gray",
            font=("Arial", 10),
        ).grid(row=score_row, column=0, pady=(5, 0))
        for c, p in enumerate(self.game.players):
            bg_col = (
                "#334155"
                if p.id == self.game.players[self.game.current_player_idx].id
                else "#1e293b"
            )
            tk.Label(
                self.score_container,
                text=str(p.score),
                bg=bg_col,
                fg="white",
                font=("Arial", 12, "bold"),
            ).grid(row=score_row, column=c + 1, sticky="nsew", pady=(5, 0))

        for c in range(len(self.game.players) + 1):
            self.score_container.grid_columnconfigure(c, weight=1)

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
