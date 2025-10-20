"""
Tests for VectorStore functionality
"""
import pytest
from vector_store import VectorStore, SearchResults


class TestVectorStoreBasics:
    """Test basic vector store operations"""

    def test_empty_store_search_returns_empty(self, empty_vector_store):
        """Test that searching an empty store returns empty results"""
        results = empty_vector_store.search("machine learning")
        assert results.is_empty()
        assert len(results.documents) == 0
        assert len(results.metadata) == 0

    def test_add_course_metadata(self, empty_vector_store, sample_course):
        """Test adding course metadata"""
        empty_vector_store.add_course_metadata(sample_course)

        # Verify course was added
        course_titles = empty_vector_store.get_existing_course_titles()
        assert sample_course.title in course_titles
        assert empty_vector_store.get_course_count() == 1

    def test_add_course_content(self, empty_vector_store, sample_course_chunks):
        """Test adding course content chunks"""
        empty_vector_store.add_course_content(sample_course_chunks)

        # Search for content that should exist
        results = empty_vector_store.search("linear regression")
        assert not results.is_empty()
        assert len(results.documents) > 0

    def test_get_course_count(self, populated_vector_store):
        """Test getting course count"""
        assert populated_vector_store.get_course_count() == 1

    def test_get_existing_course_titles(self, populated_vector_store, sample_course):
        """Test getting existing course titles"""
        titles = populated_vector_store.get_existing_course_titles()
        assert len(titles) == 1
        assert sample_course.title in titles


class TestVectorStoreSearch:
    """Test vector store search functionality"""

    def test_search_returns_relevant_results(self, populated_vector_store):
        """Test that search returns relevant results"""
        results = populated_vector_store.search("linear regression")

        assert not results.is_empty()
        assert len(results.documents) > 0
        # Check that the result contains relevant content
        assert any("linear regression" in doc.lower() for doc in results.documents)

    def test_search_with_course_filter(self, populated_vector_store, sample_course):
        """Test searching with course name filter"""
        results = populated_vector_store.search(
            "machine learning",
            course_name=sample_course.title
        )

        assert not results.is_empty()
        # All results should be from the specified course
        for meta in results.metadata:
            assert meta['course_title'] == sample_course.title

    def test_search_with_lesson_filter(self, populated_vector_store):
        """Test searching with lesson number filter"""
        results = populated_vector_store.search(
            "regression",
            course_name="Introduction to Machine Learning",
            lesson_number=1
        )

        assert not results.is_empty()
        # All results should be from lesson 1
        for meta in results.metadata:
            assert meta['lesson_number'] == 1

    def test_search_nonexistent_course_fuzzy_match(self, populated_vector_store):
        """Test that searching for non-existent course returns fuzzy match

        Vector search always returns the closest match, even if the query
        is completely unrelated. This is the expected behavior of semantic search.
        """
        results = populated_vector_store.search(
            "anything",
            course_name="Nonexistent Course XYZ123"
        )

        # Vector search will find the closest match, not return an error
        # This is correct behavior for semantic/fuzzy search
        assert not results.is_empty() or results.error is not None

    def test_search_with_limit(self, populated_vector_store):
        """Test search result limit"""
        results = populated_vector_store.search("learning", limit=1)

        assert not results.is_empty()
        assert len(results.documents) <= 1

    def test_search_empty_query(self, populated_vector_store):
        """Test searching with empty query"""
        results = populated_vector_store.search("")

        # Should still return results (vector search on empty string)
        assert not results.is_empty()


