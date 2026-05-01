from manim import *
import numpy as np


class HatTrickAward(Scene):
    def construct(self):
        # 1. 背景と色の設定
        self.camera.background_color = "#0a0a0a"
        # より明るい純金に近い色を採用
        bright_gold = "#FFD700"
        deep_gold = "#B8860B"
        bull_red = "#FF0000"
        bull_green = "#00FF00"

        # 2. ターゲット（ブル）の作成
        outer_bull = Circle(radius=1.2, color=bull_green, stroke_width=8)
        inner_bull = Circle(radius=0.4, color=bull_red, fill_opacity=0.8)
        target = VGroup(outer_bull, inner_bull)

        # 3. 称号テキストの作成
        # 文字自体を明るい金色に設定
        title_text = Text("HAT TRICK", weight=BOLD, font_size=96)
        title_text.set_color(bright_gold)
        title_text.shift(UP * 0.5)

        # 4. 枠のデザイン（SurroundingRectangleを使用して綺麗に囲む）
        # 塗りつぶしを0にし、線だけを光らせる
        frame = SurroundingRectangle(
            title_text, color=bright_gold, buff=0.4, stroke_width=6
        )

        # テキストと枠をグループ化
        award_group = VGroup(frame, title_text)
        award_group.set_opacity(0)
        # Z-indexを上げて一番手前に表示
        award_group.set_z_index(10)

        # --- アニメーション開始 ---

        # ターゲットの登場
        self.play(
            Create(outer_bull),
            DrawBorderThenFill(inner_bull),
            run_time=1,
            rate_func=smooth,
        )
        self.wait(0.1)

        # 3本のダーツヒット演出
        for i in range(3):
            ripple = Circle(radius=0.1, color=WHITE).move_to(ORIGIN)
            dart_light = Dot(
                point=UR * 5 + RIGHT * (i * 2), color=bright_gold, radius=0.15
            )

            # 飛来
            self.play(
                dart_light.animate.move_to(ORIGIN), run_time=0.2, rate_func=rush_into
            )

            # 着弾（フラッシュ効果）
            self.remove(dart_light)
            flash = Flash(ORIGIN, color=bright_gold, line_length=0.3, num_lines=12)
            self.add(flash)
            self.play(
                ripple.animate.scale(15).set_stroke(width=0).set_opacity(0),
                inner_bull.animate.set_color(WHITE).scale(1.3),
                run_time=0.2,
            )
            self.play(
                inner_bull.animate.set_color(bull_red).scale(1 / 1.3), run_time=0.2
            )
            self.remove(ripple, flash)

        self.wait(0.2)

        # 5. フィナーレ：金色のHAT TRICK出現
        self.play(FadeOut(target, scale=0.5))

        # テキストを光らせながら出現させる
        self.play(
            award_group.animate.set_opacity(1).scale(1.1),
            Write(title_text, stroke_color=bright_gold),
            Create(frame),
            run_time=1,
        )

        # 仕上げのグロー（輝き）演出：文字の周りに少し光を散らす
        stars = VGroup(
            *[
                Star(color=bright_gold, fill_opacity=0.8)
                .scale(0.05)
                .move_to(
                    title_text.get_center()
                    + [np.random.uniform(-3, 3), np.random.uniform(-1, 1), 0]
                )
                for _ in range(20)
            ]
        )

        self.play(
            LaggedStart(*[FadeIn(s, scale=2) for s in stars], lag_ratio=0.05),
            award_group.animate.scale(1.05),
            run_time=1,
        )
        self.play(FadeOut(stars), run_time=0.5)

        self.wait(2)
