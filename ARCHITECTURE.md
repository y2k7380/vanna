# Vanna Architecture Guide
# Vanna 아키텍처 가이드

This document provides an overview of the Vanna framework architecture for newcomers.
이 문서는 새로 온 사람들을 위한 Vanna 프레임워크 아키텍처 개요를 제공합니다.

## What is Vanna?
## Vanna는 무엇인가요?

Vanna is a **Web-First, User-Aware Agent Framework** for data analytics. It transforms natural language queries into SQL queries and data insights while maintaining enterprise-grade security with user awareness as a first-class concern.

Vanna는 데이터 분석을 위한 **웹 우선, 사용자 인식 에이전트 프레임워크**입니다. 자연어 쿼리를 SQL 쿼리와 데이터 인사이트로 변환하며, 사용자 인식을 최우선 관심사로 하여 엔터프라이즈급 보안을 유지합니다.

**Key Features:**
**주요 기능:**
- Natural language to SQL conversion
  자연어를 SQL로 변환
- Multi-LLM provider support (OpenAI, Anthropic, Google, etc.)
  다중 LLM 프로바이더 지원 (OpenAI, Anthropic, Google 등)
- User-aware access control with group-based permissions
  그룹 기반 권한의 사용자 인식 접근 제어
- Pluggable tool system for extending functionality
  기능 확장을 위한 플러그형 도구 시스템
- Rich UI components for data visualization
  데이터 시각화를 위한 풍부한 UI 컴포넌트
- Audit logging for compliance
  컴플라이언스를 위한 감사 로깅

---

## High-Level Architecture
## 상위 수준 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                        (Web / CLI / API)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Server Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   FastAPI    │  │    Flask     │  │     CLI      │         │
│  │   Server     │  │   Server     │  │   Interface  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Core Agent                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. User Resolution  →  2. Workflow Handler             │   │
│  │  3. LLM Call         →  4. Tool Execution               │   │
│  │  5. Response Stream  →  6. Conversation Storage         │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │   LLM    │  │   Tool   │  │ Storage  │
        │ Service  │  │ Registry │  │  Layer   │
        └──────────┘  └──────────┘  └──────────┘
                │            │            │
                │            │            │
        ┌───────┴───┐  ┌─────┴─────┐  ┌─┴────────┐
        │ OpenAI    │  │  run_sql  │  │ Postgres │
        │ Anthropic │  │visualize  │  │  Memory  │
        │  Google   │  │file_system│  │  ChromaDB│
        └───────────┘  └───────────┘  └──────────┘
```

---

## Core Components
## 핵심 컴포넌트

### 1. Agent (에이전트)
**Location:** `src/vanna/core/agent/agent.py`
**위치:** `src/vanna/core/agent/agent.py`

The Agent is the orchestrator of the entire system. It:
에이전트는 전체 시스템의 오케스트레이터입니다. 다음을 수행합니다:

- **Resolves users** from request context
  요청 컨텍스트에서 **사용자 해결**
- **Manages conversation** history
  대화 기록 **관리**
- **Calls the LLM** with system prompts and tools
  시스템 프롬프트와 도구로 **LLM 호출**
- **Executes tools** requested by the LLM
  LLM이 요청한 **도구 실행**
- **Streams responses** back to the UI
  UI로 **응답 스트리밍**
- **Applies lifecycle hooks** for extensibility
  확장성을 위한 **라이프사이클 훅 적용**

**7 Extensibility Points:**
**7가지 확장성 포인트:**
1. Lifecycle Hooks - Hook into message/tool execution
   라이프사이클 훅 - 메시지/도구 실행에 훅
2. LLM Middlewares - Transform requests/responses
   LLM 미들웨어 - 요청/응답 변환
3. Error Recovery Strategy - Handle errors with retry logic
   에러 복구 전략 - 재시도 로직으로 에러 처리
4. Context Enrichers - Add data to tool execution context
   컨텍스트 인리처 - 도구 실행 컨텍스트에 데이터 추가
5. LLM Context Enhancer - Enhance system prompts (e.g., RAG)
   LLM 컨텍스트 인핸서 - 시스템 프롬프트 향상 (예: RAG)
6. Conversation Filters - Filter conversation history
   대화 필터 - 대화 기록 필터링
7. Observability Provider - Collect telemetry
   관찰성 프로바이더 - 텔레메트리 수집

### 2. Tool System (도구 시스템)
**Location:** `src/vanna/core/tool/` and `src/vanna/tools/`
**위치:** `src/vanna/core/tool/` 및 `src/vanna/tools/`

Tools are how the LLM interacts with external systems.
도구는 LLM이 외부 시스템과 상호작용하는 방법입니다.

**Tool Base Class** (`tool/base.py`):
**도구 베이스 클래스** (`tool/base.py`):
```python
class Tool(ABC, Generic[T]):
    @property
    def name(self) -> str:
        """Unique name for the tool"""

    @property
    def description(self) -> str:
        """Description shown to the LLM"""

    @property
    def access_groups(self) -> List[str]:
        """Groups that can access this tool"""

    def get_args_schema(self) -> Type[T]:
        """Pydantic model for argument validation"""

    async def execute(self, context: ToolContext, args: T) -> ToolResult:
        """Execute the tool's work"""
