# @version 0.3.1
# @author skozin, krogla, dzhon <info@lido.fi>
# @licence MIT
from vyper.interfaces import ERC20


interface ERC20Decimals:
    def decimals() -> uint256: view

interface ChainlinkAggregatorV3Interface:
    def decimals() -> uint256: view
    # (roundId: uint80, answer: int256, startedAt: uint256, updatedAt: uint256, answeredInRound: uint80)
    def latestRoundData() -> (uint256, int256, uint256, uint256, uint256): view

interface CurvePool:
    def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256) -> uint256: payable

interface Lido:
    def submit(ref: address) -> uint256: payable


event SoldStETHToETH:
    steth_amount: uint256
    eth_amount: uint256

event SoldETHToStETH:
    eth_amount: uint256
    steth_amount: uint256

event StakedETHToStETH:
    eth_amount: uint256
    steth_amount: uint256


STETH_TOKEN: constant(address) = 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84
STETH_TOKEN_DECIMALS: constant(uint256) = 18
WETH_TOKEN: constant(address) = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
WETH_TOKEN_DECIMALS: constant(uint256) = 18

CURVE_STETH_POOL: constant(address) = 0xDC24316b9AE028F1497c275EB9192a3Ea0f67022
CURVE_ETH_INDEX: constant(uint256) = 0
CURVE_STETH_INDEX: constant(uint256) = 1

# Maximum difference (in percents multiplied by 10**18) between the resulting
# stETH/ETH price and the stETH/ETH price obtained from the feed.
max_steth_eth_price_difference_percent: public(uint256)

@external
def __init__():
    assert ERC20Decimals(WETH_TOKEN).decimals() == WETH_TOKEN_DECIMALS
    assert ERC20Decimals(STETH_TOKEN).decimals() == STETH_TOKEN_DECIMALS


@external
@payable
def __default__():
    pass


@internal
@pure
def _get_min_amount_out(
    amount: uint256,
    price: uint256,
    max_diff_percent: uint256,
    decimal_token_in: uint256,
    decimal_token_out: uint256
) -> uint256:
    # = (amount * (10 ** (18 - decimal_token_in)) * price) / 10 ** 18
    amount_out: uint256 = (amount * price) / (10 ** decimal_token_in)

    min_mult: uint256 = 10**18 - max_diff_percent

    # = ((amount_out * min_mult) / 10**18) / (10 ** (18 - decimal_token_out))
    return (amount_out * min_mult) / (10 ** (36 - decimal_token_out))


# stETH -> ETH (Curve)
@external
def swapStETH2ETH() -> uint256:
    steth_amount: uint256 = ERC20(STETH_TOKEN).balanceOf(self)
    assert steth_amount > 0, "zero stETH balance"

    ERC20(STETH_TOKEN).approve(CURVE_STETH_POOL, steth_amount)

    CurvePool(CURVE_STETH_POOL).exchange(
        CURVE_STETH_INDEX,
        CURVE_ETH_INDEX,
        steth_amount,
        0 # do not require a minimum amount
    )
    eth_amount: uint256 = self.balance

    log SoldStETHToETH(
        steth_amount,
        eth_amount
    )

    return eth_amount


# ETH -> stETH (Curve)
@external
def swapETH2StETH() -> uint256:
    eth_amount: uint256 = self.balance
    assert eth_amount > 0, "zero ETH balance"

    #ERC20(STETH_TOKEN).approve(CURVE_STETH_POOL, steth_amount)

    CurvePool(CURVE_STETH_POOL).exchange(
        CURVE_ETH_INDEX,
        CURVE_STETH_INDEX,
        eth_amount,
        0, value=eth_amount # do not require a minimum amount
    )
    steth_amount: uint256 = ERC20(STETH_TOKEN).balanceOf(self)

    log SoldETHToStETH(
        eth_amount,
        steth_amount
    )

    return steth_amount

# ETH -> stETH (Lido)
@external
def stakeETH4StETH() -> uint256:
    eth_amount: uint256 = self.balance
    assert eth_amount > 0, "zero ETH balance"

    Lido(STETH_TOKEN).submit(ZERO_ADDRESS, value=self.balance)
    steth_amount: uint256 = ERC20(STETH_TOKEN).balanceOf(self)

    log StakedETHToStETH(
        eth_amount,
        steth_amount
    )

    return steth_amount
