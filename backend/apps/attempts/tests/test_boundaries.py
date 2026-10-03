import pytest
from django.apps import apps
from django.db import models


@pytest.mark.django_db
class TestAttemptsModuleBoundaries:
    """
    Architectural boundary tests to verify zero cross-module ORM ForeignKeys
    exist in apps.attempts.
    """

    def test_all_nine_models_exist(self):
        attempts_app = apps.get_app_config("attempts")
        model_names = set(attempts_app.models.keys())
        expected = {
            "attempt",
            "attemptitem",
            "attemptitemchoice",
            "attemptresponse",
            "attemptresponsechoice",
            "attemptresponsematch",
            "attemptevaluation",
            "attemptresult",
            "attemptsectionresult",
        }
        assert model_names == expected

    def test_no_cross_module_orm_relationships(self):
        """
        Verify that EVERY ForeignKey, OneToOneField, and ManyToManyField in apps.attempts
        points exclusively to a model within apps.attempts.
        No relationship may cross module boundaries into identity, learning,
        question_bank, or assessment.
        """
        attempts_app = apps.get_app_config("attempts")
        for model in attempts_app.get_models():
            for field in model._meta.get_fields():
                if field.is_relation and (field.many_to_one or field.one_to_one or field.many_to_many):
                    related_model = field.related_model
                    if related_model:
                        assert related_model._meta.app_label == "attempts", (
                            f"Cross-module relationship violation: "
                            f"{model.__name__}.{field.name} points to "
                            f"{related_model._meta.app_label}.{related_model.__name__}. "
                            f"Cross-module references must be UUID scalar fields only."
                        )

    def test_cross_module_references_are_uuid_scalars(self):
        """
        Verify that fields referencing external domains are plain UUIDFields.
        """
        from apps.attempts.models import (
            Attempt,
            AttemptEvaluation,
            AttemptItem,
            AttemptItemChoice,
            AttemptResponseChoice,
            AttemptResponseMatch,
            AttemptSectionResult,
        )

        assert isinstance(Attempt._meta.get_field("student_id"), models.UUIDField)
        assert isinstance(Attempt._meta.get_field("assessment_paper_id"), models.UUIDField)
        assert isinstance(Attempt._meta.get_field("cancelled_by"), models.UUIDField)

        assert isinstance(AttemptItem._meta.get_field("paper_item_id"), models.UUIDField)
        assert isinstance(AttemptItem._meta.get_field("assessment_section_id"), models.UUIDField)
        assert isinstance(AttemptItem._meta.get_field("question_id"), models.UUIDField)
        assert isinstance(AttemptItem._meta.get_field("question_version_id"), models.UUIDField)

        assert isinstance(AttemptItemChoice._meta.get_field("choice_id"), models.UUIDField)
        assert isinstance(AttemptResponseChoice._meta.get_field("choice_id"), models.UUIDField)

        assert isinstance(AttemptResponseMatch._meta.get_field("left_item_id"), models.UUIDField)
        assert isinstance(AttemptResponseMatch._meta.get_field("right_item_id"), models.UUIDField)

        assert isinstance(AttemptEvaluation._meta.get_field("evaluator_id"), models.UUIDField)
        assert isinstance(AttemptSectionResult._meta.get_field("assessment_section_id"), models.UUIDField)
