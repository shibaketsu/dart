"""Local member profiles and completed-match results."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps


class MemberStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.photos = self.directory / 'photos'
        self.photos.mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.directory / 'members.sqlite3')
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys = ON')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS members (
                id TEXT PRIMARY KEY, name TEXT NOT NULL,
                photo TEXT, position INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY, mode TEXT NOT NULL, played_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS results (
                match_id TEXT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                member_id TEXT NOT NULL REFERENCES members(id),
                name TEXT NOT NULL, score INTEGER NOT NULL, won INTEGER NOT NULL,
                darts INTEGER NOT NULL, points INTEGER NOT NULL,
                bulls INTEGER NOT NULL, marks INTEGER NOT NULL, awards TEXT NOT NULL,
                PRIMARY KEY (match_id, member_id));
        ''')

    def list_members(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM members ORDER BY position, id')]

    def get(self, member_id):
        row = self.db.execute('SELECT * FROM members WHERE id = ?', (member_id,)).fetchone()
        return dict(row) if row else None

    def save_member(self, name, member_id=None, photo_source=None, remove_photo=False):
        name = name.strip()
        if not name or len(name) > 40:
            raise ValueError('名前は1〜40文字で入力してください。')
        old = self.get(member_id) if member_id else None
        if member_id and not old:
            raise ValueError('メンバーが見つかりません。')
        member_id = member_id or uuid.uuid4().hex
        photo = old['photo'] if old else None
        created_photo = None
        if photo_source:
            # Store a managed copy so moving the original never breaks a profile.
            created_photo = self.photos / f'{uuid.uuid4().hex}.png'
            with Image.open(photo_source) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                ImageOps.fit(image, (256, 256), Image.Resampling.LANCZOS).save(created_photo)
            photo = created_photo.name
        elif remove_photo:
            photo = None
        try:
            with self.db:
                if old:
                    self.db.execute('UPDATE members SET name=?, photo=? WHERE id=?',
                                    (name, photo, member_id))
                else:
                    position = self.db.execute('SELECT COALESCE(MAX(position), -1)+1 FROM members').fetchone()[0]
                    self.db.execute('INSERT INTO members VALUES (?, ?, ?, ?)',
                                    (member_id, name, photo, position))
        except Exception:
            if created_photo:
                created_photo.unlink(missing_ok=True)
            raise
        return member_id

    def photo_path(self, member):
        return self.photos / member['photo'] if member and member['photo'] else None

    def reorder(self, member_ids):
        if len(member_ids) != len(set(member_ids)) or set(member_ids) != {m['id'] for m in self.list_members()}:
            raise ValueError('並び順が登録済みメンバーと一致しません。')
        with self.db:
            self.db.executemany('UPDATE members SET position=? WHERE id=?', enumerate(member_ids))

    def record_match(self, match_id, game, roster):
        """Replace atomically: saving a finished game twice never duplicates it."""
        if not game.winner:
            raise ValueError('終了した試合だけ記録できます。')
        if len(roster) != len(game.players):
            raise ValueError('参加メンバーとプレイヤー数が一致しません。')
        ids = [m for m in roster if m]
        if len(ids) != len(set(ids)):
            raise ValueError('同じメンバーは同じ試合に複数登録できません。')
        with self.db:
            self.db.execute('DELETE FROM matches WHERE id=?', (match_id,))
            self.db.execute('INSERT INTO matches VALUES (?, ?, ?)',
                            (match_id, game.mode, datetime.now(timezone.utc).isoformat()))
            for player, member_id in zip(game.players, roster):
                if not member_id:
                    continue
                self.db.execute('INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                (match_id, member_id, player.name, player.score,
                                 int(player.id == game.winner.id), player.darts_thrown,
                                 player.points_thrown, player.bulls_hit, player.cricket_marks,
                                 json.dumps(player.awards)))

    def remove_match(self, match_id):
        with self.db:
            self.db.execute('DELETE FROM matches WHERE id=?', (match_id,))

    def history(self, member_id):
        rows = self.db.execute('''SELECT r.*, m.mode, m.played_at FROM results r
            JOIN matches m ON m.id=r.match_id WHERE r.member_id=?
            ORDER BY m.played_at DESC''', (member_id,))
        return [dict(r) for r in rows]

    def statistics(self, member_id):
        history = self.history(member_id)
        awards = {}
        by_mode = {}
        for result in history:
            mode = by_mode.setdefault(result['mode'], dict(games=0, wins=0, darts=0,
                                                          points=0, marks=0, best=None))
            for key in ('darts', 'points', 'marks'):
                mode[key] += result[key]
            mode['games'] += 1
            mode['wins'] += result['won']
            score = result['score']
            mode['best'] = score if mode['best'] is None else (
                max(mode['best'], score) if result['mode'] == 'COUNTUP' else min(mode['best'], score))
            for name, count in json.loads(result['awards']).items():
                awards[name] = awards.get(name, 0) + count
        return dict(games=len(history), wins=sum(r['won'] for r in history),
                    bulls=sum(r['bulls'] for r in history), awards=awards, modes=by_mode)

    def close(self):
        self.db.close()
