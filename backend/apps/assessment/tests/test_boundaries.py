import ast
from pathlib import Path
import pytest
from django.apps import apps
from django.db import models


@pytest.mark.django_db
class TestAssessmentModuleBoundaries:
    """
    Architectural boundary tests to verify zero cross-module ORM ForeignKeys
    exist in apps.assessment and no external domain models are statically imported.
    """

    def test_all_five_models_exist(self):
        assessment_app = apps.get_app_config("assessment")
        model_names = set(assessment_app.models.keys())
        expected = {
            "assessment",
            "assessmentsection",
            "selectionrule",
            "assessmentpaper",
            "assessmentpaperitem",
        }
        assert model_names == expected

    def test_no_cross_module_orm_relationships(self):
        """
        Verify that EVERY ForeignKey, OneToOneField, and ManyToManyField in apps.assessment
        points exclusively to a model within apps.assessment.
        No relationship may cross module boundaries into identity, learning,
        question_bank, or attempts.
        """
        assessment_app = apps.get_app_config("assessment")
        for model in assessment_app.get_models():
            for field in model._meta.get_fields():
                if field.is_relation and (field.many_to_one or field.one_to_one or field.many_to_many):
                    related_model = field.related_model
                    if related_model:
                        assert related_model._meta.app_label == "assessment", (
                            f"Cross-module relationship violation: "
                            f"{model.__name__}.{field.name} points to "
                            f"{related_model._meta.app_label}.{related_model.__name__}. "
                            f"Cross-module references must be UUID scalar fields only."
                        )

    def test_cross_module_references_are_uuid_scalars(self):
        """
        Verify that fields referencing external domains are plain UUIDFields.
        """
        from apps.assessment.models import (
            AssessmentPaperItem,
            SelectionRule,
        )

        assert isinstance(SelectionRule._meta.get_field("scope_id"), models.UUIDField)
        assert isinstance(AssessmentPaperItem._meta.get_field("question_id"), models.UUIDField)
        assert isinstance(AssessmentPaperItem._meta.get_field("question_version_id"), models.UUIDField)

    def test_no_external_model_imports_in_assessment_module(self):
        """
        Scan all python files in apps/assessment/ to ensure no files import
        models from question_bank, learning, attempts, or identity.
        """
        forbidden_import_prefixes = [
            "apps.question_bank.models",
            "apps.learning.models",
            "apps.attempts.models",
            "apps.identity.models",
        ]

        app_dir = Path(__file__).resolve().parent.parent
        py_files = [f for f in app_dir.rglob("*.py") if "tests" not in f.parts]

        violations = []
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_import_prefixes:
                            if alias.name.startswith(forbidden):
                                violations.append((str(py_file), alias.name))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for forbidden in forbidden_import_prefixes:
                            if node.module.startswith(forbidden):
                                violations.append((str(py_file), node.module))

        assert not violations, f"Forbidden cross-module model imports detected: {violations}"
