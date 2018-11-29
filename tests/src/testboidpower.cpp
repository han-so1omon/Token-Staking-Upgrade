/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
*/

#include "testboidpower.hpp"
#include <math.h>

void testboidpower::create(account_name issuer, asset maximum_supply)
{
  require_auth(_self);
}

void testboidpower::insert(account_name user, uint32_t boidpower) {
  require_auth(user);

  accounts accts(_self, user);
  auto el = accts.find(user);
  if (el != accts.end()) {
    accts.modify(el,user, [&](auto &a) {
          a.boidpower = boidpower;
    });
  } else {
    accts.emplace(user, [&](auto &a) {
          a.boidpower = boidpower;
    });
  }
}

// see https://developers.eos.io/eosio-home/docs/sending-an-inline-transaction-to-external-contract
void testboidpower::sndnewbp(account_name req_acct) {
  print("hort\n");
  require_auth(N(boid.stake));
  accounts accts(_self,req_acct);

  uint32_t boidpower = 0;
  auto el = accts.find(req_acct);
  if (el != accts.end()) {
    boidpower = el->boidpower;
  }
  print("hurp\n");
  action(
    permission_level{get_self(),N(active)},
    N(boid.stake),
    N(setnewbp),
    std::make_tuple(get_self(),req_acct,boidpower)
  ).send();
}

