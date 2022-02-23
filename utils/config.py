import os
import sys

from typing import Any, Union, Optional, Dict

from utils.brownie_prelude import *

from brownie import network, accounts
from brownie.utils import color
from brownie.network.account import Account, LocalAccount

def network_name() -> Optional[str]:
    if network.show_active() != None:
        return network.show_active()
    cli_args = sys.argv[1:]
    net_ind = next((cli_args.index(arg) for arg in cli_args if arg == '--network'), len(cli_args))

    net_name = None
    if net_ind != len(cli_args):
        net_name = cli_args[net_ind+1]

    return net_name

if network_name() in ("goerli", "goerli-fork"):
    print(f'Using {color("cyan")}config_goerli.py{color} addresses')
    from utils.config_goerli import *
else:
    print(f'Using {color("magenta")}config_mainnet.py{color} addresses')
    from utils.config_mainnet import *


def get_is_live() -> bool:
    return network_name() != 'development'

def prompt_bool() -> Optional[bool]:
    choice = input().lower()
    if choice in {'yes', 'y'}:
        return True
    elif choice in {'no', 'n'}:
        return False
    else:
        sys.stdout.write("Please respond with 'yes' or 'no'")

def get_config_params() -> Dict[str, str]:
    ret = []
    if network_name in ("goerli", "goerli-fork"):
        import utils.config_goerli
        ret = {x:globals()[x] for x in dir(utils.config_goerli) if not x.startswith("__")}
    else:
        import utils.config_mainnet
        ret = {x:globals()[x] for x in dir(utils.config_mainnet) if not x.startswith("__")}
    return ret

class ContractsLazyLoader:
    @property
    def lido(self) -> interface.Lido:
        return interface.Lido(lido_dao_steth_address)

    @property
    def oracle(self) -> interface.LidoOracle:
        return interface.LidoOracle(lido_dao_oracle_address)

    @property
    def voting(self) -> interface.Voting:
        return interface.Voting(lido_dao_voting_address)

    @property
    def acl(self) -> interface.ACL:
        return interface.ACL(lido_dao_acl_address)

    @property
    def composite_post_rebase_beacon_receiver(self) -> interface.CompositePostRebaseBeaconReceiver:
        return interface.CompositePostRebaseBeaconReceiver(composite_post_rebase_beacon_receiver_address)

    @property
    def self_owned_steth_burner(self) -> interface.SelfOwnedStETHBurner:
        return interface.SelfOwnedStETHBurner(self_owned_steth_burner_address)


def __getattr__(name: str) -> Any:
    if name == "contracts":
        return ContractsLazyLoader()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
