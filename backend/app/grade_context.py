"""Grade & Course Context Service - Load grade and course-specific curriculum info"""
import os
from typing import Optional, Dict
from functools import lru_cache

# Path to data directories
ROOT = os.path.dirname(__file__)
GRADE_DATA_DIR = os.path.join(ROOT, "..", "grade_data")
COURSE_DATA_DIR = os.path.join(ROOT, "..", "course_data")

# Mapping of grade names to filenames
GRADE_FILES = {
    "Nursery": "Nursery.md",
    "LKG": "LKG.md",
    "UKG": "UKG.md",
    "Grade 1": "Grade1.md",
    "Grade 2": "Grade2.md",
    "Grade 3": "Grade3.md",
    "Grade 4": "Grade4.md",
    "Grade 5": "Grade5.md",
    "Grade 6": "Grade6.md",
    "Grade 7": "Grade7.md",
    "Grade 8": "Grade8.md",
    "Grade 9": "Grade9.md",
    "Grade 10": "Grade10.md",
    "Grade 11": "Grade11.md",
    "Grade 12": "Grade12.md",
}

# Mapping of course names to filenames for Online Classes
COURSE_FILES = {
    "Indian Languages": "IndianLanguages.md",
    "Foreign Languages": "ForeignLanguages.md",
    "Math & Science": "MathScience.md",
    "1-to-1 Math": "OneToOneMath.md",
    "Computer Science": "ComputerScience.md",
    "Coding": "Coding.md",
    "Classical Dance": "ClassicalDance.md",
    "Classical Music": "ClassicalMusic.md",
    "Phonics": "Phonics.md",
    "Public Speaking": "PublicSpeaking.md",
    "Yoga": "Yoga.md",
    "Hobby Classes": "HobbyClasses.md",
}

# Also support short forms
GRADE_ALIASES = {
    "1": "Grade 1", "2": "Grade 2", "3": "Grade 3", "4": "Grade 4",
    "5": "Grade 5", "6": "Grade 6", "7": "Grade 7", "8": "Grade 8",
    "9": "Grade 9", "10": "Grade 10", "11": "Grade 11", "12": "Grade 12",
    "Grade1": "Grade 1", "Grade2": "Grade 2", "Grade3": "Grade 3",
    "Grade4": "Grade 4", "Grade5": "Grade 5", "Grade6": "Grade 6",
    "Grade7": "Grade 7", "Grade8": "Grade 8", "Grade9": "Grade 9",
    "Grade10": "Grade 10", "Grade11": "Grade 11", "Grade12": "Grade 12",
}


def normalize_grade(grade: str) -> str:
    """Normalize grade name to standard format"""
    grade = grade.strip()
    return GRADE_ALIASES.get(grade, grade)


@lru_cache(maxsize=30)
def load_grade_context(grade_or_course: str) -> Optional[str]:
    """Load grade or course context from markdown file (cached)
    
    This function works for both grades (Nursery, LKG, Grade 1-12)
    and courses (Indian Languages, Coding, etc.)
    """
    normalized = normalize_grade(grade_or_course)
    
    # First check if it's a grade
    filename = GRADE_FILES.get(normalized)
    if filename:
        filepath = os.path.join(GRADE_DATA_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error loading grade context for {grade_or_course}: {e}")
                return None
    
    # If not a grade, check if it's a course
    filename = COURSE_FILES.get(grade_or_course.strip())
    if filename:
        filepath = os.path.join(COURSE_DATA_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error loading course context for {grade_or_course}: {e}")
                return None
    
    return None


@lru_cache(maxsize=15)
def load_course_context(course: str) -> Optional[str]:
    """Load course context from markdown file (cached)"""
    filename = COURSE_FILES.get(course.strip())
    
    if not filename:
        return None
    
    filepath = os.path.join(COURSE_DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading course context for {course}: {e}")
        return None


def get_available_grades() -> list:
    """Get list of available grades"""
    available = []
    for grade, filename in GRADE_FILES.items():
        filepath = os.path.join(GRADE_DATA_DIR, filename)
        if os.path.exists(filepath):
            available.append(grade)
    return available


def get_available_courses() -> list:
    """Get list of available courses"""
    available = []
    for course, filename in COURSE_FILES.items():
        filepath = os.path.join(COURSE_DATA_DIR, filename)
        if os.path.exists(filepath):
            available.append(course)
    return available


def clear_context_cache():
    """Clear the cached contexts (useful for updates)"""
    load_grade_context.cache_clear()
    load_course_context.cache_clear()

