## find latest releases of compatible op-geth and op-node(optimism)
https://github.com/ethereum-optimism/op-geth/releases

## Creating Your Own L2 Rollup Testnet
following [the create-l2-rollup tutorial](https://docs.optimism.io/builders/chain-operators/tutorials/create-l2-rollup) up to the [#deploy-the-create2-factory-optional part](https://docs.optimism.io/builders/chain-operators/tutorials/create-l2-rollup#deploy-the-create2-factory-optional)
> pnpm install is not needed in optimism v1.9.1
## only run local l1 CL,EL
https://docs.optimism.io/chain/testing/dev-node#operations
```
cd ~/optimism/ops-bedrock
docker compose up -d l1 l1-bn l1-vc
cast chain-id
```

change `.envrc` with:
```
# L1 chain information
export L1_CHAIN_ID=900
export L1_BLOCK_TIME=6

# L2 chain information
export L2_CHAIN_ID=901
export L2_BLOCK_TIME=2

export L1_RPC_KIND=debug_geth
export L1_RPC_URL=http://localhost:8545
export PRIVATE_KEY=xx  # ~/optimism/ops-bedrock/op-batcher-key.txt
```

## Deploy contracts
https://docs.optimism.io/builders/chain-operators/deploy/smart-contracts
```
# difference with the above doc: scripts/Deploy.s.sol:Deploy => scripts/deploy/Deploy.s.sol:Deploy
cd packages/contracts-bedrock
DEPLOYMENT_OUTFILE=deployments/artifact.json \
DEPLOY_CONFIG_PATH=deploy-config/getting-started.json \
  forge script scripts/Deploy.s.sol:Deploy \
  --broadcast --private-key $PRIVATE_KEY \ 
  --rpc-url $ETH_RPC_URL
```

## contract depolyment & genesis creation
https://docs.optimism.io/builders/chain-operators/deploy/genesis
- l2geth: genesis file
  - allocs: initialize address = > account {balance, code, nonce}
  - fork numbers
 
```
CONTRACT_ADDRESSES_PATH=deployments/artifact.json \
DEPLOY_CONFIG_PATH=deploy-config/getting-started.json \
STATE_DUMP_PATH=mynet-l2-allocs.json \
  forge script scripts/L2Genesis.s.sol:L2Genesis \
  --sig 'runWithStateDump()'
```

- op-node: rollup config
```
 ../../op-node/bin/op-node genesis l2 \
  --deploy-config=deploy-config/getting-started.json \
  --l1-deployments=deployments/artifact.json \
  --l2-allocs=mynet-l2-allocs.json \
  --outfile.l2=l2_config.json \
  --outfile.rollup=rollup_config.json \
  --l1-rpc=$L1_RPC_URL
```

## run op-geth
https://docs.optimism.io/builders/chain-operators/tutorials/create-l2-rollup#initialize-op-geth
```
cd ~/op-geth
openssl rand -hex 32 > jwt.txt
cp jwt.txt ../optimism/op-node/
#  difference with the above doc: add --state.scheme=hash
build/bin/geth init --datadir=datadir  --state.scheme=hash ../optimism/packages/contracts-bedrock/l2_config.json
./build/bin/geth \
  --datadir ./datadir \
  --http \
  --http.corsdomain="*" \
  --http.vhosts="*" \
  --http.addr=0.0.0.0 \
  --http.api=web3,debug,eth,txpool,net,engine \
  --ws \
  --ws.addr=0.0.0.0 \
  --ws.port=8746 \ 
  --ws.origins="*" \
  --ws.api=debug,eth,txpool,net,engine \
  --syncmode=full \
  --gcmode=archive \
  --nodiscover \
  --maxpeers=0 \
  --networkid=901 \ 
  --authrpc.vhosts="*" \
  --authrpc.addr=0.0.0.0 \
  --authrpc.port=8751 \  # changed
  --authrpc.jwtsecret=./jwt.txt \
  --rollup.disabletxpoolgossip=true \
  --http.port=8745
```
> change `--ws.port` and `--authrpc.port` to avoid port conflicting, change `--networkid` to `.envrc` configured `L2_CHAIN_ID`
## run op-node
```
cd ~/optimism
cp packages/contracts-bedrock/rollup_config.json op-node/rollup.json
# difference with the above doc: add `--l1.beacon`, change `--l2`
./bin/op-node \
  --l2=http://localhost:8751  \
  --l2.jwt-secret=./jwt.txt \
  --sequencer.enabled \
  --sequencer.l1-confs=5 \
  --verifier.l1-confs=4 \
  --rollup.config=./rollup.json \
  --rpc.addr=0.0.0.0 \
  --p2p.disable \
  --rpc.enable-admin \
  --p2p.sequencer.key=$GS_SEQUENCER_PRIVATE_KEY \
  --l1=$L1_RPC_URL \
  --l1.rpckind=$L1_RPC_KIND \
  --l1.beacon=http://localhost:5052 
```


