"""
Shared test fixtures for RAG system tests
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add backend to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models import Course, CourseChunk, Lesson
from search_tools import CourseSearchTool, ToolManager
from vector_store import VectorStore


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary ChromaDB directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_config(temp_chroma_dir):
    """Create a test configuration"""
    config = Config()
    config.CHROMA_PATH = temp_chroma_dir
    config.MAX_RESULTS = 3
    return config


@pytest.fixture
def sample_course():
    """Create a sample course for testing"""
    return Course(
        title="Introduction to Machine Learning",
        course_link="https://example.com/ml-course",
        instructor="Dr. Jane Smith",
        lessons=[
            Lesson(lesson_number=0, title="Course Overview", lesson_link="https://example.com/ml-course/lesson-0"),
            Lesson(
                lesson_number=1, title="Linear Regression Basics", lesson_link="https://example.com/ml-course/lesson-1"
            ),
            Lesson(
                lesson_number=2, title="Classification Algorithms", lesson_link="https://example.com/ml-course/lesson-2"
            ),
        ],
    )


@pytest.fixture
def sample_course_chunks():
    """Create sample course chunks for testing"""
    return [
        CourseChunk(
            content="Lesson 0 content: This course covers fundamental concepts in machine learning including supervised and unsupervised learning.",
            course_title="Introduction to Machine Learning",
            lesson_number=0,
            chunk_index=0,
        ),
        CourseChunk(
            content="Linear regression is a fundamental algorithm used for predicting continuous values. It finds the best-fitting line through data points.",
            course_title="Introduction to Machine Learning",
            lesson_number=1,
            chunk_index=1,
        ),
        CourseChunk(
            content="Classification algorithms are used to predict categorical outcomes. Common examples include logistic regression, decision trees, and neural networks.",
            course_title="Introduction to Machine Learning",
            lesson_number=2,
            chunk_index=2,
        ),
    ]


@pytest.fixture
def another_sample_course():
    """Create another sample course for testing multi-course scenarios"""
    return Course(
        title="Advanced Deep Learning",
        course_link="https://example.com/dl-course",
        instructor="Prof. John Doe",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Neural Networks Introduction",
                lesson_link="https://example.com/dl-course/lesson-0",
            )
        ],
    )


@pytest.fixture
def another_course_chunks():
    """Create chunks for the second course"""
    return [
        CourseChunk(
            content="Deep learning uses neural networks with multiple layers to learn complex patterns in data.",
            course_title="Advanced Deep Learning",
            lesson_number=0,
            chunk_index=0,
        )
    ]


@pytest.fixture
def empty_vector_store(test_config):
    """Create an empty vector store for testing"""
    return VectorStore(test_config.CHROMA_PATH, test_config.EMBEDDING_MODEL, test_config.MAX_RESULTS)


@pytest.fixture
def populated_vector_store(empty_vector_store, sample_course, sample_course_chunks):
    """Create a vector store with sample data loaded"""
    empty_vector_store.add_course_metadata(sample_course)
    empty_vector_store.add_course_content(sample_course_chunks)
    return empty_vector_store


@pytest.fixture
def multi_course_vector_store(populated_vector_store, another_sample_course, another_course_chunks):
    """Create a vector store with multiple courses"""
    populated_vector_store.add_course_metadata(another_sample_course)
    populated_vector_store.add_course_content(another_course_chunks)
    return populated_vector_store


@pytest.fixture
def course_search_tool(populated_vector_store):
    """Create a CourseSearchTool with populated data"""
    return CourseSearchTool(populated_vector_store)


@pytest.fixture
def tool_manager(course_search_tool):
    """Create a ToolManager with CourseSearchTool registered"""
    manager = ToolManager()
    manager.register_tool(course_search_tool)
    return manager


@pytest.fixture
def sample_course_document_text():
    """Sample course document text for document processor testing"""
    return """Course Title: Introduction to Machine Learning
Course Link: https://example.com/ml-course
Course Instructor: Dr. Jane Smith

Lesson 0: Course Overview
Lesson Link: https://example.com/ml-course/lesson-0
This course covers fundamental concepts in machine learning including supervised and unsupervised learning.

Lesson 1: Linear Regression Basics
Lesson Link: https://example.com/ml-course/lesson-1
Linear regression is a fundamental algorithm used for predicting continuous values. It finds the best-fitting line through data points.

Lesson 2: Classification Algorithms
Lesson Link: https://example.com/ml-course/lesson-2
Classification algorithms are used to predict categorical outcomes. Common examples include logistic regression, decision trees, and neural networks.
"""


@pytest.fixture
def temp_course_file(sample_course_document_text):
    """Create a temporary course document file"""
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    temp_file.write(sample_course_document_text)
    temp_file.close()
    yield temp_file.name
    # Cleanup
    Path(temp_file.name).unlink(missing_ok=True)
