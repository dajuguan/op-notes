# dependencies:
# pip install web3
import os
import json
import time
from dataclasses import dataclass
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from web3.middleware import SignAndSendRawMiddlewareBuilder
import pprint
from enum import Enum

# change it to your optimism path
os.chdir("/root/test_nodes/opup/optimism")

'''devnet
L1_ETH_RPC = "http://localhost:8545"
OP_CHALLENGER = rf"./op-challenger/bin/op-challenger"
DEVNET_ADDRESS_JSON = ".devnet/addresses.json"
with open(DEVNET_ADDRESS_JSON) as f:
    devnetConfig = json.load(f)
DISPUTE_GAME_FACTORY_PROXY = devnetConfig["DisputeGameFactoryProxy"]
DISPUTE_GAME_FACTORY=devnetConfig["DisputeGameFactory"]
PRIV_KEY = "0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6"
'''

'''testnet'''
L1_ETH_RPC = "http://88.99.30.186:8545"
OP_CHALLENGER = rf"./op-challenger/bin/op-challenger"
DISPUTE_GAME_FACTORY_PROXY = "0x4b2215d682208b2a598cb04270f96562f5ab225f"
PRIV_KEY = "xxx"

ABI = open(r"./packages/contracts-bedrock/snapshots/abi/FaultDisputeGame.json").read()
ABI = json.loads(ABI)

w3 = Web3(Web3.HTTPProvider(L1_ETH_RPC))
default_account = Account.from_key(PRIV_KEY)
w3.eth.default_account = default_account
w3.middleware_onion.inject(
    SignAndSendRawMiddlewareBuilder.build(default_account), layer=0
)

class GameStatus(Enum):
    IN_PROGRESS = 0
    CHALLENGER_WINS = 1
    DEFENDER_WINS = 2


@dataclass
class Game:
    GameAddr: str
    GameType: int
    status: GameStatus | str
    Index: int | None = None
    created: str | None = None
    l2BlockNum: int | None = None
    rootClaim: str | None = None
    claimCount: int | None = None

    def __post_init__(self):
        # print("gameAddr:", self.GameAddr)
        self.GameAddr = Web3.to_checksum_address(self.GameAddr)
        self.contract = w3.eth.contract(address=self.GameAddr, abi=ABI)

    def lenClaims(self):
        res = self.contract.functions.claimDataLen().call(
            {"from": default_account.address}
        )
        return res

    def move(self, claim, privKey, parentIndex=None):
        if parentIndex == None:
            parentIndex = self.lenClaims() - 1
        print("parentIndex:", parentIndex)
        if isinstance(claim, str):
            if claim.startswith("0x"):
                claim = claim[2:66]
            if len(claim) < 64:
                claim = claim.rjust(64, "0")
            claim = bytes.fromhex(claim)

        cmd = rf'''{OP_CHALLENGER} move --l1-eth-rpc {L1_ETH_RPC} --game-address {self.GameAddr} --attack --parent-index {parentIndex} --claim {claim} --private-key {privKey}  --mnemonic ""'''
        res = os.popen(cmd).read()
        print(f"counter {parentIndex} move resp:", res)
        # failed using contract call directly
        # disputedClaim = self.claimAt(parentIndex)
        # tx_hash = self.contract.functions.attack(disputedClaim, parentIndex, claim).transact({"from": default_account.address})
        # print("txhash:", tx_hash)
        # tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        # print("tx_receipt:", tx_receipt)

    def claimAt(self, index):
        res = self.contract.functions.claimData(index).call(
            {"from": default_account.address}
        )[4]
        res = res.hex()
        print("claim at:", res)
        return res

    def absolutePrestate(self):
        cmd = rf'cast call {self.GameAddr} "absolutePrestate()"'
        res = os.popen(cmd).read()
        return res

    def list_claims(self):
        cmd = fr"{OP_CHALLENGER} list-claims --l1-eth-rpc {L1_ETH_RPC} --game-address {self.GameAddr}"
        res = os.popen(cmd).read()
        return res

    def gameType(self):
        cmd = rf'cast call {self.GameAddr} "gameType()"'
        res = os.popen(cmd).read()
        return res

    def gameStatus(self):
        cmd = rf'cast call {self.GameAddr} "status()"'
        res = os.popen(cmd).read()
        return GameStatus(int(res.strip(), 16))

    def maxGameDepth(self):
        cmd = rf'cast call {self.GameAddr} "maxGameDepth()"'
        res = os.popen(cmd).read()
        return res

    def attackToMaxDepth(self, privKey):
        print("attacking with false claim")
        # create an false game, and attack with false claim when honest challenger responds
        maxDepth = 50
        depth = 0
        while depth < maxDepth:
            curDepth = self.lenClaims() - 1
            if curDepth == depth + 1:
                print("got op-challenger's move:", self.claimAt(curDepth))
                print("gamestatus:", game.gameStatus())
                randClaim = f"0x{curDepth}"
                self.move(randClaim, privKey)
                depth += 2
        print("reaching max depth, waiting for op-challenger to call step() and resolve()")


def gameCount():
    cmd = rf'cast call {DISPUTE_GAME_FACTORY_PROXY} "gameCount()"'
    res = os.popen(cmd).read()
    res = res.strip()
    return int(res, 16)


def gameAtIndex(index):
    cmd = rf'cast call {DISPUTE_GAME_FACTORY_PROXY} "gameAtIndex(uint256)" {index}'
    res = os.popen(cmd).read()
    res = res.strip()
    gameType, timestamp, gameImpl = int(res[:66], 16), res[66:-40], "0x" + res[-40:]
    cmd_status = rf'cast call {gameImpl} "status()"'
    res = os.popen(cmd_status).read()
    res = int(res.strip(), 16)
    status = GameStatus(res)
    return Game(GameAddr=gameImpl, GameType=gameType, status=status)


def listGames():
    cmd = rf"{OP_CHALLENGER} list-games --l1-eth-rpc {L1_ETH_RPC} --game-factory-address {DISPUTE_GAME_FACTORY_PROXY}"
    print(cmd)
    res = os.popen(cmd).read()
    res = res.strip()
    res = res.split("\n")
    res = res[1:]  # remove the header and last line
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
            gameAddr, gameType, status, idx, created, l2BlockNum, rootClaim, claimsCount
        )
        games.append(game)
    return games

def createGame(OUTPUT_ROOT, L2_BLOCK_NUM, privKey):
    cmd = rf"{OP_CHALLENGER} create-game --l1-eth-rpc {L1_ETH_RPC} --game-factory-address {DISPUTE_GAME_FACTORY_PROXY} --output-root {OUTPUT_ROOT} --l2-block-num {L2_BLOCK_NUM} --private-key {privKey}"
    print(cmd)
    res = os.popen(cmd).read()
    gameAddress = res.strip()[-42:]
    return Game(GameAddr=gameAddress, GameType=0, status=GameStatus.IN_PROGRESS)

games = listGames()
print(len(games))
lastGame = games[-1:]
pprint.pprint(lastGame)
lastGame = lastGame[0]

# create a game with false outputroot
incorrectOutput = "0xffff"
game = createGame(incorrectOutput, lastGame.l2BlockNum, PRIV_KEY)
print("createdDishonestGame:", game)
print(game.absolutePrestate())
print(game.gameType())
print(game.lenClaims())
print(game.gameStatus())
# counter the claims submitted by honest op-challenger with random false claims until maxGameDepth
game.attackToMaxDepth(PRIV_KEY)
