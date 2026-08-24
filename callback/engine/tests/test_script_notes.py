import random
import unittest

from callback.engine.core.script_notes import (
    ACTOR_FILM_NOTE_WEIGHT,
    AMBIGUITY,
    CLARITY,
    DIRECTOR_NOTE_WEIGHT,
    ScriptNoteEffect,
    WHOLE_FILM,
    apply_script_note,
    sample_director_note,
)
from callback.engine.simulation.career import DirectorTerms, default_scene_policy, resolve_shoot


class TestScriptNoteEffectScalingAndCombining(unittest.TestCase):
    def test_scaled_leaves_fit_delta_untouched(self):
        effect = ScriptNoteEffect(fit_delta=6.0, script_quality_delta=5.0, audience_delta=4.0, critic_delta=-3.0)
        scaled = effect.scaled(0.4)
        self.assertEqual(scaled.fit_delta, 6.0)
        self.assertAlmostEqual(scaled.script_quality_delta, 2.0)
        self.assertAlmostEqual(scaled.audience_delta, 1.6)
        self.assertAlmostEqual(scaled.critic_delta, -1.2)

    def test_combined_with_sums_every_field(self):
        a = ScriptNoteEffect(fit_delta=1.0, script_quality_delta=2.0, audience_delta=3.0, critic_delta=4.0, cult_chance_bonus=0.1)
        b = ScriptNoteEffect(fit_delta=10.0, script_quality_delta=20.0, audience_delta=30.0, critic_delta=40.0, cult_chance_bonus=0.2)
        combined = a.combined_with(b)
        expected = ScriptNoteEffect(11.0, 22.0, 33.0, 44.0, 0.3)
        for field in ("fit_delta", "script_quality_delta", "audience_delta", "critic_delta", "cult_chance_bonus"):
            self.assertAlmostEqual(getattr(combined, field), getattr(expected, field))

    def test_director_note_weight_is_full_actor_weight_is_reduced(self):
        # The whole point of the rebalance: the director's own note is never diluted, the actor's
        # always is (outside directing their own film, where a different path applies).
        self.assertEqual(DIRECTOR_NOTE_WEIGHT, 1.0)
        self.assertLess(ACTOR_FILM_NOTE_WEIGHT, 1.0)
        self.assertGreater(ACTOR_FILM_NOTE_WEIGHT, 0.0)


class TestSampleDirectorNote(unittest.TestCase):
    def test_returns_a_real_choice_and_matching_effect(self):
        rng = random.Random(1)
        choice, effect = sample_director_note(60.0, 60.0, rng)
        self.assertIn(choice, (CLARITY, AMBIGUITY, WHOLE_FILM))
        self.assertEqual(effect, apply_script_note(choice))

    def test_higher_skill_and_command_leans_whole_film_more_often(self):
        weak_counts = {WHOLE_FILM: 0}
        strong_counts = {WHOLE_FILM: 0}
        trials = 2000
        rng = random.Random(7)
        for _ in range(trials):
            choice, _ = sample_director_note(10.0, 10.0, rng)
            if choice == WHOLE_FILM:
                weak_counts[WHOLE_FILM] += 1
        for _ in range(trials):
            choice, _ = sample_director_note(95.0, 95.0, rng)
            if choice == WHOLE_FILM:
                strong_counts[WHOLE_FILM] += 1
        self.assertGreater(strong_counts[WHOLE_FILM], weak_counts[WHOLE_FILM])


class TestDirectorIsPrimaryCreativeAuthorityOnActorsFilm(unittest.TestCase):
    """career.py's resolve_shoot/resolve_quality integration: the film's NPC director always
    contributes a full-weight note; an actor's own note (if they have script approval) layers on
    top at reduced weight, and never touches fit_delta, which stays theirs alone."""

    def test_shoot_result_carries_a_director_note(self):
        from callback.engine.actor.attributes import Attributes
        from callback.engine.actor.offers import Role
        from callback.engine.actor.persona import Persona
        from callback.engine.actor.standing import new_standing_model
        from callback.engine.simulation.career import ActorState

        state = ActorState(age=30, attrs=Attributes(), persona=Persona(), standing=new_standing_model())
        role = Role(
            project_id="p1", genre="drama", archetype="lead", billing="lead", char_age=30,
            type_strictness=0.5, difficulty=50.0, budget_for_role=5.0, gatekeeper="studio_head",
            film_budget_millions=20.0, studio="mid_major", union=True,
        )
        director = DirectorTerms(skill=70.0, command=70.0, prestige=60.0)
        rng = random.Random(3)
        scenes = default_scene_policy(rng)
        shoot = resolve_shoot(state, role, "table_work", scenes, director, rng)
        self.assertIn(shoot.director_note_choice, (CLARITY, AMBIGUITY, WHOLE_FILM))
        self.assertEqual(shoot.director_note, apply_script_note(shoot.director_note_choice))

    def test_actors_own_note_never_overrides_directors_on_the_film(self):
        # Force the director toward one note and the actor toward the opposite; the finished film's
        # audience/critic deltas should still be dominated by the director's, not flipped by the
        # actor's smaller, secondary push.
        director_note = apply_script_note(CLARITY)  # audience up, critic down
        actor_note = apply_script_note(AMBIGUITY)  # critic up, audience down — opposite pull
        combined = director_note.combined_with(actor_note.scaled(ACTOR_FILM_NOTE_WEIGHT))
        self.assertGreater(combined.audience_delta, 0.0)  # director's clarity push still wins out
        self.assertLess(combined.critic_delta, 0.0)


class TestSessionActingScriptNoteStillFullyControlsFit(unittest.TestCase):
    def test_your_part_fit_delta_is_never_scaled(self):
        # your_part only exists on the actor side (fit_delta) — nothing about "the director is the
        # primary creative authority" touches an actor's read on their own performance.
        from callback.engine.core.script_notes import YOUR_PART
        effect = apply_script_note(YOUR_PART)
        self.assertEqual(effect.scaled(ACTOR_FILM_NOTE_WEIGHT).fit_delta, effect.fit_delta)


if __name__ == "__main__":
    unittest.main()
