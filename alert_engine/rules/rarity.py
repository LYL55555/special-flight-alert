"""Map numeric score to a coarse rarity label for notifications."""


def rarity_tier(score: int) -> str:
    if score >= 100:
        return "very_high"
    if score >= 80:
        return "high"
    if score >= 50:
        return "medium"
    return "low"
