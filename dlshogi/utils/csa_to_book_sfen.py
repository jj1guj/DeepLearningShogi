from cshogi import *
import argparse
import os
import sys
import glob
import numpy as np
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument('dir')
parser.add_argument('book_sfen')
parser.add_argument('--limit_moves', type=int, default=80)
parser.add_argument('--limit_entries', type=int, default=50)
parser.add_argument('--filter_rating', type=int)
parser.add_argument('--only_winner', action='store_true')
parser.add_argument('--winner')
args = parser.parse_args()

csa_file_list = glob.glob(os.path.join(args.dir, '**', '*.csa'), recursive=True)

board = Board()
parser = Parser()
num_games = 0
bookdic = {}
historydic = {}
for filepath in csa_file_list:
    try:
        parser.parse_csa_file(filepath)
        if args.filter_rating:
            if parser.ratings[0] < args.filter_rating or parser.ratings[1] < args.filter_rating:
                continue
        if args.only_winner:
            if parser.win == 0:
                continue
            if args.winner and args.winner not in parser.names[parser.win - 1]:
                continue
        board.set_sfen(parser.sfen)
        if parser.sfen != "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1":
            print(parser.sfen)
        # history = board.history
        # print("startpos moves {}".format(" ".join(history)))
        assert board.is_ok(), "{}:{}".format(filepath, parser.sfen)
        for i, move in enumerate(parser.moves):
            if i >= args.limit_moves:
                break

            if not board.is_legal(move):
                print("skip {}:{}:{}".format(filepath, i, move_to_usi(move)))
                break

            if args.only_winner and board.turn != parser.win - 1:
                board.push(move)
                continue

            key = board.book_key()
            if key not in bookdic:
                bookdic[key] = defaultdict(int)
                historydic[key] = defaultdict(list)
            bookdic[key][move16(move)] += 1
            historydic[key] = board.history
            # history = board.history
            # history = [move_to_usi(i) for i in history]
            # print("startpos moves {}".format(" ".join(history)))

            board.push(move)

        num_games += 1
    except Exception as e:
        print("skip {} {}".format(filepath, e))

# 閾値以下のエントリを削除
num_positions = 0
num_entries = 0
for key in list(bookdic.keys()):
    entries = bookdic[key]
    sum_count = 0
    for count in entries.values():
        sum_count += count

    if sum_count <= args.limit_entries:
        del bookdic[key]
        del historydic[key]
        continue

    num_positions += 1
    num_entries += len(entries)

print(f"games : {num_games}")
print(f"positions : {num_positions}")
print(f'entries : {num_entries}')

# 保存
# book_entries = np.empty(num_entries, dtype=BookEntry)
# i = 0
book_history = []
for key in sorted(bookdic.keys()):
    history = historydic[key]
    history = [move_to_usi(i) for i in history]
    book_history.append("startpos moves {}\n".format(" ".join(history)))

with open(args.book_sfen, "w") as f:
    f.writelines(book_history)
#     entries = bookdic[key]
#     for move, count in entries.items():
#         book_entries[i] = key, move, count, 0
#         i += 1
# assert i == num_entries
# book_entries.tofile(args.book)