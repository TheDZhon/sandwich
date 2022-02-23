# Sandwich

Evaluate sandwich possibilities on top of the Lido oracle reports.

### Environment variables setup

Despite the chosen network you always need to set the following var:
```bash
export WEB3_INFURA_PROJECT_ID=<infura_api_key>
```
``

To run tests with a contract name resolution guided by the Etherscan you should provide the etherscan API token:
```bash
export ETHERSCAN_TOKEN=<etherscan_api_key>
```

### Command-line arguments requirements

Always pass network name explicitly with `--network {network-name}` brownie command-line arguments for both vote and tests scripts.

To reveal a full test output pass the `-s` flag when running test scripts with `brownie test`
