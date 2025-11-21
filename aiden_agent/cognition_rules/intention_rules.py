# ============================================================
#   SYMBOLIC INTENTION RULES (TUNED – PHASE 6)
#   Returns plain dicts → avoids circular import
# ============================================================

# ------------------------------------------------------------
# 0. LEARNING SATURATION (TOP PRIORITY)
# ------------------------------------------------------------
def rule_learning_saturated(agent, world, spatial):
    """
    Stop learning intention once knowledge is high enough.
    Push exploration instead.
    """
    if agent.knowledge > 20:
        return {
            "type": "EXPLORE",
            "strength": 0.4,
            "reason": "Knowledge high — diversify behavior"
        }
    return None


# ------------------------------------------------------------
# 1. LOW NOVELTY → Explore
# ------------------------------------------------------------
def rule_low_novelty(agent, world, spatial):
    novelty = agent.self_model.novelty_history[-1] if agent.self_model.novelty_history else 1.0

    if novelty < 0.08:
        return {
            "type": "EXPLORE",
            "strength": 0.7,
            "reason": "Novelty is low"
        }
    return None


# ------------------------------------------------------------
# 2. LOW KNOWLEDGE → Learn
# ------------------------------------------------------------
def rule_low_knowledge(agent, world, spatial):
    if agent.knowledge < 6:
        return {
            "type": "LEARN",
            "strength": 0.5,
            "reason": "Knowledge low"
        }
    return None


# ------------------------------------------------------------
# 3. BAD TERRAIN → Move to safer area (PHASE 6 FIX)
# ------------------------------------------------------------
def rule_bad_terrain(agent, world, spatial):
    """
    NEW LOGIC:
    • Only trigger when agent is currently on hazardous terrain.
    • Uses normalized terrain values.
    • Avoids false triggers on plains/forest/river.
    """

    terrain = spatial.get("terrain", "").lower()

    DANGEROUS = {"mountain", "mountains", "ruin", "ruins", "cliff", "lava"}

    if terrain in DANGEROUS:
        return {
            "type": "MOVE_TO_SAFER_AREA",
            "strength": 0.9,
            "reason": f"Dangerous terrain ({terrain})"
        }

    return None


# ------------------------------------------------------------
# 4. LOW ENERGY → Rest
# ------------------------------------------------------------
def rule_low_energy(agent, world, spatial):
    if agent.energy < 30:
        return {
            "type": "REST",
            "strength": 1.0,
            "reason": "Energy low"
        }
    return None


# ------------------------------------------------------------
# 5. HIGH LEARNING MOTIVATION → Learn
# ------------------------------------------------------------
def rule_motivation_learning(agent, world, spatial):
    if agent.motivation_levels.get("learning", 0) > 0.55:
        return {
            "type": "LEARN",
            "strength": 0.6,
            "reason": "Learning motivation high"
        }
    return None


# ------------------------------------------------------------
# 6. HIGH EXPLORATION MOTIVATION → Explore
# ------------------------------------------------------------
def rule_motivation_exploration(agent, world, spatial):
    if agent.motivation_levels.get("exploration", 0) > 0.45:
        return {
            "type": "EXPLORE",
            "strength": 0.6,
            "reason": "Exploration motivation high"
        }
    return None


# ============================================================
# RULE EXECUTION ORDER  (CRITICAL)
# ============================================================

INTENTION_RULES = [
    rule_learning_saturated,      # MUST stay first
    rule_low_novelty,
    rule_bad_terrain,
    rule_low_energy,
    rule_low_knowledge,
    rule_motivation_learning,
    rule_motivation_exploration,
]
