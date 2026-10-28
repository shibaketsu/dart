"""Run in a desktop session: python tests/gui_smoke.py (uses temporary data)."""
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from main import DartsApp
from awards import VIDEO_NAMES


def pump(app, milliseconds=100):
    app.after(milliseconds, app.quit)
    app.mainloop()
    app.update_idletasks()


def main():
    with tempfile.TemporaryDirectory() as directory:
        app = DartsApp(data_directory=directory)
        errors = []
        app.report_callback_exception = lambda *args: errors.append(args)
        try:
            app.awards_enabled.set(False)
            photo = Path(directory) / 'portrait.jpg'
            Image.new('RGB', (400, 300), '#38bdf8').save(photo)
            alice = app.member_store.save_member('Alice', photo_source=photo)
            bob = app.member_store.save_member('Bob')
            cara = app.member_store.save_member('Cara')
            app.open_members()
            pump(app)
            window = app.member_window
            window.tree.selection_set(alice)
            window.show_selected()
            window.toggle_selected()
            window.tree.selection_set(bob)
            window.show_selected()
            window.toggle_selected()
            pump(app)
            # Exercise the drag handlers against actual tree-row coordinates.
            a_box, b_box = window.tree.bbox(alice), window.tree.bbox(bob)
            window.drag_start(SimpleNamespace(y=a_box[1]+5))
            window.drag_motion(SimpleNamespace(y=b_box[1]+5))
            window.drag_end(None)
            assert list(window.tree.get_children())[:2] == [bob, alice]
            window.start()
            pump(app)
            assert app.roster == [bob, alice]
            assert [p.name for p in app.game.players] == ['Bob', 'Alice']
            app.round_var.set(1)
            app.reset_game('COUNTUP')
            for _ in range(3): app.on_board_hit(25, 1)
            for _ in range(3): app.on_board_hit(1, 1)
            assert app.game.winner.name == 'Bob'
            assert app.member_store.statistics(bob)['awards'] == {'HAT TRICK': 1, 'LOW TON': 1}
            assert app.member_store.statistics(alice)['games'] == 1
            app.update_ui()
            assert app.member_store.statistics(bob)['games'] == 1
            app.do_undo()
            assert app.member_store.statistics(bob)['games'] == 0
            app.on_board_hit(1, 1)
            assert app.member_store.statistics(bob)['games'] == 1
            app.open_members()
            pump(app)
            window = app.member_window
            window.tree.selection_set(bob)
            window.show_selected()
            assert '1 試合 / 1 勝' in window.stats.get('1.0', 'end')
            window.name_var.set('Bobby')
            window.save()
            assert app.game.players[0].name == 'Bobby'
            window.close()
            app.start_roster([None]*4)
            app.geometry('940x720')
            for mode in ('COUNTUP', '301', '501', 'CRICKET', 'CRICKET INVERSE', 'ALL CRICKET', 'HIDDEN CRICKET'):
                app.select_mode(mode)
                pump(app)
                assert app.avatar_label.winfo_ismapped()
                assert app.hidden_bonus_frame.winfo_ismapped() == (mode == 'HIDDEN CRICKET')
                if mode == 'ALL CRICKET':
                    canvas = app.score_view.canvas
                    for label, marks in app._target_widgets.values():
                        assert label.winfo_rooty()+label.winfo_height() <= canvas.winfo_rooty()+canvas.winfo_height()+1
                if mode == 'HIDDEN CRICKET':
                    assert app.hidden_bonus_frame.winfo_rootx()+app.hidden_bonus_frame.winfo_width() <= app.winfo_rootx()+app.winfo_width()
            app.awards_enabled.set(True)
            app.reset_game('CRICKET')
            for raw, mult in ((20,3),(19,1),(18,1)):
                app.on_board_hit(raw,mult)
            assert app.award_player.award == '5 COUNT'
            assert app.game.players[0].awards['5 COUNT'] == 1
            app.do_undo()
            assert app.award_player is None and not app.game.players[0].awards
            app.reset_game('CRICKET')
            for raw in (20,19,18): app.on_board_hit(raw,3)
            assert app.award_player.award == 'WHITE HORSE'
            assert '9 COUNT' in app.award_player.winfo_children()[0].cget('text')
            app.dismiss_award()
            app.reset_game('COUNTUP')
            for _ in range(3): app.on_board_hit(25, 1)
            assert app.award_player and not app.award_player.error
            current = len(app.game.history)
            app.on_board_hit(20, 3)
            assert len(app.game.history) == current
            pump(app, 4100)
            assert app.award_player is None  # Video completes and releases its grab.
            for award in VIDEO_NAMES:
                app.present_award(award, 'Alice')
                pump(app, 120)
                assert app.award_player.index >= 2
                assert app.award_player.error is None
                app.dismiss_award()
                assert app.award_player is None
            original_video = VIDEO_NAMES['HAT TRICK']
            try:
                VIDEO_NAMES['HAT TRICK'] = 'missing-video'
                app.present_award('HAT TRICK', 'Alice')
                assert app.award_player.error is not None
                app.dismiss_award()
            finally:
                VIDEO_NAMES['HAT TRICK'] = original_video
            app.start_roster([alice])
            assert app._avatar_key[0] == alice
            assert not errors, errors
            app.close_app()
            app = DartsApp(data_directory=directory)
            app.awards_enabled.set(False)
            assert app.member_store.get(bob)['name'] == 'Bobby'
            assert app.member_store.statistics(bob)['games'] == 1
            assert [m['id'] for m in app.member_store.list_members()] == [bob, alice, cara]
            app.awards_enabled.set(True)
            app.present_award('HAT TRICK', 'Alice')
            print('PASS: member UI/photo/order/selection, result persistence and undo, 7 modes, ALL CRICKET layout, real video playback/end/skip and restart', flush=True)
        finally:
            app.close_app()


if __name__ == '__main__':
    main()
