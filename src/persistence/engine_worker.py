import json
import sys

import chess
import chess.engine


def analyze_positions(payload):
    stockfish_path = payload["stockfish_path"]
    movetime_ms = int(payload["movetime_ms"])
    positions = payload["positions"]

    limit = chess.engine.Limit(time=movetime_ms / 1000)
    results = []
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        for fen in positions:
            board = chess.Board(fen)
            info = engine.analyse(board, limit)
            score = info["score"].white()
            results.append({
                "eval_cp": score.score(mate_score=100000),
                "eval_mate": score.mate(),
            })
    return results


def main():
    payload = json.load(sys.stdin)
    json.dump({"results": analyze_positions(payload)}, sys.stdout)


if __name__ == "__main__":
    main()
