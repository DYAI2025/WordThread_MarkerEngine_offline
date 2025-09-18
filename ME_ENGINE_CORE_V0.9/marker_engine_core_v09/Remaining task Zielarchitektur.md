Remaining Work Breakdown
Task 1: Complete Activation Engine Rules
Implement missing activation rules: WEIGHTED_AND, X_OF_Y, AT_LEAST, SUM_WEIGHT, etc.
Update analyze_conversation() in marker_engine_core.py
Add proper threshold testing
Acceptance: 12 golden tests per rule type pass
Task 2: Enhance Conversation Analysis
Improve windowing logic with proper overlap handling
Add evidence cascade tracking (which ATO/SEM activated which higher-level markers)
Include message IDs and spans in evidence
Acceptance: Window size/overlap reproducible, evidence contains Msg-IDs and spans
Task 3: Implement Drift Axes
Create drift axes mapping from aggregated scores
Load drift_axes.zip definitions
Implement event emission for threshold breaches
Acceptance: At least 3 axes with thresholds deliver events in test runs
Task 4: Build HTTP API Service
Implement FastAPI/Flask service with endpoints:
/analyze for conversation analysis
/scores for pure model results
/drift for axes/events
/health for status
Add write-once artifact persistence
Acceptance: JSON validates against 3.4 schemas, engine_digest included
Task 5: Complete Testing & CI
Create golden test suites for each marker family
Add property tests (shuffle invariance)
Implement snapshot timeline tests
Acceptance: CI green, 90%+ branch coverage on composition/scoring
Task 6: Final Integration & Validation
Ensure deterministic output (same input = same output hash)
Validate all composed_of references exist
Test end-to-end pipeline with real conversation data
Acceptance: No phantom hits, consistent scores across runs
Priority Order: 1 → 2 → 3 → 4 → 5 → 6 Estimated Effort: ~40-50 hours remaining for full implementation