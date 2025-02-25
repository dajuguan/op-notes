#!/bin/python3
# dependencies: cast, op-challenger
import argparse
import os
from dataclasses import dataclass
from enum import Enum
import pprint

OP_CHALLENGER = rf"/root/test_nodes/opup/optimism/op-challenger/bin/op-challenger"
L1_RPC = "http://88.99.30.186:8545"
DISPUTE_GAME_FACTORY_PROXY = "0x4b2215d682208b2a598cb04270f96562f5ab225f"

class GameStatus(Enum):
    IN_PROGRESS = 0
    CHALLENGER_WINS = 1
    DEFENDER_WINS = 2


@dataclass
class Game:
    gameAddr: str
    status: GameStatus | str = GameStatus.IN_PROGRESS
    gameType: int = 0  # 0:cannon, 1:permissoned, 255:fastgame
    index: int | None = None
    created: str | None = None
    l2BlockNum: int | None = None
    rootClaim: str | None = None
    claimsCount: int | None = None
    prestate: str | None = None

    def __post_init__(self):
        if type(self.status) == str:
            if "IN_PROGRESS" in self.status:
                self.status = GameStatus.IN_PROGRESS
            if "CHALLENGER_WINS" in self.status:
                self.status = GameStatus.CHALLENGER_WINS
            if "DEFENDER_WINS" in self.status:
                self.status = GameStatus.DEFENDER_WINS
        self.setAbsolutePrestate()

    def lenClaims(self):
        cmd = rf'cast call {self.gameAddr} "claimDataLen()" --rpc-url {L1_RPC}'
        res = os.popen(cmd).read()
        res = res.strip()
        return int(res, 16)

    def setAbsolutePrestate(self):
        cmd = rf'cast call {self.gameAddr} "absolutePrestate()" --rpc-url {L1_RPC}'
        res = os.popen(cmd).read()
        res = res.strip()
        self.prestate = res

    def move(self, claim, pk, parentIndex=None):
        if parentIndex == None:
            parentIndex = self.lenClaims() - 1

        cmd = rf'''{OP_CHALLENGER} move --l1-eth-rpc {L1_RPC} --game-address {self.gameAddr} --attack --parent-index {parentIndex} --claim {claim} --private-key {pk}  --mnemonic ""'''
        res = os.popen(cmd).read()
        print(f"counter {parentIndex} with claim:", claim)
        print(f"counter {parentIndex} move resp:", res)

    def claimAt(self, index):
        cmd = rf'cast call {self.gameAddr} "claimData(uint256)" {index} --rpc-url {L1_RPC}'
        res = os.popen(cmd).read()
        res = res.strip()[2:]
        return {
            "parentIndex": res[:64],
            "counteredBy": res[64 : 64 * 2],
            "claimant": res[64 * 2 : 64 * 3],
            # bond:res[64*3:64*4],
            "claim": res[64 * 4 : 64 * 5],
            # position:res[64*5:64*6],
            # clock:res[64*6:64*7]
        }

    def absolutePrestate(self):
        cmd = rf'cast call {self.gameAddr} "absolutePrestate()" --rpc-url {L1_RPC}'
        res = os.popen(cmd).read()
        return res.strip()

    def list_claims(self):
        cmd = rf"{OP_CHALLENGER} list-claims --l1-eth-rpc {L1_RPC} --game-address {self.gameAddr}"
        res = os.popen(cmd).read()
        return res.strip()

    def gameType(self):
        cmd = rf'cast call {self.gameAddr} "gameType()" --rpc-url {L1_RPC}'
        res = os.popen(cmd).read()
        return res.strip()

    def gameStatus(self):
        cmd = rf'cast call {self.gameAddr} "status()" --rpc-url {L1_RPC}'
        res = os.popen(cmd).read()
        return GameStatus(int(res.strip(), 16))

    def maxGameDepth(self):
        cmd = rf'cast call {self.gameAddr} "maxGameDepth()" --rpc-url {L1_RPC}'
        res = os.popen(cmd).read()
        return res.strip()

    def attackToMaxDepth(self, parent_index, maxdepth, pk):
        # create an false game, and attack with false claim when honest challenger responds
        maxDepth = maxdepth
        depth = parent_index - 1
        while depth < maxDepth:
            curDepth = self.lenClaims() - 1
            if curDepth == depth + 1:
                print("got op-challenger's move:", self.claimAt(curDepth))
                # the first 2 hex must be 01 or 02 to meet the _verifyExecBisectionRoot requirements
                randClaim = f"0x012222222222222222222222222221022222222222222222222222222222{curDepth+10}01"
                self.move(randClaim, pk)
                depth += 2
        print(
            """Max depth reached. Waiting for op-challenger (always honest) to:
        1. Call step() and resolve() if rootClaim is honest.
        2. Call resolve() (it's the dishonest actor's job to call step(), which will always revert) if rootClaim is dishonest.
        """
        )


