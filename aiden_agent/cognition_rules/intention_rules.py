# ============================================================
#   PHASE-6 SYMBOLIC INTENTION RULES (FINAL VERSION)
#   These rules produce *symbolic intentions*, not actions.
#   They feed into the IntentionEngine and arbitration layer.
# ============================================================

DANGEROUS = {"mountain", "mountains", "ruin", "ruins"}


# ------------------------------------------------------------
#  SAFETY UTIL: GET TERRAIN STRING RELIABLY
# ------------------------------------------------------------
def _safe_get_terrain(agent, world, spatial):
    """
    Preferred terrain source priority:
        1. spatial["terrain"] (if planner provided it)
        2. GridWorld.get_cell().terrain.value
    Guarantees a lowercase string.
    """
    # Case 1: spatial provided terrain
    t = spatial.get("terrain")
    if t:
        return str(t).lower()

    # Case 2: derive from world object
    if hasattr(world, "get_cell"):
        cell = world.get_cell(agent.position_x, agent.position_y)
        if cell and hasattr(cell.terrain, "value"):
            return cell.terrain.value.lower()

    return "unknown"


# ------------------------------------------------------------
# 1. KNOWLEDGE SATURATION (HIGHEST PRIORITY)
# ------------------------------------------------------------
def rule_learning_saturated(agent, world, spatial):
    """
    If knowledge exceeds 20:
        → force EXPLORE to diversify behavior.
    This rule must always run first.
    """
    if agent.knowledge > 20:
        return {
            "type": "EXPLORE",
            "strength": 0.65,
            "reason": "Knowledge saturated (>20) – diversify"
        }
    return None


# ------------------------------------------------------------
# 2. STRICT TERRAIN SAFETY (CRITICAL)
# ------------------------------------------------------------
def rule_strict_terrain(agent, world, spatial):
    """
    If terrain ∈ mountains/ruins:
        → force MOVE_TO_SAFER_AREA (BFS handled later)
    """
    terrain = _safe_get_terrain(agent, world, spatial)

    if terrain in DANGEROUS:
        return {
            "type": "MOVE_TO_SAFER_AREA",
            "strength": 1.0,
            "reason": f"Unsafe terrain detected: {terrain}"
        }
    return None


# ------------------------------------------------------------
# 3. LOW ENERGY → REST (PRE-META)
# ------------------------------------------------------------
def rule_low_energy(agent, world, spatial):
    """
    Symbolic rest trigger.
    True override handled by Meta-Controller (energy < 15).
    """
    if agent.energy < 30:
        return {
            "type": "REST",
            "strength": 1.0,
            "reason": "Energy < 30"
        }
    return None


# ------------------------------------------------------------
# 4. LOW KNOWLEDGE (EARLY GAME ONLY)
# ------------------------------------------------------------
def rule_low_knowledge(agent, world, spatial):
    """
    Allow LEARN only in early game.
    Hard stop once knowledge > 6.
    """
    if agent.knowledge < 6:
        return {
            "type": "LEARN",
            "strength": 0.85,
            "reason": "Knowledge < 6"
        }
    return None


# ------------------------------------------------------------
# 5. LOW NOVELTY → EXPLORE
# ------------------------------------------------------------
def rule_low_novelty(agent, world, spatial):
    """
    If novelty < 0.08:
        → encourage EXPLORE.
    Stronger stagnation override is in IntentionEngine.
    """
    novelty = agent.self_model.novelty_history[-1] if agent.self_model.novelty_history else 1.0

    if novelty < 0.08:
        return {
            "type": "EXPLORE",
            "strength": 0.7,
            "reason": "Novelty drop (<0.08)"
        }
    return None


# ------------------------------------------------------------
# 6. HIGH LEARNING DRIVE
# ------------------------------------------------------------
def rule_motivation_learning(agent, world, spatial):
    """
    If learning motivation > 0.55:
        → propose LEARN intention (unless blocked by saturation rule).
    """
    if agent.motivation_levels.get("learning", 0) > 0.55:
        return {
            "type": "LEARN",
            "strength": 0.6,
            "reason": "Learning motivation > 0.55"
        }
    return None


# ------------------------------------------------------------
# 7. HIGH EXPLORATION DRIVE
# ------------------------------------------------------------
def rule_motivation_exploration(agent, world, spatial):
    """
    If exploration motivation > 0.45:
        → EXPLORE.
    """
    if agent.motivation_levels.get("exploration", 0) > 0.45:
        return {
            "type": "EXPLORE",
            "strength": 0.6,
            "reason": "Exploration motivation > 0.45"
        }
    return None


# ============================================================
# RULE ORDER (NEVER CHANGE)
# ============================================================

INTENTION_RULES = [
    rule_learning_saturated,         # 1 – always first
    rule_strict_terrain,             # 2 – safety
    rule_low_energy,                 # 3 – physiological
    rule_low_knowledge,              # 4 – early learning
    rule_low_novelty,                # 5 – diversification
    rule_motivation_learning,        # 6 – drives
    rule_motivation_exploration      # 7 – drives
]
