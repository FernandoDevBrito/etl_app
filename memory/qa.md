# QA memory (recurring mistakes seen in rejections; retro curates)

- Subjective criteria ("looks good", "fast enough") can't be verified: reject if the card reached review with them unquantified.
- Reject when a criterion has no test or command evidence.
- Criteria passing is not enough for parsers/money code: probe malformed and adversarial inputs (stray signs, unbalanced parens, exponents) and reject if any silently returns a wrong value instead of raising. (Card 003: only qa caught the sign flip; a reviewer who just checks listed criteria misses it.)
