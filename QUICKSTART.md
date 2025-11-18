# Vanna Quickstart Guide
# Vanna 빠른 시작 가이드

This guide helps you get started with Vanna in 5 minutes.
이 가이드는 5분 안에 Vanna를 시작하는 데 도움이 됩니다.

## What You'll Learn
## 배울 내용

- Setting up a basic agent
  기본 에이전트 설정
- Registering tools
  도구 등록
- Sending messages
  메시지 전송
- Understanding the response
  응답 이해하기

---

## Installation
## 설치

```bash
pip install vanna
```

---

## Basic Example: Text-to-SQL Agent
## 기본 예제: 텍스트-SQL 에이전트

This example creates an agent that can answer questions about your database using natural language.
이 예제는 자연어를 사용하여 데이터베이스에 대한 질문에 답할 수 있는 에이전트를 생성합니다.

### Step 1: Import Required Modules
### 1단계: 필요한 모듈 가져오기

```python
from vanna.core.agent import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import StaticUserResolver, User, RequestContext
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.sqlite import SqliteConnection
from vanna.tools.run_sql import RunSqlTool
from vanna.capabilities.agent_memory import InMemoryAgentMemory
```

### Step 2: Set Up Database Connection
### 2단계: 데이터베이스 연결 설정

```python
# Create a SQLite database connection
# SQLite 데이터베이스 연결 생성
db = SqliteConnection(path="./my_database.db")

# Or use PostgreSQL:
# 또는 PostgreSQL 사용:
# from vanna.integrations.postgres import PostgresConnection
# db = PostgresConnection(connection_string="postgresql://user:pass@localhost/mydb")
```

### Step 3: Set Up LLM Service
### 3단계: LLM 서비스 설정

```python
# Create an Anthropic LLM service (Claude)
# Anthropic LLM 서비스 생성 (Claude)
llm = AnthropicLlmService(
    api_key="your-anthropic-api-key",
    model="claude-3-5-sonnet-20241022"
)

# Or use OpenAI:
# 또는 OpenAI 사용:
# from vanna.integrations.openai import OpenAILlmService
# llm = OpenAILlmService(api_key="your-openai-api-key")
```

### Step 4: Register Tools
### 4단계: 도구 등록

```python
# Create a tool registry
# 도구 레지스트리 생성
registry = ToolRegistry()

# Register the SQL execution tool
# SQL 실행 도구 등록
# This allows the LLM to query your database
# 이를 통해 LLM이 데이터베이스를 쿼리할 수 있습니다
registry.register_local_tool(
    tool=RunSqlTool(db_connection=db),
    access_groups=[]  # Empty list = accessible to all users
                      # 빈 리스트 = 모든 사용자가 접근 가능
)
```

### Step 5: Set Up User Resolver
### 5단계: 사용자 리졸버 설정

```python
# Create a static user for testing
# 테스트를 위한 정적 사용자 생성
# In production, use a custom UserResolver that integrates with your auth system
# 프로덕션에서는 인증 시스템과 통합하는 사용자 정의 UserResolver를 사용하세요
test_user = User(
    id="user123",
    name="Alice",
    group_memberships=["analyst"],  # User belongs to "analyst" group
                                     # 사용자는 "analyst" 그룹에 속함
    attributes={}
)

user_resolver = StaticUserResolver(user=test_user)
```

### Step 6: Create Agent
### 6단계: 에이전트 생성

```python
# Create an in-memory agent memory (for learning patterns)
# 인메모리 에이전트 메모리 생성 (패턴 학습용)
agent_memory = InMemoryAgentMemory()

# Create the agent
# 에이전트 생성
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory
)
```

### Step 7: Send a Message
### 7단계: 메시지 전송

```python
import asyncio

async def ask_question(question: str):
    """Ask the agent a question"""
    # Create a request context (in production, this comes from HTTP request)
    # 요청 컨텍스트 생성 (프로덕션에서는 HTTP 요청에서 가져옴)
    context = RequestContext(metadata={})

    # Send the message and stream the response
    # 메시지를 전송하고 응답을 스트리밍
    async for component in agent.send_message(
        request_context=context,
        message=question
    ):
        # Each component is a UiComponent with rich and simple versions
        # 각 컴포넌트는 리치 및 단순 버전이 있는 UiComponent입니다
        # For this example, we'll just print the simple text version
        # 이 예제에서는 단순 텍스트 버전만 출력합니다
        if component.simple_component:
            print(component.simple_component.text)

# Run the async function
# 비동기 함수 실행
asyncio.run(ask_question("What is the total revenue by product category?"))
```

---

## Complete Example
## 완전한 예제

