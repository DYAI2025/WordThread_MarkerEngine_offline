# AI Coding Assistant Instructions

## Project Overview

This is a multi-project workspace focused on AI-powered conversation analysis and automation systems. The workspace contains four main projects:

- **gemini-cli**: Node.js/TypeScript CLI tool for AI workflow automation with Google Gemini
- **MarkThread**: Python/Streamlit frontend for marker engine data visualization
- **PROMATRA**: Python audio processing system for speech analysis and transcription
- **ME_ENGINE_CORE_V0.9**: Python conversation analysis engine with marker detection

## Architecture Patterns

### Modular Monorepo Structure
- **CLI Package** (`packages/cli`): User-facing interface with React/Ink components
- **Core Package** (`packages/core`): Backend logic with Gemini API integration and tool execution
- **VS Code Companion** (`packages/vscode-ide-companion`): IDE integration via MCP server
- **Python Components**: ML/data processing with FastAPI services and Streamlit frontends

### Key Design Principles
- **MCP Integration**: Model Context Protocol for extensible tool system
- **Hierarchical Memory**: GEMINI.md files for contextual AI instructions
- **Functional Architecture**: Plain objects over classes, immutable state updates
- **ES Module Encapsulation**: Explicit import/export boundaries

## Critical Developer Workflows

### Build & Validation (gemini-cli)
```bash
# Comprehensive preflight check (build + test + lint + typecheck)
npm run preflight

# Individual steps
npm run build        # Build all packages
npm run test:ci      # Run tests with coverage
npm run lint:ci      # ESLint with no warnings
npm run typecheck    # TypeScript validation
```

### Testing Patterns
- **Framework**: Vitest with `describe`/`it`/`expect`/`vi`
- **Mocking**: `vi.mock()` at top of files for ES modules
- **Common Mocks**: `fs`, `fs/promises`, `os`, `@google/genai`, internal packages
- **React Testing**: `ink-testing-library` for CLI components

### Custom CLI Commands
Commands defined in TOML files at `~/.gemini/commands/` or `<project>/.gemini/commands/`:
```toml
description = "Command description"
prompt = "AI instruction template with {{args}} for user input"
```

## Project-Specific Conventions

### JavaScript/TypeScript
- **Prefer Plain Objects**: Use interfaces/types over classes for data structures
- **Functional Programming**: Leverage `.map()`, `.filter()`, `.reduce()` for data transformation
- **ES Module Boundaries**: Export only public APIs, keep internals private
- **Avoid `any` Types**: Use `unknown` with type narrowing instead
- **Immutable Updates**: Always create new objects/arrays for state changes

### React/Ink Components (CLI UI)
- **Functional Components**: No class components, use hooks exclusively
- **Pure Rendering**: No side effects in component bodies
- **One-Way Data Flow**: Props down, events up
- **Effect Usage**: Only for external synchronization, include all dependencies
- **Refs**: Only when absolutely necessary (focus, animations, non-React integration)

### Python Components
- **FastAPI Services**: RESTful APIs for core engines
- **Streamlit Frontends**: Data visualization with reactive components
- **Data Processing**: Pandas/NumPy for analysis, JSON Lines for data exchange

## Integration Patterns

### Cross-Component Communication
- **MCP Servers**: Tool registration and execution between CLI and external systems
- **Data Formats**: JSON/JSONL for structured data exchange
- **API Contracts**: REST endpoints with consistent response schemas
- **File-Based Coordination**: Shared data files between Python and Node.js components

### External Dependencies
- **Google Gemini API**: Primary AI model integration
- **Google Cloud Services**: Authentication and deployment
- **Audio Processing**: Whisper, librosa for speech analysis
- **Data Visualization**: Plotly, Streamlit for interactive dashboards

## Development Best Practices

### Code Organization
- **Co-located Tests**: `*.test.ts` files alongside source files
- **Feature Modules**: Group related functionality in dedicated directories
- **Configuration Hierarchy**: Project-specific settings override global defaults

### Quality Gates
- **Type Safety**: Strict TypeScript with no `any` types
- **Test Coverage**: Comprehensive Vitest suites with proper mocking
- **Code Style**: ESLint with Prettier formatting
- **Build Validation**: Automated preflight checks before commits

### Performance Considerations
- **Lazy Loading**: Dynamic imports for large modules
- **Caching**: Token caching for API efficiency
- **Memory Management**: Proper cleanup in effects and event handlers
- **Concurrent Rendering**: Code that works with React's concurrent features

## Common Patterns & Examples

### CLI Command Definition
```toml
description = "Analyze code changes for security issues"
prompt = """
Review the following code changes for security vulnerabilities:
{{args}}

Focus on:
- Input validation
- Authentication bypasses
- Data exposure risks
- Injection vulnerabilities
"""
```

### React Component Structure
```typescript
function AnalysisPanel({ data, onUpdate }: Props) {
  const [filteredData, setFilteredData] = useState(data);

  useEffect(() => {
    // External synchronization only
    const subscription = externalService.subscribe(onUpdate);
    return () => subscription.unsubscribe();
  }, [onUpdate]);

  const handleFilter = useCallback((criteria: FilterCriteria) => {
    const filtered = data.filter(item => matchesCriteria(item, criteria));
    setFilteredData(filtered);
  }, [data]);

  return (
    <Box flexDirection="column">
      <FilterControls onFilter={handleFilter} />
      <DataDisplay data={filteredData} />
    </Box>
  );
}
```

### Python Data Processing
```python
def process_conversation_data(messages: List[Dict], config: Dict) -> AnalysisResult:
    """Process conversation messages with marker detection."""
    # Functional approach with immutable data
    processed = [
        {**msg, "markers": detect_markers(msg["text"], config)}
        for msg in messages
    ]

    # Calculate scores using pure functions
    scores = calculate_scores(processed, config.get("weights", {}))

    return {
        "processed_messages": processed,
        "scores": scores,
        "metadata": generate_metadata(processed)
    }
```

## File Structure Expectations

### gemini-cli Layout
```
packages/
├── cli/           # User interface and commands
├── core/          # Business logic and API integration
└── vscode-ide-companion/  # IDE integration
docs/              # Comprehensive documentation
integration-tests/ # End-to-end testing
```

### Python Projects Layout
```
components/        # Reusable UI/data components
utils/            # Data processing utilities
schemas/          # Data validation schemas
assets/           # Static files and styles
```

## Error Handling Patterns

### CLI Error Management
- **User-Friendly Messages**: Clear error descriptions with actionable guidance
- **Graceful Degradation**: Continue operation when non-critical components fail
- **Logging**: Structured logging for debugging without exposing internals

### API Error Handling
- **Consistent Response Format**: Standardized error responses across services
- **Retry Logic**: Automatic retries for transient failures
- **Circuit Breakers**: Prevent cascade failures in distributed systems

Remember: This codebase emphasizes **functional programming**, **modular architecture**, and **comprehensive testing**. Always prefer **immutable data structures**, **explicit dependencies**, and **clear separation of concerns**.