#!/usr/bin/env python3
"""
Test script for enhanced trigger system.

Run this to test keyword, regex, and semantic matching.
"""

import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from trigger_system import TriggerMatcher


def print_separator(title=""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    else:
        print('-'*60)


def test_keyword_matching():
    """Test enhanced keyword matching"""
    print_separator("TEST 1: KEYWORD MATCHING")

    # Configuration with keyword matching only
    config = {
        'trigger_system': {
            'keyword_matching': {
                'enabled': True,
                'case_sensitive': False,
                'use_word_boundaries': True
            },
            'regex_matching': {'enabled': False},
            'semantic_matching': {'enabled': False}
        }
    }

    matcher = TriggerMatcher(config)
    test_dir = Path(__file__).parent / "test_data"

    # Test messages
    test_cases = [
        ("Marcus is here", "Should match Marcus"),
        ("Marcus's car", "Should match Marcus (possessive)"),
        ("marc said hello", "Should match Marcus (case-insensitive)"),
        ("Marcusian empire", "Should NOT match (word boundary)"),
        ("I went to the restaurant", "Should match Bruno's Restaurant"),
        ("Sarah called me", "Should match Sarah"),
    ]

    for message, expected in test_cases:
        print(f"\nMessage: \"{message}\"")
        print(f"Expected: {expected}")

        matches = matcher.find_triggered_files(
            message,
            test_dir,
            log_callback=lambda msg: print(f"  LOG: {msg}")
        )

        if matches:
            for match in matches:
                print(f"  MATCHED: {match.entity_name} ({match.trigger_type})")
        else:
            print("  NO MATCHES")


def test_regex_matching():
    """Test regex pattern matching"""
    print_separator("TEST 2: REGEX MATCHING")

    # Configuration with regex matching
    config = {
        'trigger_system': {
            'keyword_matching': {'enabled': False},
            'regex_matching': {
                'enabled': True,
                'max_patterns_per_file': 10
            },
            'semantic_matching': {'enabled': False}
        }
    }

    matcher = TriggerMatcher(config)
    test_dir = Path(__file__).parent / "test_data"

    # Test messages with regex patterns
    test_cases = [
        ("Marcus's car is red", "Should match possessive pattern"),
        ("Mark is here too", "Should match Marc/Mark pattern"),
        ("Bruno's Restaurant is great", "Should match Bruno's pattern"),
        ("Brunos Cafe downtown", "Should match Brunos Cafe pattern"),
        ("I saw Marcus' friend", "Should match Marcus' pattern"),
    ]

    for message, expected in test_cases:
        print(f"\nMessage: \"{message}\"")
        print(f"Expected: {expected}")

        matches = matcher.find_triggered_files(
            message,
            test_dir,
            log_callback=lambda msg: print(f"  LOG: {msg}")
        )

        if matches:
            for match in matches:
                print(f"  MATCHED: {match.entity_name} (pattern: {match.matched_pattern})")
        else:
            print("  NO MATCHES")


def test_semantic_matching():
    """Test semantic matching (requires sentence-transformers)"""
    print_separator("TEST 3: SEMANTIC MATCHING")

    # Check if sentence-transformers is available
    try:
        import sentence_transformers
        print("sentence-transformers is installed. Testing semantic matching...")
    except ImportError:
        print("sentence-transformers NOT installed.")
        print("Install with: pip install sentence-transformers")
        print("Skipping semantic matching tests.")
        return

    # Configuration with semantic matching
    config = {
        'trigger_system': {
            'keyword_matching': {'enabled': False},
            'regex_matching': {'enabled': False},
            'semantic_matching': {
                'enabled': True,
                'model': 'all-MiniLM-L6-v2',
                'similarity_threshold': 0.7
            }
        }
    }

    matcher = TriggerMatcher(config)
    test_dir = Path(__file__).parent / "test_data"

    # Test messages with semantic concepts
    test_cases = [
        ("My bodyguard is with me", "Should match 'protective friend'"),
        ("My guardian was there", "Should match 'protective friend'"),
        ("My loyal buddy helped", "Should match 'loyal companion'"),
        ("We went to the pasta place", "Should match 'Italian restaurant'"),
        ("The trattoria was nice", "Should match 'Italian restaurant'"),
        ("My colleague arrived", "Should NOT match (different concept)"),
    ]

    for message, expected in test_cases:
        print(f"\nMessage: \"{message}\"")
        print(f"Expected: {expected}")

        matches = matcher.find_triggered_files(
            message,
            test_dir,
            log_callback=lambda msg: print(f"  LOG: {msg}")
        )

        if matches:
            for match in matches:
                print(f"  MATCHED: {match.entity_name} (concept: '{match.matched_pattern}', confidence: {match.confidence:.3f})")
        else:
            print("  NO MATCHES")


def test_combined_matching():
    """Test all three matching types together"""
    print_separator("TEST 4: COMBINED MATCHING (ALL TYPES)")

    # Configuration with all matching types enabled
    config = {
        'trigger_system': {
            'keyword_matching': {
                'enabled': True,
                'case_sensitive': False,
                'use_word_boundaries': True
            },
            'regex_matching': {
                'enabled': True,
                'max_patterns_per_file': 10
            },
            'semantic_matching': {
                'enabled': True,
                'model': 'all-MiniLM-L6-v2',
                'similarity_threshold': 0.7
            }
        }
    }

    # Check if semantic is available
    try:
        import sentence_transformers
        semantic_available = True
    except ImportError:
        semantic_available = False
        print("Note: Semantic matching disabled (sentence-transformers not installed)\n")
        config['trigger_system']['semantic_matching']['enabled'] = False

    matcher = TriggerMatcher(config)
    test_dir = Path(__file__).parent / "test_data"

    # Test various messages
    test_cases = [
        "Marcus is here",
        "Marc's car is nice",
        "My loyal friend helped",
        "Bruno's Restaurant has great food",
        "The pasta place downtown",
        "Sarah and I worked together",
    ]

    for message in test_cases:
        print(f"\nMessage: \"{message}\"")

        matches = matcher.find_triggered_files(
            message,
            test_dir,
            log_callback=lambda msg: print(f"  {msg}")
        )

        if matches:
            for match in matches:
                info = f"{match.entity_name} ({match.trigger_type}"
                if match.trigger_type == 'semantic':
                    info += f", confidence: {match.confidence:.3f}"
                info += ")"
                print(f"  RESULT: {info}")
        else:
            print("  NO MATCHES")


def main():
    """Run all tests"""
    print("="*60)
    print("  ENHANCED TRIGGER SYSTEM - TEST SUITE")
    print("="*60)

    try:
        # Test 1: Keyword matching
        test_keyword_matching()

        # Test 2: Regex matching
        test_regex_matching()

        # Test 3: Semantic matching
        test_semantic_matching()

        # Test 4: Combined
        test_combined_matching()

        print_separator("TESTS COMPLETE")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