Here's the complete code in one place:
다음은 한 곳에 모아진 완전한 코드입니다:

```python
import asyncio
from vanna.core.agent import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import StaticUserResolver, User, RequestContext
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.sqlite import SqliteConnection
from vanna.tools.run_sql import RunSqlTool
from vanna.capabilities.agent_memory import InMemoryAgentMemory

async def main():
    # 1. Database connection
    # 1. 데이터베이스 연결
    db = SqliteConnection(path="./my_database.db")

    # 2. LLM service
    # 2. LLM 서비스
    llm = AnthropicLlmService(
        api_key="your-api-key",
        model="claude-3-5-sonnet-20241022"
    )

    # 3. Tool registry
    # 3. 도구 레지스트리
    registry = ToolRegistry()
    registry.register_local_tool(
        tool=RunSqlTool(db_connection=db),
        access_groups=[]
    )

    # 4. User resolver
    # 4. 사용자 리졸버
    test_user = User(
        id="user123",
        name="Alice",
        group_memberships=["analyst"],
        attributes={}
    )
    user_resolver = StaticUserResolver(user=test_user)

    # 5. Agent memory
    # 5. 에이전트 메모리
    agent_memory = InMemoryAgentMemory()

    # 6. Create agent
    # 6. 에이전트 생성
    agent = Agent(
        llm_service=llm,
        tool_registry=registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory
    )

    # 7. Ask questions
    # 7. 질문하기
    context = RequestContext(metadata={})

    async for component in agent.send_message(
        request_context=context,
        message="What are the top 5 products by revenue?"
    ):
        if component.simple_component:
            print(component.simple_component.text)

# Run
# 실행
asyncio.run(main())
```

---

## Adding More Tools
## 더 많은 도구 추가

### Add Data Visualization
### 데이터 시각화 추가

```python
from vanna.tools.visualize_data import VisualizeDataTool

# Register the visualization tool
# 시각화 도구 등록
registry.register_local_tool(
    tool=VisualizeDataTool(),
    access_groups=[]
)

# Now the agent can create charts!
# 이제 에이전트가 차트를 만들 수 있습니다!
# Example question: "Show me a bar chart of sales by region"
# 예제 질문: "지역별 매출의 막대 차트를 보여주세요"
```

### Add File System Access
### 파일 시스템 접근 추가

```python
from vanna.tools.file_system import FileSystemTool
from vanna.capabilities.file_system import LocalFileSystem

# Create file system capability
# 파일 시스템 기능 생성
fs = LocalFileSystem(base_path="./data")

# Register the file system tool
# 파일 시스템 도구 등록
registry.register_local_tool(
    tool=FileSystemTool(file_system=fs),
    access_groups=[]
)

# Now the agent can read/write files!
# 이제 에이전트가 파일을 읽고 쓸 수 있습니다!
# Example: "Read the contents of sales_report.csv"
# 예제: "sales_report.csv의 내용을 읽어주세요"
```

---

## Access Control Example
## 접근 제어 예제

Restrict tools to specific user groups:
특정 사용자 그룹으로 도구를 제한하세요:

```python
# Only users in "admin" group can run SQL
# "admin" 그룹의 사용자만 SQL을 실행할 수 있음
registry.register_local_tool(
    tool=RunSqlTool(db_connection=db),
    access_groups=["admin"]
)

# Create user without admin access
# 관리자 접근 권한이 없는 사용자 생성
regular_user = User(
    id="user456",
    name="Bob",
    group_memberships=["viewer"],  # Not in "admin" group
                                    # "admin" 그룹에 속하지 않음
    attributes={}
)

# When Bob tries to run SQL, it will be denied
# Bob이 SQL을 실행하려고 하면 거부됩니다
# ✗ Access denied: Insufficient group access for tool 'run_sql'
```

---

## Row-Level Security Example
## 행 레벨 보안 예제

Apply user-specific filters to SQL queries:
SQL 쿼리에 사용자별 필터를 적용하세요:

