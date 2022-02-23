"""
Tests for mev+tx_priority_fee sandwitching (post-merge)

"""

import pytest

from brownie import CurveExchanger, chain
import utils.log as log


########################################################################################################
# Base scenario:
# Sandwicher has 10,000 ETH to try his luck on extracting profit from too large rebase.
#
# Preconditions:
# Nowadays APR is ~5%, so DPR is ~1.4 basis points
# Post-merge APR could increase to 15% on short-term surges (DPR ~4 basis points)
# Expected post-merge APR is about 7.5% according to current MEV and priority fee evaluations (DPR ~2 basis points)
#
# See:
# https://github.com/lidofinance/Beaconchain_model/blob/main/queue_modeling.ipynb
# ttps://github.com/lidofinance/lido-improvement-proposals/blob/lip-12/restaking-with-forecast/LIPS/assets/lip-12/restaking_effect.ipynb
#
# Keynotes:
# - priority_fee_monthly  = 21282 # https://dune.xyz/queries/382535
#
# - avg_mev_reward_per_block = 0.185 # inferring from flashbots activity, \
# we obtain this number by substracting the Flashbots miner tip from the \
# tail gas price multiplied by the gas used by the mined Flashbots bundle.
#
# - block_selection_frequency_flashbots = 58 # % of blocks seen by Flashbots-enabled miners contains Flashbots bundles
########################################################################################################

dprs = [1.4, 2., 4., 7.25]
sandwitcher_balances = [x * 10**18 for x in [100, 1_000, 10_000, 100_000]]

# Large ETH holder
eth_holder: str = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'

@pytest.fixture(scope="module")
def sandwicher(accounts):
    return CurveExchanger.deploy({'from': accounts[0]})

def test_mev_tx_fee_sandwiching_trading_only(
    sandwicher, accounts, lido, oracle, dao_voting
):
    whale = accounts.at(eth_holder, force=True)
    oracle.setAllowedBeaconBalanceAnnualRelativeIncrease(10000, {'from': dao_voting})
    chain.snapshot()

    for dpr in dprs:
        for sandwiching_balance in sandwitcher_balances:
            whale.transfer(sandwicher, sandwiching_balance, gas_price=0)

            log.h(f'Testing DPR {dpr}')
            log.ok('Testing sandwiching balance', sandwicher.balance() / 10**18)

            sandwicher.swapETH2StETH({'from': accounts[0]})
            log.ok('Supply increase (ETH)', (dpr * lido.getTotalPooledEther() / 10000) // 10**18)
            oracle_report(lido, oracle, dpr)

            sandwicher.swapStETH2ETH({'from': accounts[0]})

            log.ok('Sandwicher ETH balance (after swap)', sandwicher.balance() / 10**18)

            if sandwicher.balance() > sandwiching_balance:
                log.nb("Sandwicher wins (ETH)", (sandwicher.balance() - sandwiching_balance) / 10**18)
            else:
                log.ok('Sandwicher loss (ETH)', (sandwiching_balance - sandwicher.balance()) / 10**18)

            assert sandwicher.balance() < sandwiching_balance

            chain.revert()


def test_mev_tx_fee_sandwiching_stake_trading(
    sandwicher, accounts, lido, oracle, dao_voting
):
    whale = accounts.at(eth_holder, force=True)
    oracle.setAllowedBeaconBalanceAnnualRelativeIncrease(10000, {'from': dao_voting})
    chain.snapshot()

    for dpr in dprs:
        for sandwiching_balance in sandwitcher_balances:
            whale.transfer(sandwicher, sandwiching_balance, gas_price=0)

            log.h(f'Testing DPR {dpr}')
            log.ok('Testing sandwiching balance', sandwicher.balance() / 10**18)

            sandwicher.stakeETH4StETH({'from': accounts[0]})
            log.ok('Supply increase (ETH)', (dpr * lido.getTotalPooledEther() / 10000) // 10**18)
            oracle_report(lido, oracle, dpr)

            sandwicher.swapStETH2ETH({'from': accounts[0]})

            log.ok('Sandwicher ETH balance (after swap)', sandwicher.balance() / 10**18)

            if sandwicher.balance() > sandwiching_balance:
                log.nb("Sandwicher wins (ETH)", (sandwicher.balance() - sandwiching_balance) / 10**18)
            else:
                log.ok('Sandwicher loss (ETH)', (sandwiching_balance - sandwicher.balance()) / 10**18)

            assert sandwicher.balance() < sandwiching_balance

            chain.revert()


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
