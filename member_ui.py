"""Member registration, photographs, results and drag-to-order roster."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from PIL import Image, ImageOps, ImageTk


class MemberWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app, self.store = app, app.member_store
        self.title('メンバー / MEMBERS')
        self.geometry('880x640')
        self.minsize(800, 580)
        self.configure(bg='#1e293b')
        self.transient(app)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.bind('<Escape>', lambda event: self.close())
        self.selected = {mid for mid in app.roster if mid}
        self.editing_id = None
        self.photo_source = None
        self.remove_photo = False
        self.drag_id = None
        tk.Label(self, text='MEMBERS', bg='#1e293b', fg='white',
                 font=('Arial', 18, 'bold')).pack(anchor='w', padx=18, pady=(16, 4))
        tk.Label(self, text='名前を選んで参加にチェック。行をドラッグして投球順を変更できます。',
                 bg='#1e293b', fg='#cbd5e1').pack(anchor='w', padx=18)
        body = tk.Frame(self, bg='#1e293b')
        body.pack(fill='both', expand=True, padx=18, pady=12)
        left = tk.Frame(body, bg='#1e293b')
        left.pack(side='left', fill='both', expand=True, padx=(0, 16))
        self.tree = ttk.Treeview(left, columns=('join', 'name', 'games', 'wins'), show='headings',
                                 selectmode='browse', height=14)
        for key, label, width in [('join', '参加', 42), ('name', '名前（ドラッグで並べ替え）', 190),
                                  ('games', '試合', 46), ('wins', '勝利', 46)]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, minwidth=width, stretch=key == 'name')
        scroll = ttk.Scrollbar(left, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.show_selected)
        self.tree.bind('<ButtonPress-1>', self.drag_start, add='+')
        self.tree.bind('<B1-Motion>', self.drag_motion)
        self.tree.bind('<ButtonRelease-1>', self.drag_end)
        self.tree.bind('<Double-1>', lambda event: self.toggle_selected())
        detail = tk.Frame(body, bg='#0f172a', padx=14, pady=12, width=300)
        detail.pack(side='right', fill='both')
        self.preview = tk.Label(detail, bg='#334155', fg='#cbd5e1')
        self.preview.pack()
        photo_actions = tk.Frame(detail, bg='#0f172a')
        photo_actions.pack(pady=6)
        app.create_button(photo_actions, '写真を選択', self.choose_photo, width=9).pack(side='left', padx=2)
        app.create_button(photo_actions, '写真を外す', self.clear_photo, width=9).pack(side='left', padx=2)
        self.name_var = tk.StringVar()
        self.entry = ttk.Entry(detail, textvariable=self.name_var, width=28)
        self.entry.pack(fill='x', pady=6)
        self.join_var = tk.BooleanVar()
        self.join_check = ttk.Checkbutton(detail, text='このメンバーが参加（最大4人）',
                                          variable=self.join_var, command=self.toggle_selected)
        self.join_check.pack(anchor='w', pady=4)
        buttons = tk.Frame(detail, bg='#0f172a')
        buttons.pack(fill='x', pady=6)
        app.create_button(buttons, '新規登録', self.new_member, width=9).pack(side='left', padx=2)
        app.create_button(buttons, '保存', self.save, width=9, accent=True).pack(side='left', padx=2)
        self.stats = tk.Text(detail, width=32, height=12, bg='#0f172a', fg='#cbd5e1',
                             relief='flat', wrap='word', font=('Arial', 10))
        self.stats.pack(fill='both', expand=True)
        bottom = tk.Frame(self, bg='#1e293b', padx=18)
        bottom.pack(fill='x', pady=(0, 14))
        self.roster_label = tk.Label(bottom, bg='#1e293b', fg='#67e8f9', wraplength=500, anchor='w')
        self.roster_label.pack(fill='x', pady=(0, 8))
        self.start_button = app.create_button(bottom, 'この順でゲーム開始', self.start, width=20, accent=True)
        self.start_button.pack(side='right')
        app.create_button(bottom, 'ゲストで開始', self.guests, width=13).pack(side='left')
        app.create_button(bottom, '閉じる', self.close).pack(side='left', padx=8)
        self.refresh()
        self.new_member()
        self.grab_set()

    def close(self):
        self.grab_release()
        self.destroy()
        self.app.member_window = None

    def refresh(self, focus=None):
        self.tree.delete(*self.tree.get_children())
        for m in self.store.list_members():
            stats = self.store.statistics(m['id'])
            self.tree.insert('', 'end', iid=m['id'], values=(
                '●' if m['id'] in self.selected else '', m['name'], stats['games'], stats['wins']))
        if focus:
            self.tree.selection_set(focus)
            self.tree.see(focus)
        self.update_roster_label()

    def update_roster_label(self):
        members = [self.store.get(mid)['name'] for mid in self.tree.get_children() if mid in self.selected]
        self.roster_label.configure(text='投球順：' + (' → '.join(members) if members else '参加メンバーを選択してください'))
        self.start_button.configure(state='normal' if members else 'disabled')

    def show_selected(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        member = self.store.get(selected[0])
        self.editing_id = member['id']
        self.name_var.set(member['name'])
        self.photo_source, self.remove_photo = None, False
        self.join_var.set(member['id'] in self.selected)
        self.join_check.state(['!disabled'])
        self.show_photo(self.store.photo_path(member))
        stat = self.store.statistics(member['id'])
        lines = [f"{stat['games']} 試合 / {stat['wins']} 勝 / BULL {stat['bulls']} 回", '']
        for mode, data in stat['modes'].items():
            avg = (3*data['marks'] if 'CRICKET' in mode else data['points']) / max(1, data['darts'])
            metric = 'MPR' if 'CRICKET' in mode else '平均投点'
            lines.extend([f"{mode}: {data['games']} 試合 / {data['wins']} 勝",
                          f"{metric} {avg:.2f}  / ベスト {data['best']}"])
        if stat['awards']:
            lines.extend(['', 'AWARDS'] + [f'{name}: {count}' for name, count in stat['awards'].items()])
        history = self.store.history(member['id'])
        if history:
            lines.extend(['', '最近の試合'])
            for result in history[:10]:
                date = datetime.fromisoformat(result['played_at']).astimezone().strftime('%m/%d %H:%M')
                lines.append(f"{date} {result['mode']}  {result['score']} {'WIN' if result['won'] else ''}")
        else:
            lines.append('試合を終了すると成績が自動で記録されます。')
        self.stats.configure(state='normal')
        self.stats.delete('1.0', 'end')
        self.stats.insert('1.0', '\n'.join(lines))
        self.stats.configure(state='disabled')

    def show_photo(self, path):
        image = Image.new('RGB', (112, 112), '#334155')
        if path:
            try:
                with Image.open(path) as source:
                    image = ImageOps.fit(ImageOps.exif_transpose(source).convert('RGB'),
                                         (112, 112), Image.Resampling.LANCZOS)
            except (OSError, ValueError):
                pass
        self._photo = ImageTk.PhotoImage(image, master=self)
        self.preview.configure(image=self._photo)

    def new_member(self):
        self.tree.selection_remove(*self.tree.selection())
        self.editing_id = None
        self.name_var.set('')
        self.photo_source, self.remove_photo = None, False
        self.join_var.set(False)
        self.join_check.state(['disabled'])
        self.show_photo(None)
        self.stats.configure(state='normal')
        self.stats.delete('1.0', 'end')
        self.stats.insert('1.0', '名前と写真を設定して「保存」で登録します。\n写真は省略できます。')
        self.stats.configure(state='disabled')
        self.entry.focus_set()

    def choose_photo(self):
        path = filedialog.askopenfilename(parent=self, title='メンバーの写真',
                                          filetypes=[('写真', '*.png *.jpg *.jpeg *.webp *.gif'), ('全ファイル', '*')])
        if path:
            try:
                with Image.open(path) as image:
                    image.verify()
            except (OSError, ValueError) as error:
                messagebox.showerror('写真を読み込めません', str(error), parent=self)
                return
            self.photo_source, self.remove_photo = path, False
            self.show_photo(path)

    def clear_photo(self):
        self.photo_source, self.remove_photo = None, True
        self.show_photo(None)

    def save(self):
        try:
            mid = self.store.save_member(self.name_var.get(), self.editing_id,
                                         self.photo_source, self.remove_photo)
        except Exception as error:
            messagebox.showerror('保存できません', str(error), parent=self)
            return
        self.app.refresh_member_names()
        self.refresh(mid)
        self.show_selected()

    def toggle_selected(self):
        if not self.editing_id:
            return
        if self.editing_id in self.selected:
            self.selected.remove(self.editing_id)
        elif len(self.selected) < 4:
            self.selected.add(self.editing_id)
        else:
            messagebox.showinfo('参加人数', '参加できるメンバーは最大4人です。', parent=self)
        self.join_var.set(self.editing_id in self.selected)
        self.refresh(self.editing_id)

    def drag_start(self, event):
        self.drag_id = self.tree.identify_row(event.y)

    def drag_motion(self, event):
        row = self.tree.identify_row(event.y)
        if self.drag_id and row and row != self.drag_id:
            self.tree.move(self.drag_id, '', self.tree.index(row))
            self.tree.see(self.drag_id)
            self.update_roster_label()

    def drag_end(self, event):
        if self.drag_id:
            try:
                self.store.reorder(list(self.tree.get_children()))
            except Exception as error:
                messagebox.showerror('並び順を保存できません', str(error), parent=self)
                self.refresh(self.editing_id)
        self.drag_id = None

    def start(self):
        roster = [mid for mid in self.tree.get_children() if mid in self.selected]
        if roster and self.app.start_roster(roster):
            self.close()

    def guests(self):
        if self.app.start_roster([None] * self.app.p_count_var.get()):
            self.close()
