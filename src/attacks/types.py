# src/attacks/types.py
from dataclasses import dataclass
from typing import Any, List, Optional

# What exists in the encrypted DB (conceptual); attacker does not see value, they see 'alpha_prefix' (oram_index)
@dataclass(frozen=True)
class EncryptedTuple:
	enc_id: int
	value: Any                 # plaintext attribute value (known to attacker in strong model)
	alpha_prefix: int          # leaked identifier prefix (your oram_index)

# Per query, what the attacker sees: observed_volume: |Sq| (padded later), returned_prefixes: list of leaked alpha_prefix values for each returned encrypted tuple
@dataclass(frozen=True)
class QueryObservation:
	token_id: int              # opaque handle for the query token (attacker doesn't know plaintext value)
	observed_volume: int
	returned_prefixes: List[int]

@dataclass(frozen=True)
class AttackResult:
	qrsr: float                # query recovery success rate
	drsr: Optional[float]      # database recovery success rate (None if not computed)
