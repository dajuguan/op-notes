
## Sync logs
```
# EL
 Forkchoice requested sync to new head    number=7,553,888 hash=2a54ee..6c2561 finalized=7,553,827
sync beacon chain headers (from CL by engine API)
INFO [01-23|12:53:53.615] Syncing beacon headers                   downloaded=2,396,672 left=3,874,341 eta=6m18.456s (from EL peers)
...
INFO [01-23|12:57:31.527] Syncing: state download in progress      synced=0.65%  state=578.53MiB accounts=267,042@59.50MiB slots=1,662,033@366.20MiB codes=35104@152.83MiB eta=5h32m8.943s (from EL peers)
INFO [01-23|12:57:31.594] Syncing: chain download in progress      synced=25.18% chain=1.10GiB    headers=1,945,600@549.94MiB bodies=1,902,028@455.26MiB receipts=1,902,028@123.73MiB eta=6m26.981s (from EL peers)

CL:
[2025-01-23 12:53:00]  INFO blockchain: Called fork choice updated with optimistic block finalizedPayloadBlockHash=0x64509b99fd97 headPayloadBlockHash=0x8d7f52a6d313 headSlot=6825265 (engine API)
[2025-01-23 12:53:00]  INFO blockchain: Synced new block block=0x7979e0e7... epoch=213289 finalizedEpoch=213287 finalizedRoot=0x12fdbffb... slot=6825265
[2025-01-23 12:53:00]  INFO blockchain: Finished applying state transition attestations=1 kzgCommitmentCount=5 payloadHash=0x8d7f52a6d313 slot=6825265 syncBitsCount=499 txCount=123
```

## CL and EL
The Merge was the implementation of the Bellatrix consensus (layer) specs, the Paris execution (layer) specs, and the Engine API.

Bellatrix: https://github.com/ethereum/consensus-specs/tree/dev/specs/bellatrix

Paris: https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/paris.md

Paris mainly consists of EIP-3675.
The interaction between the consensus layer and execution layer is specified by the Engine API: https://github.com/ethereum/execution-apis/tree/main/src/engine


## CL
Beacon node data structures:
- [BeaconBlock and BeaconState](https://eth2book.info/capella/part3/containers/blocks/)

## Engine API
- [Geth Engine API](https://github.com/ethereum/go-ethereum/blob/9b68875d68b409eb2efdb68a4b623aaacc10a5b6/eth/catalyst/api.go)
- [Engine API Spec](https://github.com/ethereum/execution-apis/blob/main/src/engine/shanghai.md)
- [Engine API: A Visual Guide](https://hackmd.io/@danielrachi/engine_api#EL-is-syncing)
- [Node architecture](https://ethereum.org/en/developers/docs/nodes-and-clients/node-architecture/)
- [engine_forkchoiceUpdatedWithWitnessV1: Verkle tree for statelessness](https://ethereum.org/en/roadmap/verkle-trees/#statelessness)

### EL Sync
- state download
    - [state, accounts, slots, code](https://github.com/ethereum/go-ethereum/blob/5adc3148179744f54bf13ae1b60c18f12be0df5c/eth/protocols/snap/sync.go#L381)
- chain download
    - [peers rpc](https://github.com/ethereum/go-ethereum/blob/14eb8967be7acc54c5dc9a416151ac45c01251b6/eth/protocols/eth/peer.go#L322
    ) and [handler](https://github.com/ethereum/go-ethereum/blob/9045b79bc266a547c5b9e923e8db4286e74c240c/eth/protocols/eth/handler.go#L162) 

# Refs:
- [beacon chain api](https://ethereum.github.io/beacon-APIs/#/Rewards)
- [ethereum docs nodes and clients](https://ethereum.org/en/developers/docs/nodes-and-clients/node-architecture/)
- [geth logs](https://geth.ethereum.org/docs/fundamentals/logs)
- [reorg](https://barnabe.substack.com/p/pos-ethereum-reorg?open=false#%C2%A7proof-of-stake-in-ethereum)
- [safe head](https://medium.com/imtoken/safe-head-part-1-14071f14016b)
- [Sync in: Booby Trapping the Ethereum Blockchain](https://www.paradigm.xyz/2021/05/booby-trapping-the-ethereum-blockchain)