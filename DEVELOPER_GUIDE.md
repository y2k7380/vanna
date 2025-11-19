# Vanna Developer Guide
# Vanna 개발자 가이드

Complete guide for understanding, using, and customizing Vanna.
Vanna를 이해하고, 사용하고, 커스터마이징하기 위한 완전한 가이드.

---

## Table of Contents
## 목차

1. [Code Structure Analysis](#code-structure-analysis)
2. [Core Components Deep Dive](#core-components-deep-dive)
3. [Usage Patterns](#usage-patterns)
4. [Customization Guide](#customization-guide)
5. [Advanced Topics](#advanced-topics)
6. [Best Practices](#best-practices)
7. [Debugging & Troubleshooting](#debugging--troubleshooting)

---

## Code Structure Analysis
## 코드 구조 분석

### Directory Organization
### 디렉토리 구성

```
vanna/
├── src/vanna/
│   ├── core/              # 핵심 프레임워크 / Core framework
│   ├── tools/             # 내장 도구 / Built-in tools
│   ├── integrations/      # 외부 통합 / External integrations
│   ├── servers/           # 웹 서버 / Web servers
│   ├── components/        # UI 컴포넌트 / UI components
│   ├── capabilities/      # 재사용 가능한 기능 / Reusable capabilities
│   └── examples/          # 예제 코드 / Example code
└── tests/                 # 테스트 / Tests
```

### Core Framework (`src/vanna/core/`)
### 핵심 프레임워크 (`src/vanna/core/`)

#### 1. Agent System (에이전트 시스템)
**Location:** `core/agent/`

```
agent/
├── agent.py           # Main Agent class - orchestrates everything
│                      # 메인 Agent 클래스 - 모든 것을 조율
├── config.py          # AgentConfig - behavior configuration
│                      # AgentConfig - 동작 설정
└── __init__.py
```

**Key Classes:**
**주요 클래스:**

```python
class Agent:
    """
    Central orchestrator that:
    중앙 오케스트레이터:
    - Receives user messages (사용자 메시지 수신)
    - Resolves user context (사용자 컨텍스트 해결)
    - Calls LLM with tools (도구와 함께 LLM 호출)
    - Executes tool calls (도구 호출 실행)
    - Streams UI components (UI 컴포넌트 스트리밍)
    """

    def __init__(
        self,
        llm_service: LlmService,           # LLM provider (OpenAI, Anthropic, etc.)
        tool_registry: ToolRegistry,       # Available tools
        user_resolver: UserResolver,       # User authentication
        agent_memory: AgentMemory,         # Long-term memory
        # ... 7 extensibility points
    ):
        pass

    async def send_message(
        self,
        request_context: RequestContext,   # HTTP request metadata
        message: str,                       # User's question
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[UiComponent, None]:
        """
        Main entry point for processing user messages
        사용자 메시지 처리를 위한 주요 진입점

        Flow:
        흐름:
        1. Resolve user from request context
           요청 컨텍스트에서 사용자 해결
        2. Load conversation history
           대화 기록 로드
        3. Build LLM request with available tools
           사용 가능한 도구로 LLM 요청 구성
        4. Stream LLM response
           LLM 응답 스트리밍
        5. Execute any tool calls
           도구 호출 실행
        6. Loop until final response
           최종 응답까지 반복
        """
        pass
```

**Configuration:**
**설정:**

```python
class AgentConfig:
    """
    Configure agent behavior
    에이전트 동작 설정
    """
    max_tool_iterations: int = 10              # Max tool calls per message
    temperature: float = 0.0                   # LLM temperature
    max_tokens: int = 4096                     # Max response tokens
    stream_responses: bool = True              # Enable streaming
    auto_save_conversations: bool = True       # Auto-save to storage
    include_thinking_indicators: bool = False  # Show "thinking..." indicators

    # UI Features - control what users can see
    # UI 기능 - 사용자가 볼 수 있는 것 제어
    ui_features: UiFeatureConfig = UiFeatureConfig(
        feature_group_access={
            "UI_FEATURE_SHOW_TOOL_NAMES": [],      # Show tool names to all
            "UI_FEATURE_SHOW_TOOL_ARGUMENTS": ["admin"],  # Only admins see args
            "UI_FEATURE_SHOW_TOOL_ERROR": ["admin"],      # Only admins see errors
        }
    )

    # Audit logging configuration
    # 감사 로깅 설정
    audit_config: AuditConfig = AuditConfig(
        enabled=True,
        log_tool_invocations=True,
        log_tool_results=True,
        log_ui_feature_checks=True,
        sanitize_tool_parameters=False  # Redact sensitive data
    )
```

#### 2. Tool System (도구 시스템)
**Location:** `core/tool/`

```
tool/
├── base.py            # Abstract Tool class
│                      # 추상 Tool 클래스
├── models.py          # ToolContext, ToolResult, ToolSchema, ToolCall
│                      # 도구 관련 데이터 모델
└── __init__.py
```

**Creating a Custom Tool:**
**사용자 정의 도구 생성:**

```python
from pydantic import BaseModel, Field
from vanna.core.tool import Tool, ToolContext, ToolResult
from vanna.components import UiComponent, DataFrameComponent
from typing import Type

# Step 1: Define argument schema with Pydantic
# 1단계: Pydantic으로 인자 스키마 정의
class WeatherArgs(BaseModel):
    """
    Arguments for weather tool
    날씨 도구 인자
    """
    location: str = Field(
        description="City name or zip code (도시 이름 또는 우편번호)"
    )
    units: str = Field(
        default="celsius",
        description="Temperature units: celsius or fahrenheit (온도 단위)"
    )

# Step 2: Implement the Tool class
# 2단계: Tool 클래스 구현
class WeatherTool(Tool[WeatherArgs]):
    """
    Get current weather for a location
    위치의 현재 날씨 가져오기
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def name(self) -> str:
        """
        Unique identifier for this tool
        이 도구의 고유 식별자
        """
        return "get_weather"

    @property
    def description(self) -> str:
        """
        Description shown to the LLM
        LLM에게 표시되는 설명

        Be specific about:
        다음을 구체적으로 작성:
        - What the tool does
        - When to use it
        - What data it returns
        """
        return """Get current weather information for a location.

        Use this when the user asks about:
        - Current weather conditions
        - Temperature
        - Weather forecast (current only, not multi-day)

        Returns temperature, conditions, humidity, and wind speed.

        위치의 현재 날씨 정보를 가져옵니다.
        사용자가 다음에 대해 물을 때 사용:
        - 현재 날씨 상태
        - 온도
        - 날씨 예보 (현재만, 여러 날 아님)

        온도, 상태, 습도, 풍속을 반환합니다.
        """

    @property
    def access_groups(self) -> List[str]:
        """
        Which user groups can access this tool
        어떤 사용자 그룹이 이 도구에 접근할 수 있는지

        Empty list = accessible to all users
        빈 리스트 = 모든 사용자가 접근 가능
        """
        return []  # Available to everyone

    def get_args_schema(self) -> Type[WeatherArgs]:
        """
        Return the Pydantic model for validation
        검증을 위한 Pydantic 모델 반환
        """
        return WeatherArgs

    async def execute(
        self,
        context: ToolContext,
        args: WeatherArgs
    ) -> ToolResult:
        """
        Execute the tool
        도구 실행

        Args:
            context: Contains user, conversation_id, request_id, agent_memory
                    사용자, conversation_id, request_id, agent_memory 포함
            args: Validated arguments (already checked by Pydantic)
                 검증된 인자 (Pydantic으로 이미 확인됨)

        Returns:
            ToolResult with:
            - success: True/False
            - result_for_llm: Text description for the LLM to read
            - ui_component: Optional rich UI component
            - error: Error message if success=False
        """
        try:
            # Your implementation here
            # 여기에 구현 작성
            weather_data = await self._fetch_weather(args.location, args.units)

            # Create result for LLM
            # LLM을 위한 결과 생성
            result_text = f"""Weather in {args.location}:
            Temperature: {weather_data['temp']}°{args.units[0].upper()}
            Conditions: {weather_data['conditions']}
            Humidity: {weather_data['humidity']}%
            Wind: {weather_data['wind_speed']} km/h
            """

            # Optional: Create rich UI component for web interface
            # 선택사항: 웹 인터페이스를 위한 리치 UI 컴포넌트 생성
            ui_component = UiComponent(
                rich_component=DataFrameComponent(
                    data=pd.DataFrame([weather_data]),
                    title=f"Weather in {args.location}"
                ),
                simple_component=SimpleTextComponent(text=result_text)
            )

            return ToolResult(
                success=True,
                result_for_llm=result_text,
                ui_component=ui_component
            )

        except Exception as e:
            # Handle errors gracefully
            # 에러를 우아하게 처리
            return ToolResult(
                success=False,
                result_for_llm=f"Failed to get weather: {str(e)}",
                error=str(e)
            )

    async def _fetch_weather(self, location: str, units: str) -> dict:
        """Internal method to fetch weather data"""
        # Call weather API
        # 날씨 API 호출
        pass

# Step 3: Register the tool
# 3단계: 도구 등록
registry = ToolRegistry()
registry.register_local_tool(
    tool=WeatherTool(api_key="your-api-key"),
    access_groups=[]  # Accessible to all
)
```

#### 3. Tool Registry (도구 레지스트리)
**Location:** `core/registry.py`

**Execution Pipeline:**
**실행 파이프라인:**

```python
class ToolRegistry:
    """
    Manages all tools and their execution
    모든 도구와 실행 관리
    """

    async def execute(
        self,
        tool_call: ToolCall,      # LLM's request to call a tool
        context: ToolContext       # Execution context
    ) -> ToolResult:
        """
        Execute a tool with full validation pipeline
        완전한 검증 파이프라인으로 도구 실행

        Pipeline (7 steps):
        파이프라인 (7단계):

        1. Tool Lookup
           도구 조회
           ├─ Check if tool exists
           └─ Return error if not found

        2. Permission Check
           권한 확인
           ├─ Validate user's group memberships
           ├─ Check against tool.access_groups
           ├─ Log access denial if rejected
           └─ Return error if insufficient permissions

        3. Argument Validation
           인자 검증
           ├─ Get Pydantic schema from tool
           ├─ Validate LLM's arguments
           └─ Return error if validation fails

        4. Argument Transformation
           인자 변환
           ├─ Call transform_args() (can override)
           ├─ Apply user-specific rules (e.g., RLS)
           └─ Return error if transformation rejects

        5. Audit Logging (Pre-execution)
           감사 로깅 (실행 전)
           ├─ Log successful access check
           └─ Log tool invocation details

        6. Tool Execution
           도구 실행
           ├─ Measure execution time
           ├─ Call tool.execute()
           └─ Handle exceptions

        7. Audit Logging (Post-execution)
           감사 로깅 (실행 후)
           └─ Log tool result
        """
        pass

    async def transform_args(
        self,
        tool: Tool[T],
        args: T,
        user: User,
        context: ToolContext
    ) -> Union[T, ToolRejection]:
        """
        Override this to implement custom argument transformation
        사용자 정의 인자 변환을 구현하려면 이것을 오버라이드

        Use cases:
        사용 사례:
        - Row-Level Security (RLS) for SQL
          SQL을 위한 행 레벨 보안 (RLS)
        - User-specific data filtering
          사용자별 데이터 필터링
        - Argument validation beyond Pydantic
          Pydantic을 넘어선 인자 검증
        - Redacting sensitive fields
          민감한 필드 삭제
        """
        # Default: no transformation
        # 기본값: 변환 없음
        return args
```

**Implementing Row-Level Security (RLS):**
**행 레벨 보안 (RLS) 구현:**

```python
class SecureToolRegistry(ToolRegistry):
    """
    Custom registry with Row-Level Security
    행 레벨 보안이 있는 사용자 정의 레지스트리
    """

    async def transform_args(self, tool, args, user, context):
        """
        Add user-specific filters to SQL queries
        SQL 쿼리에 사용자별 필터 추가
        """

        # Only apply to SQL tools
        # SQL 도구에만 적용
        if tool.name != "run_sql":
            return args

        # Check if user has required attributes
        # 사용자가 필요한 속성을 가지고 있는지 확인
        region = user.attributes.get("region")
        department = user.attributes.get("department")

        if not region:
            return ToolRejection(
                reason="User must have a region assigned to run SQL queries"
            )

        # Parse SQL and add WHERE clause
        # SQL을 파싱하고 WHERE 절 추가
        original_sql = args.sql

        # Simple example - in production use a SQL parser
        # 간단한 예제 - 프로덕션에서는 SQL 파서 사용
        if "WHERE" in original_sql.upper():
            # Add to existing WHERE clause
            # 기존 WHERE 절에 추가
            args.sql = original_sql.replace(
                "WHERE",
                f"WHERE region = '{region}' AND department = '{department}' AND",
                1
            )
        else:
            # Add new WHERE clause
            # 새로운 WHERE 절 추가
            args.sql = f"{original_sql} WHERE region = '{region}' AND department = '{department}'"

        # Log the transformation for audit
        # 감사를 위해 변환 기록
        logger.info(f"Applied RLS for user {user.id}: {original_sql} -> {args.sql}")

        return args

# Usage
# 사용법
registry = SecureToolRegistry()
```

#### 4. User System (사용자 시스템)
**Location:** `core/user/`

```
user/
├── base.py                # User model
│                          # 사용자 모델
├── resolver.py            # UserResolver interface
│                          # UserResolver 인터페이스
├── request_context.py     # RequestContext model
│                          # RequestContext 모델
└── __init__.py
```

**Models:**
**모델:**

```python
class User:
    """
    Represents an authenticated user
    인증된 사용자를 나타냄
    """
    id: str                           # Unique user ID (고유 사용자 ID)
    name: str                         # Display name (표시 이름)
    group_memberships: List[str]      # Groups for access control (접근 제어를 위한 그룹)
    attributes: Dict[str, Any]        # Custom attributes for RLS, etc.
                                      # RLS 등을 위한 사용자 정의 속성

    # Example:
    # 예제:
    user = User(
        id="user123",
        name="Alice Smith",
        group_memberships=["analyst", "sales"],
        attributes={
            "region": "us-west",
            "department": "sales",
            "cost_center": "CC-1234"
        }
    )

class RequestContext:
    """
    Context from HTTP request
    HTTP 요청의 컨텍스트
    """
    metadata: Dict[str, Any]          # HTTP headers, session data, etc.
                                      # HTTP 헤더, 세션 데이터 등

    # Example:
    # 예제:
    context = RequestContext(
        metadata={
            "authorization": "Bearer token...",
            "user_agent": "Mozilla/5.0...",
            "ip_address": "192.168.1.1",
            "session_id": "sess_abc123"
        }
    )
```

**Implementing Custom User Resolver:**
**사용자 정의 User Resolver 구현:**

```python
from vanna.core.user import UserResolver, User, RequestContext
import jwt  # Example: JWT authentication

class JWTUserResolver(UserResolver):
    """
    Resolve user from JWT token in request headers
    요청 헤더의 JWT 토큰에서 사용자 해결
    """

    def __init__(self, jwt_secret: str):
        self.jwt_secret = jwt_secret

    async def resolve_user(self, context: RequestContext) -> User:
        """
        Extract user from JWT token
        JWT 토큰에서 사용자 추출

        Args:
            context: Request context with HTTP headers
                    HTTP 헤더가 있는 요청 컨텍스트

        Returns:
            User object with groups and attributes
            그룹과 속성이 있는 User 객체
        """
        # Get authorization header
        # Authorization 헤더 가져오기
        auth_header = context.metadata.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            raise ValueError("Missing or invalid authorization header")

        # Extract token
        # 토큰 추출
        token = auth_header.replace("Bearer ", "")

        try:
            # Decode JWT
            # JWT 디코딩
            claims = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"]
            )

            # Build User from claims
            # claims에서 User 구성
            return User(
                id=claims["sub"],                    # User ID
                name=claims.get("name", "Unknown"),  # Display name
                group_memberships=claims.get("groups", []),  # Groups
                attributes={
                    "region": claims.get("region"),
                    "department": claims.get("department"),
                    "email": claims.get("email"),
                    # Add any custom attributes from your JWT
                    # JWT의 사용자 정의 속성 추가
                }
            )

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")


class DatabaseUserResolver(UserResolver):
    """
    Resolve user from database using session ID
    세션 ID를 사용하여 데이터베이스에서 사용자 해결
    """

    def __init__(self, db_connection):
        self.db = db_connection

    async def resolve_user(self, context: RequestContext) -> User:
        """
        Look up user in database
        데이터베이스에서 사용자 조회
        """
        session_id = context.metadata.get("session_id")

        if not session_id:
            raise ValueError("No session ID provided")

        # Query database
        # 데이터베이스 쿼리
        user_data = await self.db.execute(
            "SELECT user_id, name, groups, region, department FROM sessions WHERE session_id = ?",
            (session_id,)
        )

        if not user_data:
            raise ValueError("Invalid session")

        return User(
            id=user_data["user_id"],
            name=user_data["name"],
            group_memberships=user_data["groups"].split(","),
            attributes={
                "region": user_data["region"],
                "department": user_data["department"]
            }
        )


# Usage in FastAPI
# FastAPI에서 사용
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()
user_resolver = JWTUserResolver(jwt_secret="your-secret")

@app.post("/chat")
async def chat(
    message: str,
    authorization: str = Header(None)
):
    # Build request context from HTTP request
    # HTTP 요청에서 요청 컨텍스트 구성
    context = RequestContext(
        metadata={
            "authorization": authorization,
            # Add other headers as needed
            # 필요에 따라 다른 헤더 추가
        }
    )

    # Agent will use user_resolver to get User
    # Agent는 user_resolver를 사용하여 User를 가져옴
    async for component in agent.send_message(context, message):
        yield component
```

#### 5. LLM Service (LLM 서비스)
**Location:** `core/llm/`

```
llm/
├── base.py            # LlmService interface
│                      # LlmService 인터페이스
├── models.py          # LlmRequest, LlmResponse, LlmMessage
│                      # LLM 관련 데이터 모델
└── __init__.py
```

**Interface:**
**인터페이스:**

```python
class LlmService(ABC):
    """
    Abstract interface for LLM providers
    LLM 프로바이더를 위한 추상 인터페이스
    """

    @abstractmethod
    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """
        Send a single request to the LLM
        LLM에 단일 요청 전송

        Args:
            request: Contains messages, tools, temperature, etc.
                    메시지, 도구, 온도 등 포함

        Returns:
            response: Contains text content and/or tool calls
                     텍스트 내용 및/또는 도구 호출 포함
        """
        pass

    @abstractmethod
    async def stream_request(
        self,
        request: LlmRequest
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        Stream a request to the LLM
        LLM에 요청 스트리밍

        Yields partial responses as they arrive
        부분 응답이 도착하면 생성
        """
        pass
```

**Implementing Custom LLM Service:**
**사용자 정의 LLM 서비스 구현:**

```python
from vanna.core.llm import LlmService, LlmRequest, LlmResponse
import httpx

class CustomLlmService(LlmService):
    """
    Custom LLM service for your API
    사용자 정의 API를 위한 LLM 서비스
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """
        Send request to your LLM API
        LLM API에 요청 전송
        """
        # Convert Vanna's format to your API's format
        # Vanna 형식을 API 형식으로 변환
        api_request = {
            "model": self.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        # Add tools if provided
        # 제공된 경우 도구 추가
        if request.tools:
            api_request["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
                for tool in request.tools
            ]

        # Call your API
        # API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=api_request
            )
            response.raise_for_status()
            data = response.json()

        # Convert response to Vanna's format
        # 응답을 Vanna 형식으로 변환
        return LlmResponse(
            content=data.get("message", {}).get("content"),
            tool_calls=self._parse_tool_calls(data.get("tool_calls", []))
        )

    async def stream_request(self, request: LlmRequest):
        """
        Stream request to your LLM API
        LLM API에 요청 스트리밍
        """
        # Similar to send_request but with streaming
        # send_request와 유사하지만 스트리밍 사용
        pass
```

---

## Usage Patterns
## 사용 패턴

### Pattern 1: Basic Q&A Agent
### 패턴 1: 기본 Q&A 에이전트

```python
from vanna import Agent
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.sqlite import SqliteConnection
from vanna.tools import RunSqlTool
from vanna.core.registry import ToolRegistry
from vanna.core.user import StaticUserResolver, User, RequestContext
from vanna.capabilities.agent_memory import InMemoryAgentMemory

# 1. Set up components
# 1. 컴포넌트 설정
db = SqliteConnection(path="./database.db")
llm = AnthropicLlmService(api_key="sk-...", model="claude-3-5-sonnet-20241022")
registry = ToolRegistry()
registry.register_local_tool(RunSqlTool(db_connection=db), access_groups=[])

# 2. Create agent
# 2. 에이전트 생성
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=StaticUserResolver(User(id="1", name="User", group_memberships=[])),
    agent_memory=InMemoryAgentMemory()
)

# 3. Use agent
# 3. 에이전트 사용
async def ask(question: str):
    async for component in agent.send_message(
        RequestContext(metadata={}),
        question
    ):
        if component.simple_component:
            print(component.simple_component.text)

await ask("What are our top 5 customers by revenue?")
```

### Pattern 2: Multi-Tool Agent with Permissions
### 패턴 2: 권한이 있는 다중 도구 에이전트

```python
from vanna.tools import RunSqlTool, VisualizeDataTool, FileSystemTool
from vanna.capabilities.file_system import LocalFileSystem

# Create registry
# 레지스트리 생성
registry = ToolRegistry()

# SQL tool - only for analysts and admins
# SQL 도구 - 분석가와 관리자만
registry.register_local_tool(
    RunSqlTool(db_connection=db),
    access_groups=["analyst", "admin"]
)

# Visualization - for everyone
# 시각화 - 모든 사람
registry.register_local_tool(
    VisualizeDataTool(),
    access_groups=[]
)

# File system - only for admins
# 파일 시스템 - 관리자만
registry.register_local_tool(
    FileSystemTool(file_system=LocalFileSystem(base_path="./data")),
    access_groups=["admin"]
)

# Create users with different permissions
# 다른 권한을 가진 사용자 생성
analyst_user = User(
    id="analyst1",
    name="Alice",
    group_memberships=["analyst"]
)

admin_user = User(
    id="admin1",
    name="Bob",
    group_memberships=["admin", "analyst"]
)

regular_user = User(
    id="user1",
    name="Charlie",
    group_memberships=["viewer"]
)

# Analyst can use SQL and visualization
# 분석가는 SQL과 시각화 사용 가능
# Admin can use all tools
# 관리자는 모든 도구 사용 가능
# Regular user can only use visualization
# 일반 사용자는 시각화만 사용 가능
```

### Pattern 3: Agent with Row-Level Security
### 패턴 3: 행 레벨 보안이 있는 에이전트

```python
class SecureRegistry(ToolRegistry):
    async def transform_args(self, tool, args, user, context):
        if tool.name == "run_sql":
            # Ensure user has region
            # 사용자가 지역을 가지고 있는지 확인
            region = user.attributes.get("region")
            if not region:
                return ToolRejection(
                    reason="User must have a region to query data"
                )

            # Add region filter to SQL
            # SQL에 지역 필터 추가
            args.sql = f"SELECT * FROM ({args.sql}) WHERE region = '{region}'"

        return args

# Use secure registry
# 보안 레지스트리 사용
registry = SecureRegistry()
registry.register_local_tool(RunSqlTool(db_connection=db), access_groups=["analyst"])

# Users can only see data for their region
# 사용자는 자신의 지역 데이터만 볼 수 있음
user = User(
    id="user1",
    name="Alice",
    group_memberships=["analyst"],
    attributes={"region": "us-west"}
)
```

### Pattern 4: Agent with Custom Memory
### 패턴 4: 사용자 정의 메모리가 있는 에이전트

```python
from vanna.capabilities.agent_memory import AgentMemory
import chromadb

class ChromaAgentMemory(AgentMemory):
    """
    Agent memory backed by ChromaDB
    ChromaDB로 지원되는 에이전트 메모리
    """

    def __init__(self, collection_name: str):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)

    async def store_interaction(
        self,
        user_query: str,
        tool_calls: List[ToolCall],
        success: bool
    ):
        """
        Store successful tool interactions for learning
        학습을 위해 성공적인 도구 상호작용 저장
        """
        if success:
            self.collection.add(
                documents=[user_query],
                metadatas=[{
                    "tool": tool_calls[0].name,
                    "args": json.dumps(tool_calls[0].arguments)
                }],
                ids=[str(uuid.uuid4())]
            )

    async def get_similar_interactions(
        self,
        query: str,
        limit: int = 5
    ) -> List[dict]:
        """
        Find similar past interactions
        유사한 과거 상호작용 찾기
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        return results

# Use custom memory
# 사용자 정의 메모리 사용
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver,
    agent_memory=ChromaAgentMemory(collection_name="my_agent")
)
```

---

## Customization Guide
## 커스터마이징 가이드

### 1. Custom Lifecycle Hooks
### 1. 사용자 정의 라이프사이클 훅

```python
from vanna.core.lifecycle import LifecycleHook
from vanna.core.tool import ToolResult
from vanna.core.storage import Conversation
from typing import Optional

class QuotaEnforcementHook(LifecycleHook):
    """
    Enforce usage quotas
    사용 할당량 강제
    """

    def __init__(self, max_messages_per_day: int = 100):
        self.max_messages = max_messages_per_day
        self.usage_tracker = {}

    async def before_message(
        self,
        user: User,
        message: str
    ) -> Optional[str]:
        """
        Check quota before processing message
        메시지 처리 전 할당량 확인

        Return None to continue, or modified message
        계속하려면 None 반환, 또는 수정된 메시지
        Raise exception to block
        차단하려면 예외 발생
        """
        user_id = user.id
        today = datetime.now().date()
        key = f"{user_id}:{today}"

        # Get usage count
        # 사용 횟수 가져오기
        count = self.usage_tracker.get(key, 0)

        if count >= self.max_messages:
            raise Exception(f"Daily quota exceeded ({self.max_messages} messages)")

        # Increment count
        # 횟수 증가
        self.usage_tracker[key] = count + 1

        # Don't modify message
        # 메시지 수정하지 않음
        return None

    async def after_message(
        self,
        conversation: Conversation
    ) -> None:
        """
        Called after message is processed
        메시지가 처리된 후 호출됨
        """
        # Could log metrics here
        # 여기서 메트릭 로깅 가능
        pass

    async def before_tool(
        self,
        tool: Tool,
        context: ToolContext
    ) -> None:
        """
        Called before tool execution
        도구 실행 전 호출됨
        """
        # Could log tool usage
        # 도구 사용 로깅 가능
        logger.info(f"Executing tool: {tool.name}")

    async def after_tool(
        self,
        result: ToolResult
    ) -> Optional[ToolResult]:
        """
        Called after tool execution
        도구 실행 후 호출됨

        Return None to keep result, or modified result
        결과를 유지하려면 None 반환, 또는 수정된 결과
        """
        # Could modify result
        # 결과 수정 가능
        if not result.success:
            logger.error(f"Tool failed: {result.error}")

        return None


# Add to agent
# 에이전트에 추가
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    lifecycle_hooks=[QuotaEnforcementHook(max_messages_per_day=50)]
)
```

### 2. Custom LLM Middleware
### 2. 사용자 정의 LLM 미들웨어

```python
from vanna.core.middleware import LlmMiddleware
from vanna.core.llm import LlmRequest, LlmResponse

class CachingMiddleware(LlmMiddleware):
    """
    Cache LLM responses to reduce costs
    비용 절감을 위해 LLM 응답 캐싱
    """

    def __init__(self):
        self.cache = {}

    async def before_llm_request(
        self,
        request: LlmRequest
    ) -> LlmRequest:
        """
        Called before sending to LLM
        LLM에 전송하기 전 호출됨

        Can modify the request
        요청 수정 가능
        """
        # Add custom system prompt
        # 사용자 정의 시스템 프롬프트 추가
        if request.system_prompt:
            request.system_prompt += "\n\nAlways be concise."

        return request

    async def after_llm_response(
        self,
        request: LlmRequest,
        response: LlmResponse
    ) -> LlmResponse:
        """
        Called after receiving from LLM
        LLM에서 수신한 후 호출됨

        Can modify the response
        응답 수정 가능
        """
        # Cache the response
        # 응답 캐싱
        cache_key = self._get_cache_key(request)
        self.cache[cache_key] = response

        return response

    def _get_cache_key(self, request: LlmRequest) -> str:
        # Create cache key from request
        # 요청에서 캐시 키 생성
        return hashlib.md5(
            str(request.messages).encode()
        ).hexdigest()


# Add to agent
# 에이전트에 추가
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    llm_middlewares=[CachingMiddleware()]
)
```

### 3. Custom Observability Provider
### 3. 사용자 정의 관찰성 프로바이더

```python
from vanna.core.observability import ObservabilityProvider, Span
from datadog import statsd
import time

class DatadogObservabilityProvider(ObservabilityProvider):
    """
    Send metrics to Datadog
    Datadog에 메트릭 전송
    """

    async def create_span(
        self,
        name: str,
        attributes: dict = None
    ) -> Span:
        """
        Create a new span for tracing
        추적을 위한 새 스팬 생성
        """
        span = Span(name=name, attributes=attributes or {})
        span.start_time = time.time()
        return span

    async def end_span(self, span: Span) -> None:
        """
        End a span and send metrics
        스팬 종료 및 메트릭 전송
        """
        span.end_time = time.time()
        duration_ms = (span.end_time - span.start_time) * 1000

        # Send to Datadog
        # Datadog에 전송
        statsd.histogram(
            f"vanna.{span.name}.duration",
            duration_ms,
            tags=[f"{k}:{v}" for k, v in span.attributes.items()]
        )

    async def record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        tags: dict = None
    ) -> None:
        """
        Record a metric
        메트릭 기록
        """
        statsd.gauge(
            f"vanna.{name}",
            value,
            tags=[f"{k}:{v}" for k, v in (tags or {}).items()]
        )


# Add to agent
# 에이전트에 추가
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    observability_provider=DatadogObservabilityProvider()
)
```

---

## Advanced Topics
## 고급 주제

### Multi-Agent Systems
### 다중 에이전트 시스템

```python
class RouterAgent:
    """
    Route requests to specialized agents
    특수화된 에이전트로 요청 라우팅
    """

    def __init__(self):
        # Create specialized agents
        # 특수화된 에이전트 생성
        self.sql_agent = self._create_sql_agent()
        self.python_agent = self._create_python_agent()
        self.general_agent = self._create_general_agent()

    async def route(self, message: str, context: RequestContext):
        """
        Route to appropriate agent
        적절한 에이전트로 라우팅
        """
        # Simple routing logic
        # 간단한 라우팅 로직
        if "sql" in message.lower() or "database" in message.lower():
            return await self.sql_agent.send_message(context, message)
        elif "python" in message.lower() or "code" in message.lower():
            return await self.python_agent.send_message(context, message)
        else:
            return await self.general_agent.send_message(context, message)
```

### Conversation Branching
### 대화 분기

```python
class BranchingConversationStore(ConversationStore):
    """
    Support conversation branches for "what-if" scenarios
    "what-if" 시나리오를 위한 대화 분기 지원
    """

    async def branch_conversation(
        self,
        conversation_id: str,
        branch_name: str
    ) -> str:
        """
        Create a branch from current conversation
        현재 대화에서 분기 생성
        """
        # Copy conversation
        # 대화 복사
        original = await self.get_conversation(conversation_id)
        branch_id = f"{conversation_id}:{branch_name}"

        branched = Conversation(
            id=branch_id,
            user=original.user,
            messages=original.messages.copy(),
            metadata={"branch_from": conversation_id}
        )

        await self.update_conversation(branched)
        return branch_id
```

---

## Best Practices
## 모범 사례

### 1. Security
### 1. 보안

```python
# ✅ DO: Use group-based access control
# ✅ 권장: 그룹 기반 접근 제어 사용
registry.register_local_tool(
    DeleteDataTool(),
    access_groups=["admin"]  # Restrict dangerous tools
)

# ✅ DO: Implement RLS for multi-tenant systems
# ✅ 권장: 다중 테넌트 시스템을 위한 RLS 구현
class SecureRegistry(ToolRegistry):
    async def transform_args(self, tool, args, user, context):
        if tool.name == "run_sql":
            tenant_id = user.attributes.get("tenant_id")
            args.sql = f"{args.sql} WHERE tenant_id = '{tenant_id}'"
        return args

# ✅ DO: Enable audit logging
# ✅ 권장: 감사 로깅 활성화
config = AgentConfig(
    audit_config=AuditConfig(
        enabled=True,
        log_tool_invocations=True,
        log_tool_results=True
    )
)

# ❌ DON'T: Give all users access to all tools
# ❌ 비권장: 모든 사용자에게 모든 도구 접근 권한 부여
registry.register_local_tool(DeleteDataTool(), access_groups=[])  # Bad!
```

### 2. Performance
### 2. 성능

```python
# ✅ DO: Use streaming for better UX
# ✅ 권장: 더 나은 UX를 위해 스트리밍 사용
config = AgentConfig(stream_responses=True)

# ✅ DO: Implement caching
# ✅ 권장: 캐싱 구현
class CachingLlmService(LlmService):
    def __init__(self, base_service: LlmService):
        self.base = base_service
        self.cache = {}

    async def send_request(self, request):
        key = self._cache_key(request)
        if key in self.cache:
            return self.cache[key]

        response = await self.base.send_request(request)
        self.cache[key] = response
        return response

# ✅ DO: Set appropriate limits
# ✅ 권장: 적절한 제한 설정
config = AgentConfig(
    max_tool_iterations=5,  # Prevent infinite loops
    max_tokens=4096         # Control costs
)
```

### 3. Error Handling
### 3. 에러 처리

```python
# ✅ DO: Return helpful error messages
# ✅ 권장: 도움이 되는 에러 메시지 반환
async def execute(self, context, args):
    try:
        result = await self._do_work(args)
        return ToolResult(
            success=True,
            result_for_llm=f"Successfully processed {len(result)} items"
        )
    except ValueError as e:
        return ToolResult(
            success=False,
            result_for_llm=f"Invalid input: {e}. Please provide a valid email address.",
            error=str(e)
        )
    except Exception as e:
        logger.exception("Unexpected error")
        return ToolResult(
            success=False,
            result_for_llm="An unexpected error occurred. Please try again.",
            error=str(e)
        )

# ❌ DON'T: Let exceptions bubble up
# ❌ 비권장: 예외가 위로 전파되도록 허용
async def execute(self, context, args):
    result = await self._do_work(args)  # Might raise!
    return ToolResult(success=True, result_for_llm=str(result))
```

---

## Debugging & Troubleshooting
## 디버깅 및 문제 해결

### Enable Debug Logging
### 디버그 로깅 활성화

```python
import logging

# Enable debug logging
# 디버그 로깅 활성화
logging.basicConfig(level=logging.DEBUG)

# Or for specific modules
# 또는 특정 모듈에 대해
logging.getLogger("vanna.core.agent").setLevel(logging.DEBUG)
logging.getLogger("vanna.core.registry").setLevel(logging.DEBUG)
```

### Common Issues
### 일반적인 문제

#### Issue 1: "Tool not found"
#### 문제 1: "도구를 찾을 수 없음"

```python
# Solution: Verify tool is registered
# 해결책: 도구가 등록되었는지 확인
tools = await registry.list_tools()
print(f"Registered tools: {tools}")

# Make sure you registered it
# 등록했는지 확인
registry.register_local_tool(MyTool(), access_groups=[])
```

#### Issue 2: "Insufficient group access"
#### 문제 2: "그룹 접근 권한 부족"

```python
# Solution: Check user's groups vs tool's required groups
# 해결책: 사용자 그룹 vs 도구 필수 그룹 확인
print(f"User groups: {user.group_memberships}")
print(f"Tool requires: {tool.access_groups}")

# Either add user to group or change tool access
# 사용자를 그룹에 추가하거나 도구 접근 변경
user.group_memberships.append("admin")
# OR
registry.register_local_tool(MyTool(), access_groups=[])
```

#### Issue 3: "Invalid arguments"
#### 문제 3: "잘못된 인자"

```python
# Solution: Check Pydantic schema
# 해결책: Pydantic 스키마 확인
class MyToolArgs(BaseModel):
    required_field: str = Field(description="This is required")
    optional_field: Optional[str] = Field(default=None, description="Optional")

    # Add examples for the LLM
    # LLM을 위한 예제 추가
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "required_field": "example value",
                    "optional_field": "optional example"
                }
            ]
        }
    )
```

### Testing Tools
### 도구 테스트

```python
import pytest
from vanna.core.tool import ToolContext
from vanna.core.user import User

@pytest.mark.asyncio
async def test_my_tool():
    """
    Test tool execution
    도구 실행 테스트
    """
    # Create tool
    # 도구 생성
    tool = MyTool()

    # Create context
    # 컨텍스트 생성
    context = ToolContext(
        user=User(id="test", name="Test User", group_memberships=[]),
        conversation_id="test-conv",
        request_id="test-req"
    )

    # Create args
    # 인자 생성
    args = MyToolArgs(required_field="test")

    # Execute
    # 실행
    result = await tool.execute(context, args)

    # Assert
    # 검증
    assert result.success
    assert "expected output" in result.result_for_llm
```

---

**Continue to [EXAMPLES.md](./EXAMPLES.md) for more code examples**
**더 많은 코드 예제는 [EXAMPLES.md](./EXAMPLES.md) 참조**

**Happy coding! 즐거운 코딩 되세요!** 🚀
