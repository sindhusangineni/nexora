import uuid
import pytest
from apps.assessment.adapters.question_bank import DatabaseQuestionBankCandidateAdapter
from apps.assessment.models import (
    Difficulty,
    QuestionType,
    ScopeType,
)
from apps.learning.models import Chapter, Domain, Subject, Topic
from apps.question_bank.models import Question, QuestionTopic, QuestionVersion


@pytest.mark.django_db
class TestSelectionRulesAndCandidateAdapter:
    @pytest.fixture
    def taxonomy_tree(self):
        domain = Domain.objects.create(name="General Studies")
        subject = Subject.objects.create(domain=domain, name="Indian Polity")
        chapter = Chapter.objects.create(subject=subject, name="Preamble")
        topic1 = Topic.objects.create(chapter=chapter, name="Historical Background")
        topic2 = Topic.objects.create(chapter=chapter, name="Salient Features")
        return {
            "domain": domain,
            "subject": subject,
            "chapter": chapter,
            "topic1": topic1,
            "topic2": topic2,
        }

    def _create_question_with_version(self, topic, q_type="MCQ", difficulty="EASY", status="PUBLISHED"):
        q = Question.objects.create()
        QuestionTopic.objects.create(question=q, topic=topic)
        qv = QuestionVersion.objects.create(
            question=q,
            version_number=1,
            question_type=q_type,
            difficulty=difficulty,
            text=f"Question text for {q.id}",
            status="DRAFT",
        )
        if status != "DRAFT":
            QuestionVersion.objects.filter(pk=qv.pk).update(status=status)
            qv.refresh_from_db()
        return q, qv

    def test_adapter_topic_scope_published_only(self, taxonomy_tree):
        t1 = taxonomy_tree["topic1"]
        q1, v1 = self._create_question_with_version(t1, status="PUBLISHED")
        q2, v2 = self._create_question_with_version(t1, status="DRAFT")  # Should be excluded

        adapter = DatabaseQuestionBankCandidateAdapter()
        candidates = adapter.get_published_candidates(
            scope_type=ScopeType.TOPIC,
            scope_id=t1.id,
        )
        assert len(candidates) == 1
        assert candidates[0].question_id == q1.id
        assert candidates[0].question_version_id == v1.id

    def test_adapter_chapter_scope_aggregation(self, taxonomy_tree):
        t1 = taxonomy_tree["topic1"]
        t2 = taxonomy_tree["topic2"]
        ch = taxonomy_tree["chapter"]

        q1, v1 = self._create_question_with_version(t1, status="PUBLISHED")
        q2, v2 = self._create_question_with_version(t2, status="PUBLISHED")

        adapter = DatabaseQuestionBankCandidateAdapter()
        candidates = adapter.get_published_candidates(
            scope_type=ScopeType.CHAPTER,
            scope_id=ch.id,
        )
        cand_ids = {c.question_id for c in candidates}
        assert cand_ids == {q1.id, q2.id}

    def test_adapter_subject_and_domain_scope(self, taxonomy_tree):
        t1 = taxonomy_tree["topic1"]
        sub = taxonomy_tree["subject"]
        dom = taxonomy_tree["domain"]

        q1, v1 = self._create_question_with_version(t1, status="PUBLISHED")

        adapter = DatabaseQuestionBankCandidateAdapter()

        sub_candidates = adapter.get_published_candidates(
            scope_type=ScopeType.SUBJECT,
            scope_id=sub.id,
        )
        assert len(sub_candidates) == 1
        assert sub_candidates[0].question_id == q1.id

        dom_candidates = adapter.get_published_candidates(
            scope_type=ScopeType.DOMAIN,
            scope_id=dom.id,
        )
        assert len(dom_candidates) == 1
        assert dom_candidates[0].question_id == q1.id

    def test_adapter_filter_by_question_type_and_difficulty(self, taxonomy_tree):
        t1 = taxonomy_tree["topic1"]
        q1, v1 = self._create_question_with_version(t1, q_type="MCQ", difficulty="EASY", status="PUBLISHED")
        q2, v2 = self._create_question_with_version(t1, q_type="DESCRIPTIVE", difficulty="HARD", status="PUBLISHED")

        adapter = DatabaseQuestionBankCandidateAdapter()

        # Filter by MCQ
        mcq_cands = adapter.get_published_candidates(
            scope_type=ScopeType.TOPIC,
            scope_id=t1.id,
            question_type=QuestionType.MCQ,
        )
        assert len(mcq_cands) == 1
        assert mcq_cands[0].question_id == q1.id

        # Filter by HARD
        hard_cands = adapter.get_published_candidates(
            scope_type=ScopeType.TOPIC,
            scope_id=t1.id,
            difficulty=Difficulty.HARD,
        )
        assert len(hard_cands) == 1
        assert hard_cands[0].question_id == q2.id

        # Non-matching filter
        none_cands = adapter.get_published_candidates(
            scope_type=ScopeType.TOPIC,
            scope_id=t1.id,
            question_type=QuestionType.TRUE_FALSE,
        )
        assert len(none_cands) == 0

    def test_adapter_unknown_scope_returns_empty(self):
        adapter = DatabaseQuestionBankCandidateAdapter()
        candidates = adapter.get_published_candidates(
            scope_type="UNKNOWN",
            scope_id=uuid.uuid4(),
        )
        assert candidates == []
