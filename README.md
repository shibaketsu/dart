# Python Darts Master

ダーツゲームのシミュレーション及びアニメーション生成プロジェクト

## 概要

このプロジェクトは、Pythonで実装されたダーツゲームアプリケーションです。tkinterを使用したGUIと、Manimライブラリを使用したアニメーション生成機能を備えています。

## 機能

- **ダーツゲームシミュレータ**：TkinterベースのダーツボードUI
- **複数のゲームモード**：COUNTUP、ダブルアウトなど複数のモードに対応
- **クリケットゲーム対応**：クリケットゲームのターゲット設定
- **HIDDEN CRICKET**：7つのターゲットをランダム抽選し、当たるまで非公開にするモード
- **ダブルアウト表**：高スコア達成時の推奨ダーツ配置を提示
- **アニメーション生成**：Manimを使用した「Hat Trick Award」などのアニメーション

## プロジェクト構成

```
.
├── main.py              # メインアプリケーション（Tkinter UI）
├── models.py            # ゲームロジック・データモデル
├── ui.py                # UIコンポーネント（ダーツボード表示など）
├── config.py            # 設定・定数（ダーツボード配置、ゲーム設定など）
├── animation.py         # Manimアニメーション生成スクリプト
├── media/               # メディアファイル格納
│   ├── images/          # 画像ファイル
│   │   └── animation/   # アニメーション用画像
│   ├── texts/           # テキストファイル
│   └── videos/          # 生成動画
│       └── animation/   # アニメーション生成動画
└── README.md            # このファイル
```

## 必要要件

- Python 3.8以上
- tkinter（Pythonに付属）
- manim（アニメーション生成用）
- tkmacosx（Mac環境でのUI改善用、オプション）

## インストール

```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate  # Mac/Linux
# または
.venv\Scripts\activate  # Windows

# 依存パッケージのインストール
pip install manim
pip install tkmacosx  # Mac環境の場合
```

## 使用方法

### ダーツゲームアプリの起動

```bash
python main.py
```

Tkinterベースのダーツボード表示ウィンドウが起動します。

### アニメーション生成

```bash
manim -pl animation.py HatTrickAward
```

「Hat Trick Award」アニメーションが生成されます。

## ゲーム設定

`config.py`で以下の設定をカスタマイズ可能：

- **SEGMENTS**：ダーツボードのセグメント配置（時計回り）
- **CRICKET_TARGETS**：クリケットゲームのターゲット
- **CRICKET_TARGET_POOL**：HIDDEN CRICKETで使う候補数字
- **HIDDEN_CRICKET_TARGET_COUNT**：HIDDEN CRICKETで使う数字の数
- **DOUBLE_OUT_TABLE**：ダブルアウト表の推奨配置

HIDDEN CRICKETでは、ゲーム開始時に1〜20とBULLの候補から7つを抽選します。最初にその数字を当てたプレイヤーには、事前に選んだ1本または2本のボーナスが追加されます。

## ライセンス

未指定

## 作者

Dart Master Dev Team