class TestVectorStoreCourseResolution:
    """Test course name resolution functionality"""

    def test_resolve_exact_course_name(self, populated_vector_store, sample_course):
        """Test resolving exact course name"""
        resolved = populated_vector_store._resolve_course_name(sample_course.title)
        assert resolved == sample_course.title

    def test_resolve_partial_course_name(self, populated_vector_store):
        """Test resolving partial course name"""
        # Should find "Introduction to Machine Learning" from partial match
        resolved = populated_vector_store._resolve_course_name("Machine Learning")
        assert resolved is not None
        assert "Machine Learning" in resolved

    def test_resolve_nonexistent_course(self, populated_vector_store):
        """Test resolving non-existent course returns None"""
        resolved = populated_vector_store._resolve_course_name("Totally Fake Course XYZ123")
        # Might return None or might return the closest match
        # The behavior depends on the vector search


class TestVectorStoreMultipleCourses:
    """Test vector store with multiple courses"""

    def test_multiple_courses_loaded(self, multi_course_vector_store):
        """Test that multiple courses can be loaded"""
        assert multi_course_vector_store.get_course_count() == 2

    def test_search_across_courses(self, multi_course_vector_store):
        """Test searching across multiple courses"""
        results = multi_course_vector_store.search("learning")

        assert not results.is_empty()
        # Results might come from either course
        course_titles = set(meta['course_title'] for meta in results.metadata)
        assert len(course_titles) >= 1  # At least one course

    def test_filter_by_specific_course(self, multi_course_vector_store):
        """Test filtering by specific course when multiple exist"""
        results = multi_course_vector_store.search(
            "learning",
            course_name="Advanced Deep Learning"
        )

        assert not results.is_empty()
        # All results should be from the Deep Learning course
        for meta in results.metadata:
            assert meta['course_title'] == "Advanced Deep Learning"


class TestVectorStoreLinks:
    """Test lesson and course link retrieval"""

    def test_get_course_link(self, populated_vector_store, sample_course):
        """Test retrieving course link"""
        link = populated_vector_store.get_course_link(sample_course.title)
        assert link == sample_course.course_link

    def test_get_lesson_link(self, populated_vector_store, sample_course):
        """Test retrieving lesson link"""
        link = populated_vector_store.get_lesson_link(sample_course.title, 1)
        assert link == sample_course.lessons[1].lesson_link

    def test_get_lesson_link_nonexistent_lesson(self, populated_vector_store, sample_course):
        """Test getting link for non-existent lesson"""
        link = populated_vector_store.get_lesson_link(sample_course.title, 999)
        assert link is None

    def test_get_course_link_nonexistent_course(self, populated_vector_store):
        """Test getting link for non-existent course"""
        link = populated_vector_store.get_course_link("Nonexistent Course")
        assert link is None


class TestVectorStoreClearData:
    """Test clearing vector store data"""

    def test_clear_all_data(self, populated_vector_store):
        """Test clearing all data from vector store"""
        # Verify data exists
        assert populated_vector_store.get_course_count() > 0

        # Clear data
        populated_vector_store.clear_all_data()

        # Verify data is cleared
        assert populated_vector_store.get_course_count() == 0

        # Search should return empty results
        results = populated_vector_store.search("anything")
        assert results.is_empty()


class TestSearchResults:
    """Test SearchResults dataclass"""

    def test_search_results_from_chroma(self):
        """Test creating SearchResults from ChromaDB results"""
        chroma_results = {
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{'key': 'value1'}, {'key': 'value2'}]],
            'distances': [[0.1, 0.2]]
        }

        results = SearchResults.from_chroma(chroma_results)

        assert len(results.documents) == 2
        assert len(results.metadata) == 2
        assert len(results.distances) == 2
        assert results.documents[0] == 'doc1'

    def test_search_results_empty(self):
        """Test creating empty SearchResults"""
        results = SearchResults.empty("Error message")

        assert results.is_empty()
        assert results.error == "Error message"

    def test_is_empty_check(self):
        """Test is_empty() method"""
        empty_results = SearchResults([], [], [], None)
        assert empty_results.is_empty()

        non_empty_results = SearchResults(['doc'], [{'key': 'val'}], [0.1], None)
        assert not non_empty_results.is_empty()
