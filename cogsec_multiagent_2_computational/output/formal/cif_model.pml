/* CIF Promela Model: 5 agents, max 1 Byzantine */

#define N_AGENTS 5
#define MAX_BYZANTINE 1
#define QUORUM ((2 * N_AGENTS) / 3 + 1)

/* State variables */
int vote_count = 0;
bool decided = false;
int trust[N_AGENTS];
int delegated_trust[N_AGENTS];
int direct_trust[N_AGENTS];
bool firewall_active = true;
bool injection = false;

/* Agent process */
proctype Agent(int id; bool is_byzantine) {
  int my_trust;

  if
  :: is_byzantine ->
    /* Byzantine agent: adversarial voting */
    trust[id] = 0;
    my_trust = 0;
  :: !is_byzantine ->
    /* Honest agent: truthful voting */
    trust[id] = 100;
    my_trust = 100;
  fi;

  /* Vote phase */
  atomic {
    if
    :: my_trust > 50 -> vote_count++;
    :: else -> skip;
    fi;
  };

  /* Check quorum */
  if
  :: vote_count >= QUORUM -> decided = true;
  :: else -> skip;
  fi;

  /* Delegation: delegated <= direct */
  direct_trust[id] = my_trust;
  delegated_trust[id] = my_trust * 85 / 100;  /* decay = 0.85 */
}

/* Firewall process */
proctype Firewall() {
  do
  :: injection && firewall_active ->
    injection = false;  /* blocked */
  :: !firewall_active && injection ->
    skip;  /* not blocked */
  :: !injection ->
    skip;
  od;
}

/* Init */
init {
  int i;
  for (i : 0 .. 4) {
    if
    :: i < 1 ->
      run Agent(i, true);
    :: else ->
      run Agent(i, false);
    fi;
  };
  run Firewall();
}

/* LTL Properties */

/* P1: Consensus eventually reached when quorum available */
ltl consensus { [] (vote_count >= QUORUM -> <> decided) }

/* P2: Delegated trust never exceeds direct trust */
ltl trust_bound { [] (delegated_trust[0] <= direct_trust[0]) }

/* P3: Active firewall prevents injection */
ltl no_injection { [] (firewall_active -> !injection) }
