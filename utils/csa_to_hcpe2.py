from cshogi import *
from cshogi import CSA
import numpy as np
import os
import glob
import argparse

HuffmanCodedPosAndEval2 = np.dtype([
    ('hcp', dtypeHcp),
    ('eval', dtypeEval),
    ('bestMove16', dtypeMove16),
    ('result', np.uint8),
    ('dummy', np.uint8),
    ])

parser = argparse.ArgumentParser()
parser.add_argument('csa_dir')
parser.add_argument('hcpe')
parser.add_argument('--out_maxmove', action='store_true')
parser.add_argument('--filter_moves', type=int, default=50)
parser.add_argument('--filter_rating', type=int, default=3500)
args = parser.parse_args()

filter_moves = args.filter_moves
filter_rating = args.filter_rating

csa_file_list = glob.glob(os.path.join(args.csa_dir, '**', '*.csa'), recursive=True)

hcpes = np.zeros(513, HuffmanCodedPosAndEval2)

f = open(args.hcpe, 'wb')

board = Board()
kif_num = 0
position_num = 0
for filepath in csa_file_list:
    for kif in CSA.Parser.parse_file(filepath):
        endgame = kif.endgame
        if endgame not in ('%TORYO', '%SENNICHITE', '%KACHI', '%JISHOGI') or len(kif.moves) < filter_moves:
            continue
        if filter_rating > 0 and (kif.ratings[0] < filter_rating and kif.ratings[1] < filter_rating):
            continue

        # 評価値がない棋譜は除く
        if len(kif.moves) != len(kif.scores):
            continue

        if endgame == '%JISHOGI':
            if not args.out_maxmove:
                continue

        board.set_sfen(kif.sfen)
        try:
            for i, (move, score) in enumerate(zip(kif.moves, kif.scores)):
                assert board.is_legal(move)
                hcpe = hcpes[i]
                board.to_hcp(hcpe['hcp'])
                assert abs(score) <= 100000
                score = min(32767, max(score, -32767))
                hcpe['eval'] = score if board.turn == BLACK else -score
                hcpe['bestMove16'] = move16(move)
                hcpe['result'] = kif.win
                board.push(move)
        except:
            print(f'skip {filepath}:{i}:{move_to_usi(move)}:{score}')
            continue

        move_num = len(kif.moves)
        assert move_num == i + 1

        # 評価値がない棋譜は除く
        if (hcpes[:move_num]['eval'] == 0).sum() >= move_num // 2:
            continue

        if endgame == '%SENNICHITE':
            hcpes[:move_num]['result'] += 4
        elif endgame == '%KACHI':
            hcpes[:move_num]['result'] += 8
        elif endgame == '%JISHOGI':
            hcpes[:move_num]['result'] += 16

        hcpes[:move_num].tofile(f)

        kif_num += 1
        position_num += move_num

print('kif_num', kif_num)
print('position_num', position_num)
