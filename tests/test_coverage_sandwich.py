"""
Tests for coverage sandwitching

"""

import pytest

from brownie import ZERO_ADDRESS, CurveExchanger
from utils.config import network_name
import utils.log as log


########################################################################################################
# Base scenario:
# Sandwicher has 10,000 ETH to try his luck on extracting profit from coverage application.
#
# Outcomes:
# 1. Sandwicher wins ~90ETH by step-in with 10,000 ETH without quota.
#    NB: sandwicher wins more with trading (two swaps) than with stake-trade (stake and single swap)
#        because he balances pool by two-swaps approach dealing with large amounts.
#
# 2. Sandwicher wins nothing with quota 8 BP or less.
#    NB: we have chosen 4 BP as single swap curve pool fee with a margin 4 BP for oracle rebase itself.
#
########################################################################################################


initial_victim_stETH_balance = 100 * 10**18
initial_sandwicher_ETH_balance = 10000 * 10**18
burn_quota_bp = 8


# Large ETH holder
eth_holder: str = '0x00000000219ab540356cBB839Cbe05303d7705Fa'

@pytest.fixture(scope="module")
def sandwicher(accounts):
    exchanger = CurveExchanger.deploy({'from': accounts[0]})
    # burn extra funds
    exchanger_acc = accounts.at(exchanger, force=True)
    exchanger_acc.transfer(ZERO_ADDRESS, exchanger_acc.balance(), gas_price=0)
    return exchanger

