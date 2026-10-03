import uuid
import pytest
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError

from apps.learning.models import Chapter, Domain, Subject, Topic


@pytest.mark.django_db
class TestLearningModelIdentity:
    def test_domain_creation_and_uuid_pk(self):
        domain = Domain.objects.create(name="Civil Services", description="Civil Services exam prep")
        assert isinstance(domain.id, uuid.UUID)
        assert domain.name == "Civil Services"
        assert domain.description == "Civil Services exam prep"
        assert domain.created_at is not None
        assert domain.updated_at is not None
        assert str(domain) == "Civil Services"

    def test_subject_belongs_to_domain(self):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="Polity", position=1)
        assert isinstance(subject.id, uuid.UUID)
        assert subject.domain == domain
        assert subject.name == "Polity"
        assert subject.position == 1
        assert subject.description == ""
        assert str(subject) == "Polity"
        assert list(domain.subjects.all()) == [subject]

    def test_chapter_belongs_to_subject(self):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="Polity")
        chapter = Chapter.objects.create(subject=subject, name="Preamble", position=2)
        assert isinstance(chapter.id, uuid.UUID)
        assert chapter.subject == subject
        assert chapter.name == "Preamble"
        assert chapter.position == 2
        assert chapter.description == ""
        assert str(chapter) == "Preamble"
        assert list(subject.chapters.all()) == [chapter]

    def test_topic_belongs_to_chapter(self):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="Polity")
        chapter = Chapter.objects.create(subject=subject, name="Preamble")
        topic = Topic.objects.create(chapter=chapter, name="Significance of Preamble", position=1)
        assert isinstance(topic.id, uuid.UUID)
        assert topic.chapter == chapter
        assert topic.name == "Significance of Preamble"
        assert topic.position == 1
        assert topic.description == ""
        assert str(topic) == "Significance of Preamble"
        assert list(chapter.topics.all()) == [topic]

    def test_default_values(self):
        domain = Domain.objects.create(name="Engineering")
        subject = Subject.objects.create(domain=domain, name="Computer Science")
        chapter = Chapter.objects.create(subject=subject, name="Algorithms")
        topic = Topic.objects.create(chapter=chapter, name="Sorting")

        assert domain.description == ""
        assert subject.description == ""
        assert subject.position == 0
        assert chapter.description == ""
        assert chapter.position == 0
        assert topic.description == ""
        assert topic.position == 0


@pytest.mark.django_db
class TestLearningModelHierarchyProtection:
    def test_domain_cannot_be_deleted_when_subject_exists(self):
        domain = Domain.objects.create(name="Civil Services")
        Subject.objects.create(domain=domain, name="History")

        with pytest.raises(ProtectedError):
            domain.delete()

    def test_subject_cannot_be_deleted_when_chapter_exists(self):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="History")
        Chapter.objects.create(subject=subject, name="Ancient India")

        with pytest.raises(ProtectedError):
            subject.delete()

    def test_chapter_cannot_be_deleted_when_topic_exists(self):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="History")
        chapter = Chapter.objects.create(subject=subject, name="Ancient India")
        Topic.objects.create(chapter=chapter, name="Indus Valley Civilization")

        with pytest.raises(ProtectedError):
            chapter.delete()

    def test_leaf_topic_can_be_deleted(self):
        domain = Domain.objects.create(name="Civil Services")
        subject = Subject.objects.create(domain=domain, name="History")
        chapter = Chapter.objects.create(subject=subject, name="Ancient India")
        topic = Topic.objects.create(chapter=chapter, name="Indus Valley Civilization")

        topic_id = topic.id
        topic.delete()
        assert not Topic.objects.filter(id=topic_id).exists()

        # Chapter can now be deleted since it has no topics
        chapter_id = chapter.id
        chapter.delete()
        assert not Chapter.objects.filter(id=chapter_id).exists()


