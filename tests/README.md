# PR Agent Tests

Comprehensive test suite for the PR Agent System, including Phase 3 features.

## Test Structure

### Phase 3 Tests

1. **`test_memory.py`** - Memory system tests
   - Short-term conversation memory
   - Long-term vector memory
   - Session management
   - Memory statistics

2. **`test_evaluation.py`** - Evaluation framework tests
   - Comment quality assessment
   - Batch evaluation
   - Criteria breakdown
   - Evaluation summary

3. **`test_rag.py`** - RAG system tests
   - Comment storage and retrieval
   - Media knowledge management
   - Examples for few-shot learning
   - Context augmentation

4. **`test_phase3_integration.py`** - End-to-end integration tests
   - Complete Phase 3 workflow
   - Memory persistence
   - Evaluation integration
   - Feature statistics

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_memory.py -v
```

### Run Specific Test

```bash
pytest tests/test_memory.py::TestMemoryInitialization::test_memory_disabled_when_config_false -v
```

### Run with Coverage

```bash
pip install pytest-cov
pytest tests/ --cov=pr_agent --cov-report=html
```

## Test Requirements

Most tests use mocking to avoid requiring actual API keys. However, for integration tests with real APIs:

### Required Environment Variables

```env
# For memory and RAG tests
VOYAGE_API_KEY=your_voyage_key

# For evaluation tests
ANTHROPIC_API_KEY=your_anthropic_key

# For full integration tests
SERPER_API_KEY=your_serper_key
EMAIL_FROM=test@example.com
EMAIL_PASSWORD=test_password
```

## Test Coverage

- **Memory System**: 8 test classes, 25+ test cases
- **Evaluation Framework**: 6 test classes, 20+ test cases
- **RAG System**: 9 test classes, 30+ test cases
- **Phase 3 Integration**: 5 test classes, 15+ test cases

**Total**: 90+ test cases covering all Phase 3 features

## Notes

- Tests use mocking extensively to avoid API costs
- Each test class focuses on a specific component
- Error handling is thoroughly tested
- Tests verify graceful degradation when features are disabled
