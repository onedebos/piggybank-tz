# Written in smartpy v0.19

import smartpy as sp


@sp.module
def main():
    ledger: type = sp.big_map[
        sp.address, sp.record(balance=sp.mutez, withdrawal_date=sp.timestamp)
    ]

    class Piggybank(sp.Contract):
        def __init__(self):
            self.data.ledger = {}
            self.data.total_deposits = sp.mutez(0)

        @sp.entrypoint
        def create_piggybank(self, params):
            value = sp.record(balance=sp.mutez(0), withdrawal_date=params.date)
            assert not self.data.ledger.contains(
                sp.sender
            ), "Piggybank already created."
            self.data.ledger[sp.sender] = value

        @sp.entrypoint
        def deposit(self):
            assert self.data.ledger.contains(sp.sender), "Join the group first"
            balance = self.data.ledger[sp.sender].balance
            withdrawal_date = self.data.ledger[sp.sender].withdrawal_date
            value = sp.record(
                balance=balance + sp.amount, withdrawal_date=withdrawal_date
            )
            self.data.ledger[sp.sender] = value
            self.data.total_deposits += sp.amount

        @sp.entrypoint
        def break_piggybank(self):
            assert self.data.ledger.contains(sp.sender), "Join the group first"
            piggybank = self.data.ledger[sp.sender]
            assert sp.now >= piggybank.withdrawal_date, "Withdrawal date not reached"
            sp.send(sp.sender, piggybank.balance)
            self.data.total_deposits -= piggybank.balance
            del self.data.ledger[sp.sender]

        @sp.onchain_view
        def get_piggybank_balance(self, params):
            # when a wallet address is passed, return the balance
            return self.data.ledger[params.address].balance


@sp.add_test()
def test():
    scenario = sp.test_scenario("Test", main)
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob").address
    charlie = sp.test_account("Charlie").address

    contract = main.Piggybank()
    scenario += contract

    scenario.h3("Create Piggybank")
    contract.create_piggybank(
        _sender=alice, date=sp.timestamp_from_utc(2024, 2, 23, 11, 00, 00)
    )
    contract.create_piggybank(
        _sender=charlie, date=sp.timestamp_from_utc(2024, 2, 19, 11, 00, 00)
    )

    scenario.h3("Deposit to Piggybank")
    contract.deposit(_sender=alice, _amount=sp.tez(10))
    contract.deposit(_sender=charlie, _amount=sp.tez(20))

    scenario.h3("Cannot break Piggybank")
    contract.break_piggybank(
        _sender=alice, _valid=False, _now=sp.timestamp_from_utc(2024, 2, 21, 11, 00, 00)
    )

    scenario.h3("Can break Piggybank")
    contract.break_piggybank(
        _sender=charlie, _now=sp.timestamp_from_utc(2024, 2, 21, 11, 00, 00)
    )
