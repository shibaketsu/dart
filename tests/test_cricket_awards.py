import unittest
from models import DartsGame


class CricketAwardTests(unittest.TestCase):
    def game(self, mode='CRICKET'):
        game = DartsGame()
        game.setup_game(mode, 2, 15)
        return game

    def test_counts_5_through_9_and_undo(self):
        for count, multipliers in [(5,(3,1,1)), (6,(3,2,1)), (7,(3,3,1)),
                                    (8,(3,3,2)), (9,(3,3,3))]:
            with self.subTest(count):
                game = self.game()
                for target, mult in zip((20,19,18), multipliers):
                    award = game.handle_hit(target, mult)
                self.assertIn(f'{count} COUNT', game.last_awards)
                self.assertEqual(game.players[0].awards[f'{count} COUNT'], 1)
                self.assertEqual(game.players[0].cricket_marks, count)
                self.assertEqual(award, 'WHITE HORSE' if count == 9 else f'{count} COUNT')
                game.undo()
                self.assertEqual(game.players[0].awards, {})
                game.handle_hit(18, multipliers[-1])
                self.assertEqual(game.players[0].awards[f'{count} COUNT'], 1)

    def test_closed_and_non_targets_do_not_count(self):
        game = self.game()
        for p in game.players:
            p.marks[20] = 3
        for raw, mult in [(20,3), (14,3), (19,3)]:
            game.handle_hit(raw,mult)
        self.assertEqual(game.players[0].cricket_marks, 3)
        self.assertEqual(game.last_awards, [])

    def test_scoring_hits_count_when_opponent_still_open(self):
        game = self.game()
        game.players[0].marks[20] = 3
        for _ in range(3): game.handle_hit(20,3)
        self.assertEqual(game.players[1].score, 180)
        self.assertEqual(game.last_awards, ['THREE IN A BED', '9 COUNT'])

    def test_white_horse_requires_available_distinct_triples(self):
        game = self.game()
        for raw,mult in [(20,3),(19,3),(18,3)]: game.handle_hit(raw,mult)
        self.assertEqual(game.last_awards, ['WHITE HORSE', '9 COUNT'])
        game = self.game()
        for p in game.players: p.marks[20] = 3
        for raw in (20,19,18): game.handle_hit(raw,3)
        self.assertNotIn('WHITE HORSE', game.last_awards)
        self.assertIn('6 COUNT', game.last_awards)

    def test_hidden_bonus_is_not_an_award_mark(self):
        game = self.game('HIDDEN CRICKET')
        game.hidden_cricket_bonus = 2
        for target in game.active_targets[:3]: game.handle_hit(target,1)
        self.assertEqual(game.players[0].cricket_marks, 3)
        self.assertFalse(any(name.endswith('COUNT') for name in game.last_awards))
        game = self.game('HIDDEN CRICKET')
        targets = [t for t in game.active_targets if t != 25]
        for target, mult in zip(targets, (3,2,1)): game.handle_hit(target,mult)
        self.assertIn('6 COUNT', game.last_awards)

    def test_all_and_inverse_use_their_own_targets(self):
        for mode in ('ALL CRICKET', 'CRICKET INVERSE'):
            game = self.game(mode)
            for target,mult in [(1,3),(2,2),(3,1)]: game.handle_hit(target,mult)
            self.assertIn('6 COUNT', game.last_awards)

    def test_skip_and_early_win_finalize_once(self):
        game = self.game()
        game.handle_hit(20,3)
        game.handle_hit(19,2)
        self.assertEqual(game.last_awards, [])
        self.assertEqual(game.skip_turn(), '5 COUNT')
        self.assertEqual(game.players[0].awards, {'5 COUNT': 1})
        game.undo()
        self.assertEqual(game.players[0].awards, {})
        self.assertEqual(game.skip_turn(), '5 COUNT')
        game = self.game()
        for target in game.active_targets: game.players[0].marks[target] = 3
        game.players[0].marks[20] = 0
        game.players[0].marks[19] = 0
        game.handle_hit(20,3)
        self.assertEqual(game.handle_hit(19,2), None)
        game.handle_hit(19,1)
        self.assertIsNotNone(game.winner)
        self.assertIn('6 COUNT', game.last_awards)

    def test_bull_5_count_and_black_6_count_overlap(self):
        game = self.game()
        for mult in (2,2,1): game.handle_hit(25,mult)
        self.assertEqual(game.last_awards, ['HAT TRICK', '5 COUNT'])
        game = self.game()
        for _ in range(3): game.handle_hit(25,2)
        self.assertEqual(game.last_awards, ['THREE IN THE BLACK', 'HAT TRICK', '6 COUNT'])

    def test_double_bed_high_out_and_one_bull(self):
        game = self.game('COUNTUP')
        for _ in range(3): game.handle_hit(18,2)
        self.assertEqual(game.last_awards, ['THREE IN A BED', 'LOW TON'])
        game = self.game('301')
        game.players[0].score = game.players[0].round_start_score = 120
        game.handle_hit(20,3)
        self.assertEqual(game.handle_hit(20,3), 'HIGH OUT')
        self.assertEqual(game.last_awards, ['HIGH OUT', 'LOW TON'])
        game = self.game('COUNTUP')
        for raw in (25,1,2): game.handle_hit(raw,1)
        self.assertEqual(game.last_awards, ['ONE BULL'])


if __name__ == '__main__':
    unittest.main()
