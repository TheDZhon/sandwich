import pytest
import os

from typing import Optional

from brownie import chain

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
    oracle = interface.LidoOracle(lido_dao_oracle_address)
    oracle.setAllowedBeaconBalanceAnnualRelativeIncrease(2800, {'from': dao_voting.address})
    oracle.reportBeacon(159300, 4700878413390971, 141433, {'from': '0x007de4a5f7bc37e2f26c0cb2e8a95006ee9b89b5'})
    return oracle

@pytest.fixture(scope="module")
def composite_post_rebase_beacon_receiver(interface):
    return interface.CompositePostRebaseBeaconReceiver(
        composite_post_rebase_beacon_receiver_address
    )

@pytest.fixture(scope="module")
def self_owned_steth_burner(interface):
    return interface.SelfOwnedStETHBurner(
        self_owned_steth_burner_address
    )
