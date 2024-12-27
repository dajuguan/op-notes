# dependencies:
# pip install web3 
import os
import json
from dataclasses import dataclass
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from web3.middleware import SignAndSendRawMiddlewareBuilder

# change it to your optimism path
os.chdir("/root/test_nodes/opup/optimism")

L1_ETH_RPC = "http://localhost:8545"
OP_CHALLENGER = rf"./op-challenger/bin/op-challenger"
DEVNET_ADDRESS_JSON = ".devnet/addresses.json"
with open(DEVNET_ADDRESS_JSON) as f:
    devnetConfig = json.load(f)
DISPUTE_GAME_FACTORY_PROXY = devnetConfig["DisputeGameFactoryProxy"]
PRIV_KEY = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
ABI = open(r"./packages/contracts-bedrock/snapshots/abi/FaultDisputeGame.json").read()
ABI = json.loads(ABI)

w3 = Web3(Web3.HTTPProvider(L1_ETH_RPC))
default_account = Account.from_key(PRIV_KEY)
w3.eth.default_account = default_account
w3.middleware_onion.inject(
    SignAndSendRawMiddlewareBuilder.build(default_account), layer=0
)


@dataclass
class Game:
    GameAddr: str
    GameType: int
    status: str
    Index: int | None = None
    created: str | None = None
    l2BlockNum: int | None = None
    rootClaim: str | None = None
    claimCount: int | None = None

    def __post_init__(self):
        print("gameAddr:", self.GameAddr)
        self.GameAddr = Web3.to_checksum_address(self.GameAddr)
        self.contract = w3.eth.contract(address=self.GameAddr, abi=ABI)

    def lenClaims(self):
        res = self.contract.functions.claimDataLen().call(
            {"from": default_account.address}
        )
        print("len claims:", res)
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

        disputedClaim = self.claimAt(parentIndex)
        cmd = rf'''{OP_CHALLENGER} move --l1-eth-rpc {L1_ETH_RPC} --game-address {self.GameAddr} --attack --parent-index {parentIndex} --claim {claim} --private-key {privKey}  --mnemonic ""'''
        res = os.popen(cmd).read()
        print("move resp:", res)
        # failed using contract call directly
        # tx_hash = self.contract.functions.attack(disputedClaim, parentIndex, claim).transact({"from": default_account.address})
        # print("txhash:", tx_hash)
        # tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        # print("tx_receipt:", tx_receipt)

    def claimAt(self, index):
        return self.contract.functions.claimData(index).call(
            {"from": default_account.address}
        )[4]


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
    status = ""
    if res == 0:
        status = "In Progress"
    elif res == 1:
        status = "Challenger Won"
    else:
        status = "Defender Won"
    print("game status:", status)
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
        idx = line[:4]
        gameAddr = line[4 : 4 + 43].strip()
        gameType = line[4 + 43 : 4 + 43 + 4].strip()
        created = line[4 + 43 + 5 : 4 + 43 + 5 + 21].strip()
        l2BlockNum = line[4 + 43 + 5 + 22 : 4 + 43 + 5 + 22 + 14].strip()
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


# games = listGames()
# print(games[-1:])
gameCount = gameCount()
print("game at Index:", gameCount)
index = gameCount - 1
index = 5
game = gameAtIndex(index)
claim = "0xffb026F67DA0869EB3ABB190cB7F015CE0925CdF"
game.move(claim, PRIV_KEY)