```python
from vanna.core.registry import ToolRegistry
from vanna.core.tool import ToolRejection

class SecureToolRegistry(ToolRegistry):
    """Custom registry with row-level security"""
    """행 레벨 보안이 있는 사용자 정의 레지스트리"""

    async def transform_args(self, tool, args, user, context):
        # Only apply RLS to SQL queries
        # SQL 쿼리에만 RLS 적용
        if tool.name == "run_sql":
            # Check if user has a region assigned
            # 사용자에게 지역이 할당되어 있는지 확인
            region = user.attributes.get("region")
            if not region:
                return ToolRejection(
                    reason="User must have a region assigned to run queries"
                )

            # Add WHERE clause to restrict data access
            # 데이터 접근 제한을 위해 WHERE 절 추가
            original_sql = args.sql
            args.sql = f"{original_sql} WHERE region = '{region}'"

        return args

# Use the secure registry
# 보안 레지스트리 사용
registry = SecureToolRegistry()

# Create user with region
# 지역이 있는 사용자 생성
user_with_region = User(
    id="user789",
    name="Charlie",
    group_memberships=["analyst"],
    attributes={"region": "us-west"}  # User can only see us-west data
                                       # 사용자는 us-west 데이터만 볼 수 있음
)
```

---

## Understanding the Response
## 응답 이해하기

The agent streams `UiComponent` objects. Each has:
에이전트는 `UiComponent` 객체를 스트리밍합니다. 각각은 다음을 가집니다:

- **Rich Component** - Full-featured UI (charts, tables, buttons)
  **리치 컴포넌트** - 완전한 기능의 UI (차트, 테이블, 버튼)
- **Simple Component** - Text fallback for basic clients
  **단순 컴포넌트** - 기본 클라이언트를 위한 텍스트 폴백

```python
async for component in agent.send_message(...):
    # Rich component (for web UI)
    # 리치 컴포넌트 (웹 UI용)
    if component.rich_component:
        if isinstance(component.rich_component, DataFrameComponent):
            print("Got a data table!")
            print(component.rich_component.data)
        elif isinstance(component.rich_component, ChartComponent):
            print("Got a chart!")
            print(component.rich_component.chart_data)

    # Simple component (for CLI or basic clients)
    # 단순 컴포넌트 (CLI 또는 기본 클라이언트용)
    if component.simple_component:
        print(component.simple_component.text)
```

---

## Common Component Types
## 일반 컴포넌트 타입

| Component | When Used | Korean |
|-----------|-----------|--------|
| `RichTextComponent` | LLM's text response | LLM의 텍스트 응답 |
| `DataFrameComponent` | SQL query results | SQL 쿼리 결과 |
| `ChartComponent` | Data visualizations | 데이터 시각화 |
| `StatusCardComponent` | Tool execution status | 도구 실행 상태 |
| `TaskTrackerUpdateComponent` | Progress updates | 진행 상황 업데이트 |
| `StatusBarUpdateComponent` | Agent status | 에이전트 상태 |

---

## Next Steps
## 다음 단계

1. **Read ARCHITECTURE.md** - Understand the framework design
   **ARCHITECTURE.md 읽기** - 프레임워크 설계 이해하기

2. **Explore examples/** - See more complex examples
   **examples/ 탐색하기** - 더 복잡한 예제 보기

3. **Create custom tools** - Extend the agent's capabilities
   **사용자 정의 도구 생성** - 에이전트의 기능 확장

4. **Add lifecycle hooks** - Hook into execution flow
   **라이프사이클 훅 추가** - 실행 흐름에 훅

5. **Deploy with FastAPI** - Use the web server
   **FastAPI로 배포** - 웹 서버 사용

---

## Troubleshooting
## 문제 해결

### Error: "Tool not found"
### 에러: "도구를 찾을 수 없음"

Make sure you registered the tool:
도구를 등록했는지 확인하세요:
```python
registry.register_local_tool(tool=MyTool(), access_groups=[])
```

### Error: "Insufficient group access"
### 에러: "그룹 접근 권한 부족"

The user doesn't belong to the required groups:
사용자가 필요한 그룹에 속하지 않습니다:
```python
# Either add user to the group:
# 사용자를 그룹에 추가하거나:
user.group_memberships.append("admin")

# Or remove the restriction:
# 또는 제한을 제거하세요:
registry.register_local_tool(tool=MyTool(), access_groups=[])
```

### Error: "Invalid arguments"
### 에러: "잘못된 인자"

The LLM provided arguments that don't match your Pydantic schema. Check:
LLM이 Pydantic 스키마와 일치하지 않는 인자를 제공했습니다. 확인하세요:
1. Tool description is clear
   도구 설명이 명확한지
2. Pydantic model fields have good descriptions
   Pydantic 모델 필드에 좋은 설명이 있는지
3. Required vs optional fields are correctly marked
   필수 대 선택적 필드가 올바르게 표시되어 있는지

---

## Support
## 지원

- **GitHub Issues:** https://github.com/vanna-ai/vanna/issues
- **Documentation:** See ARCHITECTURE.md and inline code comments
  **문서:** ARCHITECTURE.md 및 인라인 코드 주석 참조

---

**Happy building! 즐거운 개발 되세요!** 🎉