def list_games(status, l1_rpc, fdg_addr, **kargs):
    cmd = rf"{OP_CHALLENGER} list-games --l1-eth-rpc {l1_rpc} --game-factory-address {fdg_addr}"
    res = os.popen(cmd).read()
    res = res.strip()
    res = res.split("\n")
    res = res[1:]  # remove the header fields and last line
    games = []
    for line in res:
        idx = line[:4].strip()
        gameAddr = line[4 : 4 + 43].strip()
        gameType = line[4 + 43 : 4 + 43 + 5].strip()
        created = line[4 + 43 + 5 : 4 + 43 + 5 + 21].strip()
        l2BlockNum = line[4 + 43 + 5 + 21 : 4 + 43 + 5 + 22 + 15].strip()
        rootClaim = line[4 + 43 + 5 + 22 + 15 : 4 + 43 + 5 + 22 + 15 + 66].strip()
        claimsCount = line[
            4 + 43 + 5 + 22 + 15 + 67 : 4 + 43 + 5 + 22 + 15 + 67 + 6
        ].strip()
        status = line[
            4 + 43 + 5 + 22 + 15 + 67 + 7 : 4 + 43 + 5 + 22 + 15 + 67 + 7 + 14
        ].strip()
        game = Game(
            gameAddr=gameAddr,
            gameType=gameType,
            status=status,
            index=idx,
            created=created,
            l2BlockNum=l2BlockNum,
            rootClaim=rootClaim,
            claimsCount=claimsCount,
            prestate=None,
        )
        games.append(game)
    if status != 0:
        games = list(filter(lambda x: x.status == status, games))

    pprint.pprint(games)


def attack_game_to_max_depth(game_addr, parent_index, maxdepth, pk, **kargs):
    game = Game(gameAddr=game_addr)
    game.attackToMaxDepth(parent_index, maxdepth, pk)

def list_claims(game_addr, **kargs):
    game = Game(gameAddr=game_addr)
    claims = game.list_claims()
    print(claims)


def main():
    global L1_RPC, OP_CHALLENGER
    parser = argparse.ArgumentParser(description="Game management script")
    parser.add_argument("--l1-rpc", type=str, default=L1_RPC, help="l1 EL rpc url")
    parser.add_argument(
        "--fdg-addr",
        type=str,
        default=DISPUTE_GAME_FACTORY_PROXY,
        help="dispute game factory address",
    )
    parser.add_argument(
        "--binpath",
        type=str,
        default=OP_CHALLENGER,
        help="op-challenger absolute binary path",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Subparser for the list-games command
    parser_list = subparsers.add_parser("list-games", help="List all games")
    parser_list.add_argument(
        "--status",
        type=int,
        default=1,
        choices=[0, 1, 2, 3],
        help="game status, 0:all, 1:in-progress, 2:challenger-wins, 3:defender-wins",
    )
    parser_list.set_defaults(func=list_games)

    # Subparser for the attack command
    parser_attack = subparsers.add_parser(
        "attack-all",
        help="Attack a game for every counter claim by honest challenger to maxDepth with random claim values",
    )
    parser_attack.add_argument(
        "--game-addr",
        type=str,
        required=True,
        help="contract address of the game to attack, eg:0x11",
    )
    parser_attack.add_argument(
        "--pk", type=str, required=True, help="private key, eg:0x11"
    )
    parser_attack.add_argument(
        "--parent-index", type=int, default=0, help="parent index to start attacking from, usually claimsCount-1"
    )
    parser_attack.add_argument(
        "--maxdepth", type=int, default=50, help="maxGameDepth of the attack ending"
    )
    parser_attack.set_defaults(func=attack_game_to_max_depth)


    # Subparser for the list-claims command
    parser_claims = subparsers.add_parser(
        "list-claims",
        help="List claims for a given game",
    )
    parser_claims.add_argument(
        "--game-addr",
        type=str,
        required=True,
        help="contract address of the game to attack, eg:0x11",
    )
    parser_claims.set_defaults(func=list_claims)

    args = parser.parse_args()
    if args.l1_rpc:
        L1_RPC = args.l1_rpc
    if args.binpath:
        OP_CHALLENGER = args.binpath
    print("args==:", args)
    if args.command:
        args.func(**vars(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
