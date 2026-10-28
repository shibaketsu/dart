import sqlite3
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from members import MemberStore
from models import DartsGame


class MemberTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = MemberStore(self.tmp.name)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def finished_game(self):
        game = DartsGame()
        game.setup_game('COUNTUP', 2, 1)
        for _ in range(3):
            game.handle_hit(25, 1)
        for _ in range(3):
            game.handle_hit(1, 1)
        return game

    def test_profiles_photos_order_survive_reopen(self):
        source = Path(self.tmp.name) / 'original.jpg'
        Image.new('RGB', (640, 320), 'blue').save(source)
        a = self.store.save_member('Alice', photo_source=source)
        b = self.store.save_member('Bob')
        self.store.reorder([b, a])
        source.unlink()
        self.store.close()
        self.store = MemberStore(self.tmp.name)
        self.assertEqual([m['id'] for m in self.store.list_members()], [b, a])
        with Image.open(self.store.photo_path(self.store.get(a))) as photo:
            self.assertEqual(photo.size, (256, 256))
        self.store.save_member('Alice 2', a)
        self.assertIsNotNone(self.store.get(a)['photo'])
        self.store.save_member('Alice 2', a, remove_photo=True)
        self.assertIsNone(self.store.get(a)['photo'])

    def test_invalid_profile_and_reorder_preserve_data(self):
        a = self.store.save_member('Alice')
        for name in ('', ' '*3, 'x'*41):
            with self.assertRaises(ValueError):
                self.store.save_member(name, a)
        with self.assertRaises(ValueError):
            self.store.reorder([a, a])
        with self.assertRaises(OSError):
            self.store.save_member('New', photo_source='/nonexistent.jpg')
        self.assertEqual(len(self.store.list_members()), 1)
        self.assertEqual(self.store.get(a)['name'], 'Alice')

    def test_match_idempotence_guests_and_undo_removal(self):
        a = self.store.save_member('Alice')
        game = self.finished_game()
        for _ in range(2):
            self.store.record_match('same-match', game, [a, None])
        self.assertEqual(len(self.store.history(a)), 1)
        stat = self.store.statistics(a)
        self.assertEqual((stat['games'], stat['wins'], stat['bulls']), (1, 1, 3))
        self.assertEqual(stat['awards'], {'HAT TRICK': 1, 'LOW TON': 1})
        self.assertEqual(stat['modes']['COUNTUP']['best'], 150)
        self.store.remove_match('same-match')
        self.assertEqual(self.store.statistics(a)['games'], 0)
        self.store.record_match('same-match', game, [a, None])
        self.assertEqual(self.store.statistics(a)['games'], 1)

    def test_failed_match_replace_rolls_back(self):
        a = self.store.save_member('Alice')
        game = self.finished_game()
        self.store.record_match('match', game, [a, None])
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.record_match('match', game, ['missing', None])
        self.assertEqual(len(self.store.history(a)), 1)
        with self.assertRaises(ValueError):
            self.store.record_match('match', game, [a, a])

    def test_both_members_get_independent_stats(self):
        a, b = self.store.save_member('Alice'), self.store.save_member('Bob')
        self.store.record_match('match', self.finished_game(), [a, b])
        self.assertEqual(self.store.statistics(a)['wins'], 1)
        self.assertEqual(self.store.statistics(b)['wins'], 0)
        self.assertEqual(self.store.statistics(b)['modes']['COUNTUP']['points'], 3)


class AwardTests(unittest.TestCase):
    def game(self, mode='COUNTUP', rounds=8):
        game = DartsGame()
        game.setup_game(mode, 2, rounds)
        return game

    def test_award_detection_and_undo(self):
        cases = [([(25, 1)]*3, 'HAT TRICK'), ([(20, 3)]*3, 'TON 80'),
                 ([(20, 3), (19, 3), (18, 3)], 'HIGH TON'),
                 ([(20, 3), (20, 1), (20, 1)], 'LOW TON'),
                 ([(19, 3)]*3, 'THREE IN A BED')]
        for throws, expected in cases:
            with self.subTest(expected):
                game = self.game()
                for raw, mult in throws:
                    actual = game.handle_hit(raw, mult)
                self.assertEqual(actual, expected)
                self.assertEqual(game.players[0].awards[expected], 1)
                self.assertTrue(all(count == 1 for count in game.players[0].awards.values()))
                self.assertEqual(game.players[0].darts_thrown, 3)
                game.undo()
                self.assertEqual(game.players[0].awards, {})
                self.assertEqual(game.players[0].darts_thrown, 2)
                self.assertEqual(game.handle_hit(*throws[-1]), expected)
                self.assertEqual(game.players[0].awards[expected], 1)
                self.assertTrue(all(count == 1 for count in game.players[0].awards.values()))

    def test_cricket_bulls_and_marks_exclude_hidden_bonus(self):
        game = self.game('CRICKET')
        for _ in range(3):
            award = game.handle_hit(25, 1)
        self.assertEqual(award, 'HAT TRICK')
        self.assertEqual(game.players[0].cricket_marks, 3)
        game = self.game('HIDDEN CRICKET')
        target = game.active_targets[0]
        game.handle_hit(target, 1)
        self.assertEqual(game.players[0].cricket_marks, 1)
        self.assertEqual(game.players[0].marks[target], 2)

    def test_early_checkout_counts_and_undo(self):
        game = self.game('301')
        game.players[0].score = 50
        game.handle_hit(25, 1)
        self.assertIsNotNone(game.winner)
        self.assertEqual(game.players[0].bulls_hit, 1)
        game.undo()
        self.assertIsNone(game.winner)
        self.assertEqual(game.players[0].darts_thrown, 0)

    def test_miss_bust_reset_and_final_round_awards(self):
        game = self.game('301')
        game.players[0].score = 10
        self.assertEqual(game.handle_hit(20, 3), 'BUST')
        self.assertEqual(game.players[0].awards, {})
        self.assertEqual(game.players[0].darts_thrown, 1)
        game.undo()
        self.assertEqual(game.players[0].darts_thrown, 0)
        game = self.game(rounds=1)
        for _ in range(3):
            game.handle_hit(0, 1)
        for _ in range(3):
            award = game.handle_hit(25, 2)
        self.assertEqual(award, 'THREE IN THE BLACK')
        self.assertEqual(game.winner.id, 2)
        self.assertEqual(game.players[1].awards, {'THREE IN THE BLACK': 1, 'HAT TRICK': 1, 'LOW TON': 1})
        game.setup_game('COUNTUP', 1, 8)
        self.assertEqual(game.players[0].awards, {})


if __name__ == '__main__':
    unittest.main()