```

**Built-in Tools:**
**내장 도구:**
- `run_sql` - Execute SQL queries with user-aware permissions
  사용자 인식 권한으로 SQL 쿼리 실행
- `visualize_data` - Create charts with Plotly
  Plotly로 차트 생성
- `file_system` - Read/write/search files
  파일 읽기/쓰기/검색
- `python` - Execute Python code
  Python 코드 실행
- `agent_memory` - Long-term memory for tool patterns
  도구 패턴을 위한 장기 메모리

### 3. Tool Registry (도구 레지스트리)
**Location:** `src/vanna/core/registry.py`
**위치:** `src/vanna/core/registry.py`

The ToolRegistry manages all tools and handles:
ToolRegistry는 모든 도구를 관리하고 다음을 처리합니다:

**Execution Pipeline:**
**실행 파이프라인:**
1. **Tool Lookup** - Find tool by name
   **도구 조회** - 이름으로 도구 찾기
2. **Permission Check** - Validate user access via groups
   **권한 확인** - 그룹을 통한 사용자 접근 검증
3. **Argument Validation** - Validate with Pydantic
   **인자 검증** - Pydantic으로 검증
4. **Argument Transformation** - Apply user-specific rules (e.g., Row-Level Security)
   **인자 변환** - 사용자별 규칙 적용 (예: 행 레벨 보안)
5. **Audit Logging** - Record invocation
   **감사 로깅** - 호출 기록
6. **Execution** - Run the tool
   **실행** - 도구 실행
7. **Result Logging** - Record result
   **결과 로깅** - 결과 기록

**Permission Model:**
**권한 모델:**
```python
# Tool requires "admin" OR "analyst" groups
# 도구가 "admin" 또는 "analyst" 그룹 필요
tool.access_groups = ["admin", "analyst"]

