"""Shared update guarantees with distinct record ownership; no automatic cascade."""
from dataclasses import dataclass
from brain import BrainError, Plan

# (owner agreement required, downstream records to review, never auto-write)
RULES = {
    'VISION': {'direction': (True, ('README', 'PROGRESS', 'BRAIN'))},
    'PROGRESS': {'status': (False, ()), 'delivered': (False, ('CHANGELOG', 'README')), 'priority': (True, ('VISION',))},
    'BRAIN': {'navigation': (False, ('STRUCTURE',)), 'provider': (True, ('STRUCTURE',)), 'permission': (True, ('STRUCTURE',))},
    'STRUCTURE': {'location': (False, ('BRAIN', 'README')), 'command': (False, ('README',))},
}

@dataclass(frozen=True)
class Change:
    record: str
    event: str
    evidence: tuple[str, ...] = ()
    agreement: str = ''

@dataclass(frozen=True)
class RecordPlan:
    plan: Plan
    change: Change
    review: tuple[str, ...]


def prepare_record(brain, identity, patch, change):
    if change.record not in RULES or change.event not in RULES[change.record]:
        raise BrainError('event does not belong to this record')
    plan = brain.prepare(identity, patch)
    if plan.after == plan.source.text:
        return RecordPlan(plan, change, ())
    agreement_required, review = RULES[change.record][change.event]
    if not isinstance(change.evidence, tuple) or not change.evidence or any(not isinstance(e, str) or not e.strip() for e in change.evidence):
        raise BrainError('changed facts need evidence references')
    if agreement_required and (not isinstance(change.agreement, str) or not change.agreement.strip()):
        raise BrainError('owner agreement reference required')
    return RecordPlan(plan, change, review)


def apply_record(brain, record_plan, authorize):
    # Evidence references describe the claim; they do not prove it or grant
    # permission. The trusted host verifies them and all current holds here.
    return brain.apply(record_plan.plan, lambda _: authorize(record_plan))


def should_report(*, requested=False, permission_needed=False, actionable_blocker=False):
    """Routine review/maintenance never replaces the user's actual task report."""
    return requested or permission_needed or actionable_blocker