@pytest.mark.django_db
class TestLearningModelNameUniqueness:
    def test_domain_name_unique_case_insensitive_db(self):
        Domain.objects.create(name="History")
        with pytest.raises(IntegrityError):
            Domain.objects.create(name="history")

    def test_domain_name_unique_case_insensitive_clean(self):
        Domain.objects.create(name="History")
        duplicate = Domain(name="HISTORY")
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_subject_name_unique_case_insensitive_within_domain_db(self):
        domain = Domain.objects.create(name="UPSC")
        Subject.objects.create(domain=domain, name="History")

        with pytest.raises(IntegrityError):
            Subject.objects.create(domain=domain, name="history")

    def test_subject_name_unique_case_insensitive_within_domain_clean(self):
        domain = Domain.objects.create(name="UPSC")
        Subject.objects.create(domain=domain, name="History")

        duplicate = Subject(domain=domain, name="HISTORY")
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_subject_same_name_allowed_under_different_domains(self):
        d1 = Domain.objects.create(name="UPSC")
        d2 = Domain.objects.create(name="Engineering")

        s1 = Subject.objects.create(domain=d1, name="History")
        s2 = Subject.objects.create(domain=d2, name="History")

        assert s1.id != s2.id
        assert s1.domain != s2.domain

    def test_chapter_name_unique_case_insensitive_within_subject_db(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="History")
        Chapter.objects.create(subject=subject, name="Modern India")

        with pytest.raises(IntegrityError):
            Chapter.objects.create(subject=subject, name="modern india")

    def test_chapter_name_unique_case_insensitive_within_subject_clean(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="History")
        Chapter.objects.create(subject=subject, name="Modern India")

        duplicate = Chapter(subject=subject, name="MODERN INDIA")
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_chapter_same_name_allowed_under_different_subjects(self):
        domain = Domain.objects.create(name="UPSC")
        s1 = Subject.objects.create(domain=domain, name="History")
        s2 = Subject.objects.create(domain=domain, name="Sociology")

        c1 = Chapter.objects.create(subject=s1, name="Introductory Concepts")
        c2 = Chapter.objects.create(subject=s2, name="Introductory Concepts")

        assert c1.id != c2.id
        assert c1.subject != c2.subject

    def test_topic_name_unique_case_insensitive_within_chapter_db(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="History")
        chapter = Chapter.objects.create(subject=subject, name="Modern India")
        Topic.objects.create(chapter=chapter, name="Revolt of 1857")

        with pytest.raises(IntegrityError):
            Topic.objects.create(chapter=chapter, name="revolt of 1857")

    def test_topic_name_unique_case_insensitive_within_chapter_clean(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="History")
        chapter = Chapter.objects.create(subject=subject, name="Modern India")
        Topic.objects.create(chapter=chapter, name="Revolt of 1857")

        duplicate = Topic(chapter=chapter, name="REVOLT OF 1857")
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_topic_same_name_allowed_under_different_chapters(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="History")
        c1 = Chapter.objects.create(subject=subject, name="Phase 1")
        c2 = Chapter.objects.create(subject=subject, name="Phase 2")

        t1 = Topic.objects.create(chapter=c1, name="Summary and Key Dates")
        t2 = Topic.objects.create(chapter=c2, name="Summary and Key Dates")

        assert t1.id != t2.id
        assert t1.chapter != t2.chapter


@pytest.mark.django_db
class TestLearningModelWhitespaceNormalization:
    def test_domain_save_normalizes_whitespace(self):
        domain = Domain.objects.create(name="   Indian   Polity   ")
        assert domain.name == "Indian Polity"

    def test_domain_clean_normalizes_whitespace(self):
        domain = Domain(name="   Indian   Polity   ")
        domain.full_clean()
        assert domain.name == "Indian Polity"

    def test_subject_save_normalizes_whitespace(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="   Indian    Polity   ")
        assert subject.name == "Indian Polity"

    def test_chapter_save_normalizes_whitespace(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="Polity")
        chapter = Chapter.objects.create(subject=subject, name="   Fundamental   Rights   ")
        assert chapter.name == "Fundamental Rights"

    def test_topic_save_normalizes_whitespace(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="Polity")
        chapter = Chapter.objects.create(subject=subject, name="Fundamental Rights")
        topic = Topic.objects.create(chapter=chapter, name="   Right   to   Equality   ")
        assert topic.name == "Right to Equality"

    def test_whitespace_and_case_variants_rejected_as_duplicates(self):
        domain = Domain.objects.create(name="Indian Polity")
        # Leading/trailing whitespace + different casing
        with pytest.raises(IntegrityError):
            Domain.objects.create(name="   indian   polity   ")


@pytest.mark.django_db
class TestLearningModelOrdering:
    def test_domain_ordering_by_name(self):
        Domain.objects.create(name="Science")
        Domain.objects.create(name="Arts")
        Domain.objects.create(name="Commerce")

        names = list(Domain.objects.values_list("name", flat=True))
        assert names == ["Arts", "Commerce", "Science"]

    def test_subject_ordering_by_position_and_name(self):
        domain = Domain.objects.create(name="UPSC")
        Subject.objects.create(domain=domain, name="Economics", position=2)
        Subject.objects.create(domain=domain, name="Polity", position=1)
        Subject.objects.create(domain=domain, name="History", position=1)
        Subject.objects.create(domain=domain, name="Ethics", position=0)

        names = list(Subject.objects.values_list("name", flat=True))
        # position 0: Ethics
        # position 1: History, Polity (alphabetical on name)
        # position 2: Economics
        assert names == ["Ethics", "History", "Polity", "Economics"]

    def test_chapter_ordering_by_position_and_name(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="Polity")
        Chapter.objects.create(subject=subject, name="Judiciary", position=2)
        Chapter.objects.create(subject=subject, name="Parliament", position=1)
        Chapter.objects.create(subject=subject, name="Executive", position=1)
        Chapter.objects.create(subject=subject, name="Preamble", position=0)

        names = list(Chapter.objects.values_list("name", flat=True))
        assert names == ["Preamble", "Executive", "Parliament", "Judiciary"]

    def test_topic_ordering_by_position_and_name(self):
        domain = Domain.objects.create(name="UPSC")
        subject = Subject.objects.create(domain=domain, name="Polity")
        chapter = Chapter.objects.create(subject=subject, name="Preamble")
        Topic.objects.create(chapter=chapter, name="Socialist Secular", position=2)
        Topic.objects.create(chapter=chapter, name="Preamble Text", position=1)
        Topic.objects.create(chapter=chapter, name="Historical Background", position=1)
        Topic.objects.create(chapter=chapter, name="Introduction", position=0)

        names = list(Topic.objects.values_list("name", flat=True))
        assert names == ["Introduction", "Historical Background", "Preamble Text", "Socialist Secular"]
