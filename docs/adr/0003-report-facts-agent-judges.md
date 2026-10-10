# EHand reports facts; the Agent judges

v0 planned an `ap diagnose` command that classified failures and attached a confidence. EHand instead hands the Agent a time-aligned Timeline of both sides (Target Board traffic and Peripheral Model replies, plus Injections and line timing) and marks only protocol-rule violations as Fact Flags. Deciding whose code is wrong and what to change is left to the Agent, because model reasoning improves faster than hand-written diagnosis rules would, and the value EHand alone can add is facts no other tool can see.

## Consequences

- Volume is handled by layering, not by judging: raw samples, edges/bytes, frames, transactions, Summary. The Agent gets the Summary by default and drills down on request. Small-model semantic compression is a later option, not V1.
