# Logic Complexity Analysis Design

## Objective
Analyze control flow and logic complexity using Python AST (Abstract Syntax Tree).

## Why AST?

Factor Graph strategies are Python code executed via `exec()`. To measure logic complexity, we need to parse:
- Control flow statements (if/else)
- Lambda functions
- Nested expressions
- Custom function definitions

**AST provides**:
- Accurate code structure parsing
- Type-safe node traversal
- Expression depth analysis

## Complexity Metrics

### 1. Conditional Branching Complexity (40% weight)
**Measures**: Number and depth of if/else statements

**Examples**:
```python
# Low complexity (linear, no branching)
cond = ma20 > ma60
```

```python
# Medium complexity (one if/else)
if ma20 > ma60:
    cond = True
else:
    cond = False
```

```python
# High complexity (nested if/else)
if ma20 > ma60:
    if volume > avg_volume:
        cond = True
    else:
        cond = False
else:
    cond = False
```

**Scoring**:
- 0 branches: 0.0
- 1 branch: 0.3
- 2-3 branches: 0.6
- 4+ branches: 1.0

**AST Detection**:
```python
class BranchCounter(ast.NodeVisitor):
    def visit_If(self, node):
        self.branch_count += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.current_depth += 1
        self.generic_visit(node)
        self.current_depth -= 1
```

### 2. Nested Condition Depth (30% weight)
**Measures**: Maximum nesting level of logical operations

**Examples**:
```python
# Depth 1
cond = a & b

# Depth 2
cond = (a & b) | (c & d)

# Depth 3
cond = ((a & b) | (c & d)) & ((e | f) & g)
```

**Scoring**:
- Depth 1: 0.0
- Depth 2: 0.4
- Depth 3: 0.7
- Depth 4+: 1.0

**AST Detection**:
```python
class NestingDepthVisitor(ast.NodeVisitor):
    def visit_BoolOp(self, node):  # AND/OR
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1
```

### 3. Custom Function Usage (15% weight)
**Measures**: Whether strategy defines helper functions

**Examples**:
```python
# No custom functions (template-like)
close = data.get('price:收盤價')
ma20 = close.average(20)

# With custom function (novel)
def momentum_score(series):
    return series.diff() / series.shift(1)

close = data.get('price:收盤價')
score = momentum_score(close)
```

**Scoring**:
- No functions: 0.0
- 1 function: 0.5
- 2+ functions: 1.0

**AST Detection**:
```python
class FunctionDefVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        self.function_count += 1
```

### 4. State Management Complexity (15% weight)
**Measures**: Number of intermediate variables and calculations

**Examples**:
```python
# Low state (1 intermediate)
close = data.get('price:收盤價')
ma20 = close.average(20)

# High state (5+ intermediates)
close = data.get('price:收盤價')
ma20 = close.average(20)
ma60 = close.average(60)
momentum = close.diff()
volume_ma = volume.average(10)
score = (momentum / ma20) * (volume / volume_ma)
```

**Scoring**:
- 0-2 variables: 0.0
- 3-5 variables: 0.5
- 6+ variables: 1.0

**AST Detection**:
```python
class VariableCounter(ast.NodeVisitor):
    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.add(target.id)
```

## Template Baseline

Factor Graph templates typically have:
- **0-1 branches**: Simple linear logic or single if/else
- **Depth 1-2**: Simple AND/OR combinations
- **0 custom functions**: Use built-in methods only
- **2-3 variables**: Minimal state

**Expected complexity**: 0.0-0.3

## Algorithm

```python
def calculate_logic_complexity(code: str) -> float:
    tree = ast.parse(code)

    # 1. Count conditional branches (40% weight)
    branches = count_branches(tree)
    branch_score = min(branches / 4.0, 1.0)

    # 2. Measure nesting depth (30% weight)
    depth = measure_nesting_depth(tree)
    depth_score = min((depth - 1) / 3.0, 1.0)  # Depth 1 = 0.0

    # 3. Count custom functions (15% weight)
    functions = count_custom_functions(tree)
    function_score = min(functions / 2.0, 1.0)

    # 4. Count state variables (15% weight)
    variables = count_variables(tree)
    state_score = min((variables - 2) / 4.0, 1.0) if variables > 2 else 0.0

    # Weighted combination
    complexity = (
        0.40 * branch_score +
        0.30 * depth_score +
        0.15 * function_score +
        0.15 * state_score
    )

    return clip(complexity, 0.0, 1.0)
```

## Edge Cases

1. **Syntax Errors**: Return 0.0 with error flag
2. **Empty Code**: Return 0.0
3. **Imports**: Ignore import statements
4. **Comments**: Automatically stripped by AST
5. **Lambda Functions**: Count as inline logic, not custom functions

## Safety Considerations

**AST Parsing is Safe**:
- Does NOT execute code
- Only analyzes structure
- No security risks

**Performance**:
- Target: >10 strategies/second
- Expected: 1,000+ strategies/second (AST is fast)
