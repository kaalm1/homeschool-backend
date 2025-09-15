import random
from collections import Counter, defaultdict
from typing import List, Set
from svc.app.models.activity import Activity
from svc.app.datatypes.enums import Cost, ActivityType, ActivityScale


def build_min_based_batches(
    activities: List[Activity],
    min_batch_size: int = 50,
    stretch_per_batch: int = 5,
    diversity_weight: float = 10.0,
    controlled_shuffle: bool = True,
) -> List[List[Activity]]:
    """
    Build batches where each batch starts at min_batch_size and remaining activities
    are distributed evenly across batches.

    Args:
        activities: List of Activity objects
        min_batch_size: Minimum allowed batch size
        stretch_per_batch: Number of fully random "wildcard" activities to inject
        diversity_weight: Scaling factor for secondary tag underrepresentation
    Returns:
        List of batches (each batch is a list of Activity objects)
    """
    total_activities = len(activities)

    # Small datasets: just one batch
    if total_activities <= min_batch_size:
        return [activities]

    # Step 1: Determine number of batches based on min_batch_size
    num_batches = total_activities // min_batch_size
    remainder = total_activities % min_batch_size

    # Initialize batch sizes
    batch_sizes = [min_batch_size] * num_batches

    # Distribute remainder evenly across first batches
    for i in range(remainder):
        batch_sizes[i] += 1

    # 🔹 Case 1: Pure random batching
    if not controlled_shuffle:
        shuffled = activities[:]
        random.shuffle(shuffled)

        batches = []
        idx = 0
        for size in batch_sizes:
            batches.append(shuffled[idx: idx + size])
            idx += size
        return batches

    # Step 2: Primary buckets for controlled shuffle
    primary_buckets = defaultdict(list)
    for act in activities:
        cost = act.costs[0] if act.costs else Cost.LOW
        scale = act.activity_scale.value if act.activity_scale else ActivityScale.MEDIUM
        key = (cost, scale)
        primary_buckets[key].append(act)

    for b in primary_buckets.values():
        random.shuffle(b)

    batches = []
    used_activity_ids: Set[int] = set()

    # Step 3: Build each batch
    for batch_size in batch_sizes:
        batch = []
        secondary_counter = Counter()

        while len(batch) < batch_size and any(primary_buckets.values()):
            non_empty_keys = [k for k, v in primary_buckets.items() if v]
            bucket_key = random.choice(non_empty_keys)
            candidate = primary_buckets[bucket_key].pop()

            if candidate.id in used_activity_ids:
                continue

            secondary_tags = (
                candidate.durations or []
            ) + (candidate.participants or []) + (candidate.age_groups or []) \
              + (candidate.locations or []) + (candidate.seasons or []) \
              + (candidate.frequency or []) + (candidate.themes or []) \
              + (candidate.activity_types or [])

            score = 1.0
            for t in secondary_tags:
                score += 1.0 / (1 + secondary_counter[t])

            if random.random() < min(score / diversity_weight, 1.0):
                batch.append(candidate)
                used_activity_ids.add(candidate.id)
                for t in secondary_tags:
                    secondary_counter[t] += 1
            else:
                primary_buckets[bucket_key].insert(0, candidate)

        # Step 4: Inject stretch/wildcards
        remaining_candidates = [a for a in activities if a.id not in used_activity_ids]
        if remaining_candidates:
            random.shuffle(remaining_candidates)
            batch.extend(remaining_candidates[:stretch_per_batch])
            used_activity_ids.update(a.id for a in remaining_candidates[:stretch_per_batch])

        batches.append(batch)

    return batches
