"""Original movie themes inspired by arcade darts award conventions."""
# name: filename, colour, visual theme, display title, subtitle
AWARD_THEMES = {
    'ONE BULL': ('one_bull', (80, 239, 132), 'grid', 'NICE ONE!', 'ONE BULL / KEEP THE RHYTHM'),
    'LOW TON': ('low_ton', (82, 127, 255), 'cubes', 'LOW TON', '100 - 150 / INTO THE ZONE'),
    'HIGH TON': ('high_ton', (255, 205, 67), 'tower', 'HIGH TON', '151 - 180 / RAISE THE LIMIT'),
    'HAT TRICK': ('hat_trick', (255, 92, 108), 'bull', 'HAT TRICK', 'THREE BULLS / LOCKED ON'),
    'THREE IN A BED': ('three_in_a_bed', (219, 106, 255), 'lanes', 'THREE IN A BED', 'SAME NUMBER. SAME RING. THREE TIMES.'),
    'TON 80': ('ton_80', (255, 127, 56), 'maximum', 'TON 80', 'T20 / T20 / T20'),
    'THREE IN THE BLACK': ('three_in_the_black', (232, 237, 247), 'tunnel', 'THREE IN THE BLACK', 'THREE DOUBLE BULLS / DEAD CENTRE'),
    'WHITE HORSE': ('white_horse', (101, 218, 255), 'horse', 'WHITE HORSE', 'THREE TRIPLES / THREE DIFFERENT TARGETS'),
    'HIGH OUT': ('high_out', (255, 108, 190), 'checkout', 'HIGH OUT', '100+ CHECKOUT / FINISH IN STYLE'),
    'WINNER': ('winner', (255, 215, 96), 'crown', 'WINNER', 'OWN THE OCHE.'),
}
for count, accent in [(5, (95, 239, 172)), (6, (66, 221, 246)), (7, (105, 155, 255)),
                      (8, (205, 122, 255)), (9, (255, 206, 74))]:
    AWARD_THEMES[f'{count} COUNT'] = (f'{count}_count', accent, 'count', f'{count} COUNT',
                                      f'{count} MARK ROUND / CRICKET')
VIDEO_NAMES = {name: theme[0] for name, theme in AWARD_THEMES.items()}