# User in any matching group → access granted
# 일치하는 그룹의 사용자 → 접근 허용
user.group_memberships = ["analyst", "viewer"]  # ✓ Access granted
```

### 4. LLM Service (LLM 서비스)
**Location:** `src/vanna/core/llm/`
**위치:** `src/vanna/core/llm/`

Abstraction layer for multiple LLM providers.
여러 LLM 프로바이더를 위한 추상화 계층.

**Interface:**
**인터페이스:**
```python
class LlmService(ABC):
    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a request to the LLM"""

    async def stream_request(self, request: LlmRequest) -> AsyncGenerator[LlmResponse, None]:
        """Stream a request to the LLM"""
```

**Supported Providers** (31 integrations):
**지원되는 프로바이더** (31개 통합):
- **LLMs:** OpenAI, Anthropic, Google Gemini, Azure OpenAI, Ollama, Mistral, etc.
  **LLM:** OpenAI, Anthropic, Google Gemini, Azure OpenAI, Ollama, Mistral 등
- **Databases:** PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, DuckDB, etc.
  **데이터베이스:** PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, DuckDB 등
- **Vector Search:** ChromaDB, Pinecone, Qdrant, Weaviate, Milvus, FAISS, etc.
  **벡터 검색:** ChromaDB, Pinecone, Qdrant, Weaviate, Milvus, FAISS 등

### 5. User System (사용자 시스템)
**Location:** `src/vanna/core/user/`
**위치:** `src/vanna/core/user/`

User-awareness flows through the entire system.
사용자 인식은 전체 시스템을 통해 흐릅니다.

**Key Models:**
**주요 모델:**
```python
class User:
    id: str
    name: str
    group_memberships: List[str]  # For access control
    attributes: Dict[str, Any]    # For RLS and customization

class RequestContext:
    metadata: Dict[str, Any]      # HTTP headers, session data, etc.
```

**User Resolver:**
**사용자 리졸버:**
Converts request context into a User object. Override this to integrate with your auth system.
요청 컨텍스트를 User 객체로 변환합니다. 인증 시스템과 통합하려면 이것을 오버라이드하세요.

### 6. Conversation Storage (대화 저장소)
**Location:** `src/vanna/core/storage/`
**위치:** `src/vanna/core/storage/`

Stores conversation history for context.
컨텍스트를 위한 대화 기록 저장.

**Interface:**
**인터페이스:**
```python
class ConversationStore(ABC):
    async def get_conversation(self, conversation_id: str, user: User) -> Optional[Conversation]:
        """Retrieve a conversation"""

    async def update_conversation(self, conversation: Conversation) -> None:
        """Save/update a conversation"""
```

**Implementations:**
**구현:**
- `MemoryConversationStore` - In-memory (for development)
  메모리 내 (개발용)
- Database-backed stores (PostgreSQL, etc.)
  데이터베이스 기반 저장소 (PostgreSQL 등)

### 7. UI Component System (UI 컴포넌트 시스템)
**Location:** `src/vanna/components/`
**위치:** `src/vanna/components/`

Rich, structured components for streaming responses.
스트리밍 응답을 위한 풍부하고 구조화된 컴포넌트.

**Component Types:**
**컴포넌트 타입:**
- **Data:** DataFrameComponent, ChartComponent
  **데이터:** DataFrameComponent, ChartComponent
- **Feedback:** NotificationComponent, StatusCardComponent, ProgressComponent
  **피드백:** NotificationComponent, StatusCardComponent, ProgressComponent
- **Interactive:** ButtonComponent, TaskListComponent
  **인터랙티브:** ButtonComponent, TaskListComponent
- **Containers:** CardComponent
  **컨테이너:** CardComponent
- **Simple:** Text, Link, Image (fallback)
  **단순:** Text, Link, Image (폴백)

Each component has:
각 컴포넌트는 다음을 가집니다:
- **Rich version** - Full-featured UI
  **리치 버전** - 완전한 기능의 UI
- **Simple version** - Text fallback for basic clients
  **단순 버전** - 기본 클라이언트를 위한 텍스트 폴백

---

## Request Flow
## 요청 흐름

Here's how a typical request flows through the system:
일반적인 요청이 시스템을 통해 흐르는 방법은 다음과 같습니다:

```
1. User sends message via Web UI
   사용자가 웹 UI를 통해 메시지 전송
   ↓
2. FastAPI server receives HTTP request
   FastAPI 서버가 HTTP 요청 수신
   ↓
3. Server creates RequestContext from HTTP headers
   서버가 HTTP 헤더에서 RequestContext 생성
   ↓
4. Agent.send_message() is called
   Agent.send_message() 호출됨
   ↓
5. User Resolver converts RequestContext → User
   사용자 리졸버가 RequestContext → User로 변환
   ↓
6. Agent loads conversation history
   에이전트가 대화 기록 로드
   ↓
7. Agent builds LLM request with:
   에이전트가 다음으로 LLM 요청 구성:
   - System prompt
     시스템 프롬프트
   - Conversation history
     대화 기록
   - Available tools (filtered by user's groups)
     사용 가능한 도구 (사용자 그룹으로 필터링됨)
   ↓
8. LLM Service sends request to LLM provider
   LLM 서비스가 LLM 프로바이더에 요청 전송
   ↓
9a. LLM returns tool calls
    LLM이 도구 호출 반환
    ↓
    Tool Registry executes tools:
    도구 레지스트리가 도구 실행:
    - Check permissions
      권한 확인
    - Validate arguments
      인자 검증
    - Transform arguments (RLS)
      인자 변환 (RLS)
    - Execute tool
      도구 실행
    - Return ToolResult with UI component
      UI 컴포넌트와 함께 ToolResult 반환
    ↓
    Agent sends tool results back to LLM
    에이전트가 도구 결과를 LLM에 다시 전송
    ↓
    Loop until LLM returns text response
    LLM이 텍스트 응답을 반환할 때까지 반복

9b. LLM returns text response
    LLM이 텍스트 응답 반환
    ↓
10. Agent streams UI components to server
    에이전트가 UI 컴포넌트를 서버로 스트리밍
    ↓
11. Server streams to Web UI via SSE/WebSocket
    서버가 SSE/WebSocket을 통해 웹 UI로 스트리밍
    ↓
12. Conversation saved to storage
    대화가 저장소에 저장됨
```

---

## Security Model
## 보안 모델

Vanna implements defense-in-depth security:
Vanna는 심층 방어 보안을 구현합니다:

### Group-Based Access Control
### 그룹 기반 접근 제어

```python
# Define user groups
# 사용자 그룹 정의
user.group_memberships = ["analyst", "sales"]

# Restrict tool access
# 도구 접근 제한
registry.register_local_tool(
    tool=RunSqlTool(),
    access_groups=["analyst", "admin"]  # Only analyst and admin can use
)
```

### Row-Level Security (RLS)
### 행 레벨 보안 (RLS)

```python
class SecureToolRegistry(ToolRegistry):
    async def transform_args(self, tool, args, user, context):
        if tool.name == "run_sql":
            # Add WHERE clause based on user's region
            # 사용자의 지역을 기반으로 WHERE 절 추가
            region = user.attributes.get("region")
            args.sql = f"{args.sql} WHERE region = '{region}'"
        return args
```

### Audit Logging
### 감사 로깅

All tool access and invocations can be logged:
모든 도구 접근 및 호출을 로깅할 수 있습니다:
- Who accessed what tool?
  누가 어떤 도구에 접근했나요?
- What arguments were provided?
  어떤 인자가 제공되었나요?
- What was the result?
  결과는 무엇이었나요?
- Which UI features were available?
  어떤 UI 기능이 사용 가능했나요?

---

## Extensibility Patterns
## 확장성 패턴

### 1. Creating a Custom Tool
### 1. 사용자 정의 도구 생성

```python
from pydantic import BaseModel
from vanna.core.tool import Tool, ToolContext, ToolResult

class CalculatorArgs(BaseModel):
    operation: str
    a: float
    b: float

class CalculatorTool(Tool[CalculatorArgs]):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Performs basic math operations (add, subtract, multiply, divide)"

    @property
    def access_groups(self) -> List[str]:
        return []  # Accessible to all users

    def get_args_schema(self) -> Type[CalculatorArgs]:
        return CalculatorArgs

    async def execute(self, context: ToolContext, args: CalculatorArgs) -> ToolResult:
        if args.operation == "add":
            result = args.a + args.b
        elif args.operation == "subtract":
            result = args.a - args.b
        # ... handle other operations

        return ToolResult(
            success=True,
            result_for_llm=f"The result is {result}"
        )

# Register the tool
# 도구 등록
registry.register_local_tool(CalculatorTool(), access_groups=[])
```

### 2. Adding a Lifecycle Hook
### 2. 라이프사이클 훅 추가

```python
from vanna.core.lifecycle import LifecycleHook

class QuotaCheckHook(LifecycleHook):
    async def before_message(self, user: User, message: str) -> Optional[str]:
        # Check if user has exceeded quota
        # 사용자가 할당량을 초과했는지 확인
        if user_exceeded_quota(user):
            raise Exception("Quota exceeded")
        return None  # No modification to message

    async def after_tool(self, result: ToolResult) -> Optional[ToolResult]:
        # Log tool usage for billing
        # 청구를 위한 도구 사용 로깅
        log_tool_usage(result)
        return None  # No modification to result

# Add to agent
# 에이전트에 추가
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    lifecycle_hooks=[QuotaCheckHook()]
)
```

### 3. Custom User Resolver
### 3. 사용자 정의 사용자 리졸버

```python
from vanna.core.user import UserResolver, User, RequestContext

class JWTUserResolver(UserResolver):
    async def resolve_user(self, context: RequestContext) -> User:
        # Extract JWT from headers
        # 헤더에서 JWT 추출
        token = context.metadata.get("authorization")
        claims = decode_jwt(token)

        return User(
            id=claims["sub"],
            name=claims["name"],
            group_memberships=claims["groups"],
            attributes={"region": claims["region"]}
        )
```

---

## Directory Structure
## 디렉토리 구조

```
vanna/
├── src/vanna/
│   ├── core/              # Core framework
│   │   ├── agent/         # Agent orchestration
│   │   ├── tool/          # Tool abstractions
│   │   ├── llm/           # LLM service interface
│   │   ├── user/          # User models and resolvers
│   │   ├── storage/       # Conversation storage
│   │   ├── registry.py    # Tool registry
│   │   ├── workflow/      # Workflow handlers
│   │   ├── lifecycle/     # Lifecycle hooks
│   │   ├── middleware/    # LLM middlewares
│   │   ├── enhancer/      # LLM context enhancers
│   │   ├── enricher/      # Tool context enrichers
│   │   ├── filter/        # Conversation filters
│   │   ├── recovery/      # Error recovery
│   │   ├── audit/         # Audit logging
│   │   └── observability/ # Telemetry
│   ├── tools/             # Built-in tools
│   │   ├── run_sql.py
│   │   ├── visualize_data.py
│   │   ├── file_system.py
│   │   ├── python.py
│   │   └── agent_memory.py
│   ├── integrations/      # LLM and DB integrations (31+)
│   │   ├── anthropic/
│   │   ├── openai/
│   │   ├── google/
│   │   ├── postgres/
│   │   ├── chromadb/
│   │   └── ...
│   ├── servers/           # Web servers
│   │   ├── fastapi/       # FastAPI server
│   │   ├── flask/         # Flask server
│   │   └── cli/           # CLI interface
│   ├── components/        # UI components
│   │   ├── rich/          # Rich components
│   │   └── simple/        # Simple fallback components
│   ├── capabilities/      # Reusable capabilities
│   │   ├── agent_memory/
│   │   ├── sql_runner/
│   │   └── file_system/
│   ├── examples/          # Example code
│   └── legacy/            # v1.x compatibility
└── tests/                 # Test suite
```

---

## Getting Started
## 시작하기

### Basic Example
### 기본 예제

```python
from vanna import Agent
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.postgres import PostgresConnection
from vanna.core.registry import ToolRegistry
from vanna.tools import RunSqlTool
from vanna.core.user import StaticUserResolver, User

# 1. Create LLM service
# 1. LLM 서비스 생성
llm = AnthropicLlmService(api_key="your-api-key")

# 2. Create database connection
# 2. 데이터베이스 연결 생성
db = PostgresConnection(connection_string="postgresql://...")

# 3. Register tools
# 3. 도구 등록
registry = ToolRegistry()
registry.register_local_tool(
    RunSqlTool(db_connection=db),
    access_groups=[]  # Accessible to all
)

# 4. Create user resolver
# 4. 사용자 리졸버 생성
user_resolver = StaticUserResolver(
    User(id="user1", name="Alice", group_memberships=["analyst"])
)

# 5. Create agent
# 5. 에이전트 생성
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver
)

# 6. Send a message
# 6. 메시지 전송
async for component in agent.send_message(
    request_context=RequestContext(metadata={}),
    message="Show me total sales by region"
):
    print(component)
```

---

## Key Concepts Summary
## 주요 개념 요약

| Concept | Purpose | Korean |
|---------|---------|--------|
| **Agent** | Orchestrates LLM, tools, and conversation | LLM, 도구, 대화를 조율 |
| **Tool** | Extends LLM capabilities with actions | 작업으로 LLM 기능 확장 |
| **ToolRegistry** | Manages tools and enforces permissions | 도구 관리 및 권한 강제 |
| **User** | Represents authenticated user with groups | 그룹이 있는 인증된 사용자 표현 |
| **RequestContext** | HTTP/session metadata for user resolution | 사용자 해결을 위한 HTTP/세션 메타데이터 |
| **ToolContext** | Execution context passed to tools | 도구에 전달되는 실행 컨텍스트 |
| **ToolResult** | Result from tool execution | 도구 실행 결과 |
| **UiComponent** | Structured UI output (rich + simple) | 구조화된 UI 출력 (리치 + 단순) |
| **Lifecycle Hook** | Extension point for message/tool lifecycle | 메시지/도구 라이프사이클을 위한 확장 포인트 |
| **LLM Middleware** | Transform LLM requests/responses | LLM 요청/응답 변환 |

---

## Next Steps
## 다음 단계

1. **Read the code** - Start with these files:
   **코드 읽기** - 다음 파일부터 시작하세요:
   - `src/vanna/core/agent/agent.py` - Agent orchestration
     에이전트 조율
   - `src/vanna/core/tool/base.py` - Tool interface
     도구 인터페이스
   - `src/vanna/core/registry.py` - Tool registry
     도구 레지스트리
   - `src/vanna/tools/run_sql.py` - Example tool
     예제 도구

2. **Run examples** - Check `src/vanna/examples/`
   **예제 실행** - `src/vanna/examples/` 확인

3. **Create a custom tool** - Extend functionality
   **사용자 정의 도구 생성** - 기능 확장

4. **Integrate your auth** - Implement custom UserResolver
   **인증 통합** - 사용자 정의 UserResolver 구현

5. **Add observability** - Implement ObservabilityProvider
   **관찰성 추가** - ObservabilityProvider 구현

---

## Resources
## 리소스

- **GitHub:** https://github.com/vanna-ai/vanna
- **Documentation:** Check README.md and inline code comments
  **문서:** README.md 및 인라인 코드 주석 확인
- **Examples:** `src/vanna/examples/`
  **예제:** `src/vanna/examples/`

---

**Happy coding! 즐거운 코딩 되세요!** 🚀
