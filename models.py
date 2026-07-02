# models.py
import copy
import random

from config import CRICKET_TARGETS, CRICKET_TARGET_POOL, HIDDEN_CRICKET_TARGET_COUNT


class HitResult:
    def __init__(self, score, multiplier, raw_number, is_bull):
        self.score = score
        self.multiplier = multiplier
        self.raw_number = raw_number
        self.is_bull = is_bull
        self.display = self._get_display()

    def _get_display(self):
        if self.raw_number == 0:
            return "MISS"
        if self.is_bull:
            return "D-BULL" if self.multiplier == 2 else "S-BULL"
        prefix = "T" if self.multiplier == 3 else "D" if self.multiplier == 2 else "S"
        return f"{prefix}-{self.raw_number}"


class Player:
    def __init__(self, pid, name, start_score=0, targets=None):
        self.id = pid
        self.name = name
        self.score = start_score
        self.round_start_score = start_score
        # ターゲットが指定されていない場合はデフォルト（通常のクリケット）を使用
        if targets is None:
            self.marks = {t: 0 for t in CRICKET_TARGETS}
        else:
            self.marks = {t: 0 for t in targets}

    def copy(self):
        # 現在のターゲット設定を引き継いでコピーを作成
        p = Player(self.id, self.name, self.score, targets=list(self.marks.keys()))
        p.round_start_score = self.round_start_score
        p.marks = self.marks.copy()
        return p