def _round10(val: int) -> int:
    return ((val + 9) // 10) * 10

def before_sandwicher_step_in(
    accounts, dao_voting, lido, oracle, acl,
    composite_post_rebase_beacon_receiver,
    self_owned_steth_burner, sandwicher
):
    netname = network_name().split('-')[0]
    assert netname in ("goerli", "mainnet"), "Incorrect network name"

    composite_post_rebase_beacon_receiver.addCallback(
        self_owned_steth_burner.address,
        { 'from': dao_voting }
    )
    oracle.setBeaconReportReceiver(
        composite_post_rebase_beacon_receiver.address,
        { 'from': dao_voting }
    )

    acl.grantPermission(self_owned_steth_burner.address, lido.address, lido.BURN_ROLE(), {'from': dao_voting})
    self_owned_steth_burner.setBurnAmountPerRunQuota(burn_quota_bp, {'from': dao_voting})

    whale = accounts.at(eth_holder, force=True)
    whale.transfer(sandwicher, initial_sandwicher_ETH_balance, gas_price=0)
    assert initial_sandwicher_ETH_balance == sandwicher.balance(), "wrong balance"

    lido.submit(ZERO_ADDRESS, {'from': accounts[0], 'value': 100*10**18})
    lido.submit(ZERO_ADDRESS, {'from': whale, 'value': 50000*10**18})

    total_ether_before = lido.getTotalPooledEther()

    log.h(log.highlight('--- 0. Forked state', log.color_yellow))
    assert _round10(initial_victim_stETH_balance) == _round10(lido.balanceOf(accounts[0].address)), "wrong balance"
    log.ok('Victim initial stETH balance', initial_victim_stETH_balance / 10**18)

    # 1% slashing (-100 basis points totalPooledEther change)
    oracle_report(lido, oracle, -100)

    log.h(log.highlight('--- 1. Slashing just happenned (1% loss)', log.color_yellow))
    log.ok('Victim after-slashing stETH balance', lido.balanceOf(accounts[0].address) / 10**18)
    total_ether_after = lido.getTotalPooledEther()
    ether_loss = total_ether_before - total_ether_after
    log.ok('Lido total ether loss', ether_loss // 10**18)
    steth_amount_to_recover = lido.getPooledEthByShares(0.01 * lido.getTotalShares())

    log.h(log.highlight('--- 2. Coverage application decided', log.color_yellow))
    assert initial_sandwicher_ETH_balance == sandwicher.balance(), "wrong balance"
    log.ok('Sandwicher initial ETH balance', initial_sandwicher_ETH_balance / 10**18)

    return steth_amount_to_recover

def after_sandwicher_step_in(
    accounts, dao_voting, lido, oracle,
    self_owned_steth_burner, sandwicher,
    steth_amount_to_recover
):
    log.ok('Sandwicher initial stETH balance', lido.balanceOf(sandwicher.address) / 10**18)

    whale = accounts.at(eth_holder, force=True)
    lido.transfer(dao_voting.address, steth_amount_to_recover, { 'from': whale })
    apply_coverage(self_owned_steth_burner, dao_voting, oracle, lido, steth_amount_to_recover)

    log.h(log.highlight(f'--- 3. First round of coverage applied with quota {burn_quota_bp} BP', log.color_yellow))
    log.ok('Sandwicher stETH balance (after first round of coverage)', lido.balanceOf(sandwicher.address) / 10**18)

    sandwicher.swapStETH2ETH({'from': accounts[0]})
    log.ok('Sandwicher ETH balance (after swap)', sandwicher.balance() / 10**18)

    if sandwicher.balance() > initial_sandwicher_ETH_balance:
        log.ok(f"Sandwicher wins {(sandwicher.balance() - initial_sandwicher_ETH_balance) / 10**18} ETH")

    log.nb('Sandwicher loss (ETH)', (initial_sandwicher_ETH_balance - sandwicher.balance()) / 10**18)

    while lido.balanceOf(self_owned_steth_burner) > 0:
        oracle_report(lido, oracle, 0)

    log.h(log.highlight('--- 4. Coverage applied completely', log.color_yellow))

    log.ok('Victim stETH balance (recovered)', lido.balanceOf(accounts[0].address) / 10**18)
    log.nb('Victim loss (stETH)', (initial_victim_stETH_balance - lido.balanceOf(accounts[0].address)) / 10**18)


def test_coverage_sandwiching_trading_only(
    sandwicher, accounts, dao_voting, lido, oracle, acl,
    composite_post_rebase_beacon_receiver, self_owned_steth_burner
):
    steth_amount_to_recover = before_sandwicher_step_in(
        accounts, dao_voting, lido, oracle, acl,
        composite_post_rebase_beacon_receiver, self_owned_steth_burner, sandwicher
    )
    sandwicher.swapETH2StETH({'from': accounts[0]})
    after_sandwicher_step_in(
        accounts, dao_voting, lido, oracle,
        self_owned_steth_burner, sandwicher, steth_amount_to_recover
    )

def test_coverage_sandwiching_staking_trading(
    sandwicher, accounts, dao_voting, lido, oracle, acl,
    composite_post_rebase_beacon_receiver, self_owned_steth_burner
):
    steth_amount_to_recover = before_sandwicher_step_in(
        accounts, dao_voting, lido, oracle, acl,
        composite_post_rebase_beacon_receiver, self_owned_steth_burner, sandwicher
    )
    sandwicher.stakeETH4StETH({'from': accounts[0]})
    after_sandwicher_step_in(
        accounts, dao_voting, lido, oracle,
        self_owned_steth_burner, sandwicher, steth_amount_to_recover
    )


def oracle_report(lido, oracle, change):
    _, validators, beaconBalance = lido.getBeaconStat()

    expectedEpoch = oracle.getExpectedEpochId()
    reporters = oracle.getOracleMembers()
    quorum = oracle.getQuorum()

    buffered = lido.getTotalPooledEther() - beaconBalance
    new_total_pooled_ether = lido.getTotalPooledEther() * (1 + change / 10000)
    new_balance = new_total_pooled_ether - buffered

    for reporter in reporters[:quorum]:
        oracle.reportBeacon(expectedEpoch, int(new_balance / 10**9 + 0.5), validators, { 'from': reporter })

def apply_coverage(steth_burner, dao_voting, oracle, lido, steth_amount):
    lido.approve(steth_burner.address, steth_amount, { 'from': dao_voting.address })

    steth_burner.requestBurnMyStETHForCover(steth_amount, { 'from': dao_voting.address })

    oracle_report(lido, oracle, 0)
