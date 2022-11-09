import pytest
import os

from typing import Optional

from brownie import chain, ZERO_ADDRESS

from utils.config import *

@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass

@pytest.fixture(scope='module')
def dao_voting(interface):
    return interface.Voting(lido_dao_voting_address)

@pytest.fixture(scope='module')
def lido(interface):
    return interface.Lido(lido_dao_steth_address)

@pytest.fixture(scope="module")
def acl(interface):
    return interface.ACL(lido_dao_acl_address)

@pytest.fixture(scope="module")
def oracle(interface, dao_voting):
    oracle = interface.LidoOracle(lido_dao_oracle)

    oracle.setAllowedBeaconBalanceAnnualRelativeIncrease(2800, {'from': dao_voting.address}) # TODO: remove this temporary hack
    oracle.reportBeacon(159300, 4700878413390971, 141433, {'from': p2p_oracle_address}) # TODO: remove this temporary hack

    vault = accounts.at(lido_dao_execution_layer_rewards_vault, force=True)
    vault.transfer(ZERO_ADDRESS, vault.balance(), gas_price=0)
    return oracle

@pytest.fixture(scope="module")
def composite_post_rebase_beacon_receiver(interface):
    return interface.CompositePostRebaseBeaconReceiver(
        lido_dao_composite_post_rebase_beacon_receiver
    )

@pytest.fixture(scope="module")
def self_owned_steth_burner(interface):
    return interface.SelfOwnedStETHBurner(
        lido_dao_self_owned_steth_burner
    )