class DartsGame:
    def __init__(self):
        self.mode = "COUNTUP"
        self.players = []
        self.current_player_idx = 0
        self.round = 1
        self.max_rounds = 8
        self.current_throws = []
        self.winner = None
        self.history = []
        self.game_log = []
        self.active_targets = CRICKET_TARGETS
        self.hidden_cricket_targets = []
        self.revealed_targets = set()
        self.current_turn_limit = 3
        self.hidden_cricket_bonus = 1

    # 変更: player_names引数を追加
    def setup_game(
        self,
        mode,
        player_count,
        max_rounds,
        player_names=None,
        hidden_cricket_bonus=1,
    ):
        self.mode = mode
        self.max_rounds = max_rounds
        self.current_player_idx = 0
        self.round = 1
        self.current_throws = []
        self.winner = None
        self.history = []
        self.game_log = []
        self.current_turn_limit = 3
        self.hidden_cricket_bonus = (
            1 if hidden_cricket_bonus not in [1, 2] else hidden_cricket_bonus
        )
        self.hidden_cricket_targets = []
        self.revealed_targets = set()

        start_score = 0
        self.active_targets = []

        # モード設定
        if mode == "CRICKET":
            self.active_targets = CRICKET_TARGETS
        elif mode == "CRICKET INVERSE":
            self.active_targets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        elif mode == "ALL CRICKET":
            self.active_targets = list(range(1, 21)) + [25]
        elif mode == "HIDDEN CRICKET":
            self.hidden_cricket_targets = random.sample(
                CRICKET_TARGET_POOL, HIDDEN_CRICKET_TARGET_COUNT
            )
            self.active_targets = list(self.hidden_cricket_targets)
        elif mode in ["301", "501"]:
            start_score = int(mode)
            self.active_targets = []

        # 変更: 名前リストがあればそれを使用、なければデフォルト
        self.players = []
        for i in range(player_count):
            name = f"PLAYER {i+1}"
            if player_names and i < len(player_names):
                name = player_names[i]

            self.players.append(
                Player(i + 1, name, start_score, targets=self.active_targets)
            )

        self.save_state()

    def save_state(self):
        state = {
            "players": [p.copy() for p in self.players],
            "current_player_idx": self.current_player_idx,
            "round": self.round,
            "current_throws": copy.deepcopy(self.current_throws),
            "winner": copy.deepcopy(self.winner),
            "game_log": copy.deepcopy(self.game_log),
            "current_turn_limit": self.current_turn_limit,
            "hidden_cricket_targets": copy.deepcopy(self.hidden_cricket_targets),
            "revealed_targets": copy.deepcopy(self.revealed_targets),
            "hidden_cricket_bonus": self.hidden_cricket_bonus,
        }
        self.history.append(state)

    def undo(self):
        # 1投戻る処理
        if len(self.history) > 1:
            state = self.history.pop()
            self.players = [p.copy() for p in state["players"]]
            self.current_player_idx = state["current_player_idx"]
            self.round = state["round"]
            self.current_throws = copy.deepcopy(state["current_throws"])
            self.winner = copy.deepcopy(state["winner"])
            self.game_log = copy.deepcopy(state["game_log"])
            self.current_turn_limit = state.get("current_turn_limit", 3)
            self.hidden_cricket_targets = copy.deepcopy(
                state.get("hidden_cricket_targets", [])
            )
            self.revealed_targets = copy.deepcopy(state.get("revealed_targets", set()))
            self.hidden_cricket_bonus = state.get("hidden_cricket_bonus", 1)
            return True
        return False

    def handle_hit(self, raw_num, mult):
        if self.winner:
            return None

        self.save_state()
        award = None

        score_val = raw_num * mult
        is_bull = raw_num == 25

        if self.mode in ["COUNTUP", "301", "501"] and is_bull:
            score_val = 50

        hit = HitResult(score_val, mult, raw_num, is_bull)
        self.current_throws.append(hit)

        current_p = self.players[self.current_player_idx]

        if self.mode == "COUNTUP":
            current_p.score += score_val

        elif self.mode in ["301", "501"]:
            temp_score = current_p.score - score_val
            if temp_score < 0:
                current_p.score = current_p.round_start_score
                self.change_turn(bust=True)
                return "BUST"
            elif temp_score == 0:
                current_p.score = 0
                self.winner = current_p
                return "WIN"
            else:
                current_p.score = temp_score

        # クリケット系全般
        elif "CRICKET" in self.mode:
            if raw_num in self.active_targets:
                is_hidden_cricket = self.mode == "HIDDEN CRICKET"
                newly_revealed = False
                if is_hidden_cricket and raw_num not in self.revealed_targets:
                    self.revealed_targets.add(raw_num)
                    newly_revealed = True

                marks_to_add = mult
                if newly_revealed:
                    marks_to_add += self.hidden_cricket_bonus
                needed = 3 - current_p.marks[raw_num]

                if needed > 0:
                    used = min(marks_to_add, needed)
                    current_p.marks[raw_num] += used
                    marks_to_add -= used

                if marks_to_add > 0:
                    for p in self.players:
                        if p.id != current_p.id and p.marks[raw_num] < 3:
                            p.score += marks_to_add * raw_num

                all_closed = all(current_p.marks[t] >= 3 for t in self.active_targets)
                if all_closed:
                    lowest = True
                    for p in self.players:
                        if p.score < current_p.score:
                            lowest = False
                    if lowest:
                        self.winner = current_p
                        return "WIN"

                if newly_revealed:
                    award = f"REVEAL {raw_num} (+{self.hidden_cricket_bonus})"
        if len(self.current_throws) == 3:
            total = sum(t.score for t in self.current_throws)
            if "CRICKET" not in self.mode:
                if total >= 151:
                    award = "HIGH TON"
                elif total >= 100:
                    award = "LOW TON"
                if all(t.is_bull for t in self.current_throws):
                    award = "HAT TRICK"

        if len(self.current_throws) >= self.current_turn_limit:
            self.change_turn()

        return award

    def change_turn(self, bust=False):
        p_name = self.players[self.current_player_idx].name
        total = sum(t.score for t in self.current_throws)
        if bust:
            total = 0
        self.game_log.insert(0, f"R{self.round} {p_name}: {total}")

        self.current_throws = []

        is_last_player = self.current_player_idx == len(self.players) - 1
        if self.round == self.max_rounds and is_last_player:
            sorted_players = sorted(self.players, key=lambda p: p.score)
            if self.mode == "COUNTUP":
                self.winner = sorted_players[-1]
            else:
                self.winner = sorted_players[0]
            return

        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.players[self.current_player_idx].round_start_score = self.players[
            self.current_player_idx
        ].score

        if is_last_player:
            self.round += 1
