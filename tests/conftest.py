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
def oracle(interface):
    return interface.LidoOracle(lido_dao_oracle_address)

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
