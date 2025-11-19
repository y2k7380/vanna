# Vanna Code Examples
# Vanna 코드 예제

Practical code examples for common use cases.
일반적인 사용 사례를 위한 실용적인 코드 예제.

---

## Table of Contents
## 목차

1. [Basic Examples](#basic-examples)
2. [Custom Tools](#custom-tools)
3. [Authentication & Authorization](#authentication--authorization)
4. [Data Security](#data-security)
5. [Integration Examples](#integration-examples)
6. [Web Server Examples](#web-server-examples)
7. [Advanced Patterns](#advanced-patterns)

---

## Basic Examples
## 기본 예제

### Example 1: Simple Text-to-SQL Agent
### 예제 1: 간단한 텍스트-SQL 에이전트

```python
"""
Basic agent that can answer questions about a database
데이터베이스에 대한 질문에 답할 수 있는 기본 에이전트
"""
import asyncio
from vanna.core.agent import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import StaticUserResolver, User, RequestContext
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.sqlite import SqliteConnection
from vanna.tools.run_sql import RunSqlTool
from vanna.capabilities.agent_memory import InMemoryAgentMemory

async def main():
    # Create SQLite database connection
    # SQLite 데이터베이스 연결 생성
    db = SqliteConnection(path="./chinook.db")  # Sample database

    # Create LLM service (using Claude)
    # LLM 서비스 생성 (Claude 사용)
    llm = AnthropicLlmService(
        api_key="your-api-key",
        model="claude-3-5-sonnet-20241022"
    )

    # Create tool registry and register SQL tool
    # 도구 레지스트리 생성 및 SQL 도구 등록
    registry = ToolRegistry()
    registry.register_local_tool(
        tool=RunSqlTool(db_connection=db),
        access_groups=[]  # Accessible to all users
    )

    # Create static user (for testing)
    # 정적 사용자 생성 (테스트용)
    user = User(
        id="user1",
        name="Test User",
        group_memberships=[],
        attributes={}
    )

    # Create agent
    # 에이전트 생성
    agent = Agent(
        llm_service=llm,
        tool_registry=registry,
        user_resolver=StaticUserResolver(user),
        agent_memory=InMemoryAgentMemory()
    )

    # Ask questions
    # 질문하기
    questions = [
        "How many customers are in the database?",
        "What are the top 5 albums by number of tracks?",
        "Show me the total sales by country",
    ]

    for question in questions:
        print(f"\n❓ Question: {question}")
        print("=" * 60)

        async for component in agent.send_message(
            request_context=RequestContext(metadata={}),
            message=question
        ):
            # Print simple text version
            # 간단한 텍스트 버전 출력
            if component.simple_component:
                print(component.simple_component.text)

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Agent with Visualization
### 예제 2: 시각화가 있는 에이전트

```python
"""
Agent that can create charts and visualizations
차트와 시각화를 만들 수 있는 에이전트
"""
from vanna.tools import RunSqlTool, VisualizeDataTool

# Create registry with SQL and visualization tools
# SQL 및 시각화 도구가 있는 레지스트리 생성
registry = ToolRegistry()

registry.register_local_tool(
    RunSqlTool(db_connection=db),
    access_groups=[]
)

registry.register_local_tool(
    VisualizeDataTool(),
    access_groups=[]
)

# Create agent (same as before)
# 에이전트 생성 (이전과 동일)
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=StaticUserResolver(user),
    agent_memory=InMemoryAgentMemory()
)

# Now you can ask for visualizations!
# 이제 시각화를 요청할 수 있습니다!
async for component in agent.send_message(
    RequestContext(metadata={}),
    "Show me a bar chart of sales by country"
):
    if component.rich_component:
        # This will be a ChartComponent with Plotly chart
        # 이것은 Plotly 차트가 있는 ChartComponent입니다
        print(component.rich_component)
```

---

## Custom Tools
## 사용자 정의 도구

### Example 3: Weather API Tool
### 예제 3: 날씨 API 도구

```python
"""
Custom tool that calls an external API
외부 API를 호출하는 사용자 정의 도구
"""
from pydantic import BaseModel, Field
from vanna.core.tool import Tool, ToolContext, ToolResult
from vanna.components import UiComponent, RichTextComponent, SimpleTextComponent
import httpx
from typing import Type

class WeatherArgs(BaseModel):
    """Arguments for weather tool / 날씨 도구 인자"""
    city: str = Field(description="City name (e.g., 'San Francisco')")
    units: str = Field(
        default="celsius",
        description="Temperature units: 'celsius' or 'fahrenheit'"
    )

class WeatherTool(Tool[WeatherArgs]):
    """Get current weather for a city / 도시의 현재 날씨 가져오기"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return """Get current weather information for a city.

        Use this when the user asks about:
        - Current weather
        - Temperature
        - Weather conditions

        Returns temperature, conditions, humidity, and wind speed.
        """

    @property
    def access_groups(self) -> list:
        return []  # Available to all users

    def get_args_schema(self) -> Type[WeatherArgs]:
        return WeatherArgs

    async def execute(
        self,
        context: ToolContext,
        args: WeatherArgs
    ) -> ToolResult:
        """Fetch weather data from API / API에서 날씨 데이터 가져오기"""
        try:
            # Call OpenWeatherMap API
            # OpenWeatherMap API 호출
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "q": args.city,
                        "appid": self.api_key,
                        "units": "metric" if args.units == "celsius" else "imperial"
                    }
                )
                response.raise_for_status()
                data = response.json()

            # Extract weather info
            # 날씨 정보 추출
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            conditions = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]

            # Format result for LLM
            # LLM을 위한 결과 형식화
            unit_symbol = "°C" if args.units == "celsius" else "°F"
            result_text = f"""Weather in {args.city}:
🌡️ Temperature: {temp}{unit_symbol} (feels like {feels_like}{unit_symbol})
☁️ Conditions: {conditions}
💧 Humidity: {humidity}%
💨 Wind: {wind_speed} m/s
"""

            # Create UI component
            # UI 컴포넌트 생성
            ui_component = UiComponent(
                rich_component=RichTextComponent(
                    content=result_text,
                    markdown=True
                ),
                simple_component=SimpleTextComponent(text=result_text)
            )

            return ToolResult(
                success=True,
                result_for_llm=result_text,
                ui_component=ui_component
            )

        except httpx.HTTPError as e:
            return ToolResult(
                success=False,
                result_for_llm=f"Failed to fetch weather: {str(e)}",
                error=str(e)
            )

# Register the tool
# 도구 등록
registry.register_local_tool(
    WeatherTool(api_key="your-openweathermap-key"),
    access_groups=[]
)
```

### Example 4: Email Sending Tool
### 예제 4: 이메일 전송 도구

```python
"""
Tool that sends emails (restricted to admins only)
이메일을 전송하는 도구 (관리자만 사용 가능)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailArgs(BaseModel):
    """Email arguments / 이메일 인자"""
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body (plain text)")

class EmailTool(Tool[EmailArgs]):
    """Send email via SMTP / SMTP를 통한 이메일 전송"""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    @property
    def name(self) -> str:
        return "send_email"

    @property
    def description(self) -> str:
        return """Send an email to a recipient.

        Use this when the user wants to:
        - Send an email
        - Notify someone
        - Share information via email

        Requires: recipient email, subject, and message body.
        """

    @property
    def access_groups(self) -> list:
        # Only admins can send emails
        # 관리자만 이메일 전송 가능
        return ["admin"]

    def get_args_schema(self) -> Type[EmailArgs]:
        return EmailArgs

    async def execute(self, context: ToolContext, args: EmailArgs) -> ToolResult:
        """Send email / 이메일 전송"""
        try:
            # Create message
            # 메시지 생성
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = args.to
            msg["Subject"] = args.subject
            msg.attach(MIMEText(args.body, "plain"))

            # Send email
            # 이메일 전송
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            # Log for audit
            # 감사를 위한 로그
            context.observability_provider.record_metric(
                "email.sent",
                1.0,
                "count",
                tags={"user": context.user.id}
            )

            return ToolResult(
                success=True,
                result_for_llm=f"Email sent successfully to {args.to}"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                result_for_llm=f"Failed to send email: {str(e)}",
                error=str(e)
            )

# Register (only for admins)
# 등록 (관리자만)
registry.register_local_tool(
    EmailTool(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username="your-email@gmail.com",
        password="your-app-password"
    ),
    access_groups=["admin"]
)
```

### Example 5: Custom Calculator Tool
### 예제 5: 사용자 정의 계산기 도구

```python
"""
Simple calculator tool for math operations
수학 연산을 위한 간단한 계산기 도구
"""
from typing import Literal

class CalculatorArgs(BaseModel):
    """Calculator arguments / 계산기 인자"""
    operation: Literal["add", "subtract", "multiply", "divide"] = Field(
        description="Math operation to perform"
    )
    a: float = Field(description="First number")
    b: float = Field(description="Second number")

class CalculatorTool(Tool[CalculatorArgs]):
    """Perform basic math operations / 기본 수학 연산 수행"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return """Perform basic math operations: add, subtract, multiply, divide.

        Use this when the user asks for calculations.
        """

    def get_args_schema(self) -> Type[CalculatorArgs]:
        return CalculatorArgs

    async def execute(self, context: ToolContext, args: CalculatorArgs) -> ToolResult:
        """Perform calculation / 계산 수행"""
        try:
            if args.operation == "add":
                result = args.a + args.b
            elif args.operation == "subtract":
                result = args.a - args.b
            elif args.operation == "multiply":
                result = args.a * args.b
            elif args.operation == "divide":
                if args.b == 0:
                    return ToolResult(
                        success=False,
                        result_for_llm="Cannot divide by zero",
                        error="Division by zero"
                    )
                result = args.a / args.b

            return ToolResult(
                success=True,
                result_for_llm=f"{args.a} {args.operation} {args.b} = {result}"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                result_for_llm=f"Calculation failed: {str(e)}",
                error=str(e)
            )

# Register
# 등록
registry.register_local_tool(CalculatorTool(), access_groups=[])
```

---

## Authentication & Authorization
## 인증 및 권한 부여

### Example 6: JWT-Based User Resolver
### 예제 6: JWT 기반 사용자 리졸버

```python
"""
Resolve users from JWT tokens in HTTP headers
HTTP 헤더의 JWT 토큰에서 사용자 해결
"""
from vanna.core.user import UserResolver, User, RequestContext
import jwt
from typing import Optional

class JWTUserResolver(UserResolver):
    """Resolve user from JWT token / JWT 토큰에서 사용자 해결"""

    def __init__(self, jwt_secret: str, jwt_algorithm: str = "HS256"):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm

    async def resolve_user(self, context: RequestContext) -> User:
        """
        Extract and validate JWT token, return User
        JWT 토큰 추출 및 검증, User 반환
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
            # Decode and validate JWT
            # JWT 디코딩 및 검증
            claims = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )

            # Extract user info from claims
            # claims에서 사용자 정보 추출
            user_id = claims.get("sub")  # Subject (user ID)
            name = claims.get("name", "Unknown")
            email = claims.get("email")

            # Extract groups/roles
            # 그룹/역할 추출
            groups = claims.get("groups", [])
            # Some systems use "roles" instead
            # 일부 시스템은 "roles" 사용
            if not groups and "roles" in claims:
                groups = claims.get("roles", [])

            # Extract custom attributes
            # 사용자 정의 속성 추출
            attributes = {
                "email": email,
                "region": claims.get("region"),
                "department": claims.get("department"),
                "tenant_id": claims.get("tenant_id"),
                # Add any other custom claims
                # 다른 사용자 정의 claims 추가
            }

            return User(
                id=user_id,
                name=name,
                group_memberships=groups,
                attributes=attributes
            )

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

# Usage with FastAPI
# FastAPI와 함께 사용
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()
user_resolver = JWTUserResolver(jwt_secret="your-secret-key")

# Create agent with JWT resolver
# JWT 리졸버로 에이전트 생성
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver,  # Use JWT resolver
    agent_memory=agent_memory
)

@app.post("/chat")
async def chat(
    message: str,
    authorization: str = Header(None)
):
    """Chat endpoint with JWT auth / JWT 인증이 있는 채팅 엔드포인트"""
    try:
        # Build request context
        # 요청 컨텍스트 구성
        context = RequestContext(
            metadata={"authorization": authorization}
        )

        # Agent will use JWT resolver to get user
        # Agent는 JWT 리졸버를 사용하여 사용자 가져옴
        async for component in agent.send_message(context, message):
            yield component

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
```

### Example 7: OAuth2 User Resolver
### 예제 7: OAuth2 사용자 리졸버

```python
"""
Resolve users from OAuth2 tokens (e.g., Google, Microsoft)
OAuth2 토큰에서 사용자 해결 (예: Google, Microsoft)
"""
from authlib.integrations.httpx_client import AsyncOAuth2Client

class OAuth2UserResolver(UserResolver):
    """Resolve user from OAuth2 token / OAuth2 토큰에서 사용자 해결"""

    def __init__(self, userinfo_endpoint: str):
        self.userinfo_endpoint = userinfo_endpoint

    async def resolve_user(self, context: RequestContext) -> User:
        """
        Validate OAuth2 token and get user info
        OAuth2 토큰 검증 및 사용자 정보 가져오기
        """
        # Get access token
        # 액세스 토큰 가져오기
        auth_header = context.metadata.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise ValueError("Missing or invalid authorization header")

        access_token = auth_header.replace("Bearer ", "")

        # Call userinfo endpoint
        # userinfo 엔드포인트 호출
        async with AsyncOAuth2Client() as client:
            response = await client.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            userinfo = response.json()

        # Map OAuth2 user to Vanna User
        # OAuth2 사용자를 Vanna User에 매핑
        return User(
            id=userinfo["sub"],
            name=userinfo.get("name", "Unknown"),
            group_memberships=userinfo.get("groups", []),
            attributes={
                "email": userinfo.get("email"),
                "picture": userinfo.get("picture"),
            }
        )

# Usage for Google OAuth2
# Google OAuth2 사용
google_resolver = OAuth2UserResolver(
    userinfo_endpoint="https://www.googleapis.com/oauth2/v3/userinfo"
)

# Usage for Microsoft Azure AD
# Microsoft Azure AD 사용
azure_resolver = OAuth2UserResolver(
    userinfo_endpoint="https://graph.microsoft.com/v1.0/me"
)
```

---

## Data Security
## 데이터 보안

### Example 8: Row-Level Security with Multi-Tenancy
### 예제 8: 다중 테넌트와 행 레벨 보안

```python
"""
Implement RLS for multi-tenant SaaS application
다중 테넌트 SaaS 애플리케이션을 위한 RLS 구현
"""
from vanna.core.registry import ToolRegistry
from vanna.core.tool import ToolRejection

class MultiTenantRegistry(ToolRegistry):
    """
    Registry with tenant isolation
    테넌트 격리가 있는 레지스트리
    """

    async def transform_args(self, tool, args, user, context):
        """
        Add tenant filter to all SQL queries
        모든 SQL 쿼리에 테넌트 필터 추가
        """
        # Only apply to SQL tools
        # SQL 도구에만 적용
        if tool.name != "run_sql":
            return args

        # Ensure user has tenant_id
        # 사용자가 tenant_id를 가지고 있는지 확인
        tenant_id = user.attributes.get("tenant_id")
        if not tenant_id:
            return ToolRejection(
                reason="User must belong to a tenant to query data"
            )

        # Parse SQL and add tenant filter
        # SQL 파싱 및 테넌트 필터 추가
        original_sql = args.sql

        # Validate SQL doesn't try to bypass tenant filter
        # SQL이 테넌트 필터를 우회하려고 시도하지 않는지 검증
        if "tenant_id" in original_sql.lower():
            return ToolRejection(
                reason="Cannot manually specify tenant_id in queries"
            )

        # Add tenant filter
        # 테넌트 필터 추가
        if "WHERE" in original_sql.upper():
            # Add to existing WHERE
            # 기존 WHERE에 추가
            modified_sql = original_sql.replace(
                "WHERE",
                f"WHERE tenant_id = '{tenant_id}' AND",
                1
            )
        else:
            # Add new WHERE
            # 새 WHERE 추가
            modified_sql = f"{original_sql} WHERE tenant_id = '{tenant_id}'"

        args.sql = modified_sql

        # Log for audit
        # 감사를 위한 로그
        logger.info(
            f"Applied tenant filter for tenant {tenant_id}",
            extra={
                "user_id": user.id,
                "tenant_id": tenant_id,
                "original_sql": original_sql,
                "modified_sql": modified_sql
            }
        )

        return args

# Usage
# 사용
registry = MultiTenantRegistry()

# Users from different tenants can only see their own data
# 다른 테넌트의 사용자는 자신의 데이터만 볼 수 있음
user_tenant_a = User(
    id="user1",
    name="Alice",
    group_memberships=["user"],
    attributes={"tenant_id": "tenant-a"}
)

user_tenant_b = User(
    id="user2",
    name="Bob",
    group_memberships=["user"],
    attributes={"tenant_id": "tenant-b"}
)

# When Alice queries: SELECT * FROM orders
# SQL becomes: SELECT * FROM orders WHERE tenant_id = 'tenant-a'
# Alice가 쿼리할 때: SELECT * FROM orders
# SQL이 됨: SELECT * FROM orders WHERE tenant_id = 'tenant-a'
```

### Example 9: Column-Level Access Control
### 예제 9: 컬럼 레벨 접근 제어

```python
"""
Hide sensitive columns based on user permissions
사용자 권한에 따라 민감한 컬럼 숨기기
"""
import sqlparse

class ColumnSecurityRegistry(ToolRegistry):
    """
    Registry with column-level security
    컬럼 레벨 보안이 있는 레지스트리
    """

    # Define sensitive columns per table
    # 테이블별 민감한 컬럼 정의
    SENSITIVE_COLUMNS = {
        "customers": ["ssn", "credit_card", "salary"],
        "employees": ["ssn", "salary", "bank_account"],
    }

    # Define which groups can see sensitive columns
    # 어떤 그룹이 민감한 컬럼을 볼 수 있는지 정의
    PRIVILEGED_GROUPS = ["admin", "finance"]

    async def transform_args(self, tool, args, user, context):
        """
        Remove sensitive columns from SELECT statements
        SELECT 문에서 민감한 컬럼 제거
        """
        if tool.name != "run_sql":
            return args

        # Check if user has privileged access
        # 사용자가 특권 접근 권한을 가지고 있는지 확인
        is_privileged = any(
            group in user.group_memberships
            for group in self.PRIVILEGED_GROUPS
        )

        if is_privileged:
            # Privileged users can see everything
            # 특권 사용자는 모든 것을 볼 수 있음
            return args

        # Parse SQL
        # SQL 파싱
        try:
            parsed = sqlparse.parse(args.sql)[0]

            # Check for SELECT *
            # SELECT * 확인
            if "SELECT *" in args.sql.upper():
                # Need to expand * and remove sensitive columns
                # *를 확장하고 민감한 컬럼 제거 필요
                return ToolRejection(
                    reason="Please specify column names explicitly (SELECT * not allowed for non-privileged users)"
                )

            # Check if query accesses sensitive columns
            # 쿼리가 민감한 컬럼에 접근하는지 확인
            for table, sensitive_cols in self.SENSITIVE_COLUMNS.items():
                for col in sensitive_cols:
                    if col.lower() in args.sql.lower():
                        return ToolRejection(
                            reason=f"Access denied to column '{col}'. Contact an administrator for access."
                        )

            return args

        except Exception as e:
            logger.error(f"Error parsing SQL: {e}")
            return args

# Usage
# 사용
registry = ColumnSecurityRegistry()

# Regular user cannot access sensitive columns
# 일반 사용자는 민감한 컬럼에 접근할 수 없음
# Query: SELECT name, ssn FROM customers
# Result: Access denied to column 'ssn'
```

### Example 10: Data Masking
### 예제 10: 데이터 마스킹

```python
"""
Mask sensitive data in query results
쿼리 결과에서 민감한 데이터 마스킹
"""
from vanna.core.lifecycle import LifecycleHook
from vanna.core.tool import ToolResult
import re

class DataMaskingHook(LifecycleHook):
    """
    Mask sensitive data in tool results
    도구 결과에서 민감한 데이터 마스킹
    """

    async def after_tool(self, result: ToolResult) -> Optional[ToolResult]:
        """
        Mask sensitive patterns in results
        결과에서 민감한 패턴 마스킹
        """
        if not result.success:
            return None

        # Patterns to mask
        # 마스킹할 패턴
        patterns = {
            # Credit card numbers (마스킹: 신용카드 번호)
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b': 'XXXX-XXXX-XXXX-XXXX',
            # SSN (마스킹: 사회보장번호)
            r'\b\d{3}-\d{2}-\d{4}\b': 'XXX-XX-XXXX',
            # Email (partially mask)
            r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})': r'\1***@\2',
        }

        # Apply masking to result text
        # 결과 텍스트에 마스킹 적용
        masked_text = result.result_for_llm
        for pattern, replacement in patterns.items():
            masked_text = re.sub(pattern, replacement, masked_text)

        # Return modified result
        # 수정된 결과 반환
        result.result_for_llm = masked_text
        return result

# Add to agent
# 에이전트에 추가
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    lifecycle_hooks=[DataMaskingHook()]
)
```

---

## Integration Examples
## 통합 예제

### Example 11: Using with PostgreSQL
### 예제 11: PostgreSQL와 함께 사용

```python
"""
Connect to PostgreSQL database
PostgreSQL 데이터베이스 연결
"""
from vanna.integrations.postgres import PostgresConnection
from vanna.tools.run_sql import RunSqlTool

# Create PostgreSQL connection
# PostgreSQL 연결 생성
db = PostgresConnection(
    connection_string="postgresql://user:password@localhost:5432/mydb"
    # Or use individual parameters
    # 또는 개별 매개변수 사용
    # host="localhost",
    # port=5432,
    # database="mydb",
    # user="user",
    # password="password"
)

# Create SQL tool
# SQL 도구 생성
sql_tool = RunSqlTool(db_connection=db)

# Register
# 등록
registry.register_local_tool(sql_tool, access_groups=["analyst"])
```

### Example 12: Using with ChromaDB for RAG
### 예제 12: RAG를 위한 ChromaDB 사용

```python
"""
Use ChromaDB for agent memory and RAG
에이전트 메모리 및 RAG를 위한 ChromaDB 사용
"""
from vanna.integrations.chromadb import ChromaDBAgentMemory

# Create ChromaDB memory
# ChromaDB 메모리 생성
agent_memory = ChromaDBAgentMemory(
    collection_name="my_agent_memory",
    persist_directory="./chroma_db"
)

# Agent will now remember successful tool interactions
# 에이전트는 이제 성공적인 도구 상호작용을 기억함
agent = Agent(
    llm_service=llm,
    tool_registry=registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory
)

# When user asks similar questions, agent can retrieve past examples
# 사용자가 유사한 질문을 할 때 에이전트는 과거 예제를 검색할 수 있음
```

### Example 13: Using OpenAI Instead of Anthropic
### 예제 13: Anthropic 대신 OpenAI 사용

```python
"""
Use OpenAI GPT models
OpenAI GPT 모델 사용
"""
from vanna.integrations.openai import OpenAILlmService

# Create OpenAI service
# OpenAI 서비스 생성
llm = OpenAILlmService(
    api_key="sk-...",
    model="gpt-4"  # or "gpt-3.5-turbo"
)

# Everything else remains the same
# 나머지는 모두 동일함
agent = Agent(
    llm_service=llm,  # Now using OpenAI
    tool_registry=registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory
)
```

---

## Web Server Examples
## 웹 서버 예제

### Example 14: FastAPI Server with Streaming
### 예제 14: 스트리밍이 있는 FastAPI 서버

```python
"""
Complete FastAPI server with SSE streaming
SSE 스트리밍이 있는 완전한 FastAPI 서버
"""
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

app = FastAPI()

# Create agent (from previous examples)
# 에이전트 생성 (이전 예제에서)
# ... agent creation code ...

class ChatRequest(BaseModel):
    """Chat request model / 채팅 요청 모델"""
    message: str
    conversation_id: Optional[str] = None

@app.post("/chat")
async def chat(
    request: ChatRequest,
    authorization: str = Header(None)
):
    """
    Chat endpoint with streaming
    스트리밍이 있는 채팅 엔드포인트
    """
    try:
        # Build request context
        # 요청 컨텍스트 구성
        context = RequestContext(
            metadata={"authorization": authorization}
        )

        # Create SSE stream
        # SSE 스트림 생성
        async def event_stream():
            async for component in agent.send_message(
                context,
                request.message,
                conversation_id=request.conversation_id
            ):
                # Convert component to JSON
                # 컴포넌트를 JSON으로 변환
                data = {
                    "type": component.rich_component.__class__.__name__,
                    "content": component.simple_component.text
                    if component.simple_component
                    else None
                }

                # Send as SSE event
                # SSE 이벤트로 전송
                yield f"data: {json.dumps(data)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream"
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check / 상태 확인"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Example 15: Flask Server with WebSockets
### 예제 15: WebSocket이 있는 Flask 서버

```python
"""
Flask server with WebSocket support
WebSocket 지원이 있는 Flask 서버
"""
from flask import Flask, request
from flask_socketio import SocketIO, emit
import asyncio

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on("chat")
def handle_chat(data):
    """
    Handle chat messages via WebSocket
    WebSocket을 통한 채팅 메시지 처리
    """
    message = data.get("message")
    conversation_id = data.get("conversation_id")

    # Get authorization from handshake
    # 핸드셰이크에서 권한 가져오기
    auth_header = request.headers.get("Authorization")

    # Build context
    # 컨텍스트 구성
    context = RequestContext(
        metadata={"authorization": auth_header}
    )

    # Stream responses
    # 응답 스트리밍
    async def stream_response():
        async for component in agent.send_message(
            context,
            message,
            conversation_id=conversation_id
        ):
            # Emit each component to client
            # 각 컴포넌트를 클라이언트에 전송
            emit("message", {
                "type": component.rich_component.__class__.__name__,
                "content": component.simple_component.text
            })

    # Run async in sync context
    # 동기 컨텍스트에서 비동기 실행
    asyncio.run(stream_response())

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
```

---

## Advanced Patterns
## 고급 패턴

### Example 16: Multi-Agent Router
### 예제 16: 다중 에이전트 라우터

```python
"""
Route requests to specialized agents
특수화된 에이전트로 요청 라우팅
"""

class AgentRouter:
    """
    Route messages to specialized agents
    특수화된 에이전트로 메시지 라우팅
    """

    def __init__(self):
        # Create specialized agents
        # 특수화된 에이전트 생성

        # SQL Agent - for database queries
        # SQL 에이전트 - 데이터베이스 쿼리용
        self.sql_agent = self._create_sql_agent()

        # Python Agent - for code execution
        # Python 에이전트 - 코드 실행용
        self.python_agent = self._create_python_agent()

        # General Agent - for conversations
        # 일반 에이전트 - 대화용
        self.general_agent = self._create_general_agent()

    def _create_sql_agent(self) -> Agent:
        """Create agent specialized for SQL"""
        registry = ToolRegistry()
        registry.register_local_tool(
            RunSqlTool(db_connection=db),
            access_groups=[]
        )
        return Agent(
            llm_service=llm,
            tool_registry=registry,
            user_resolver=user_resolver,
            agent_memory=InMemoryAgentMemory()
        )

    def _create_python_agent(self) -> Agent:
        """Create agent specialized for Python code"""
        registry = ToolRegistry()
        registry.register_local_tool(
            PythonTool(),
            access_groups=[]
        )
        return Agent(
            llm_service=llm,
            tool_registry=registry,
            user_resolver=user_resolver,
            agent_memory=InMemoryAgentMemory()
        )

    def _create_general_agent(self) -> Agent:
        """Create general conversation agent"""
        registry = ToolRegistry()
        # No tools, just conversation
        # 도구 없음, 대화만
        return Agent(
            llm_service=llm,
            tool_registry=registry,
            user_resolver=user_resolver,
            agent_memory=InMemoryAgentMemory()
        )

    async def route(
        self,
        message: str,
        context: RequestContext
    ) -> AsyncGenerator[UiComponent, None]:
        """
        Route message to appropriate agent
        메시지를 적절한 에이전트로 라우팅
        """
        # Simple keyword-based routing
        # 간단한 키워드 기반 라우팅
        message_lower = message.lower()

        if any(word in message_lower for word in ["sql", "query", "database", "table"]):
            # Route to SQL agent
            # SQL 에이전트로 라우팅
            async for component in self.sql_agent.send_message(context, message):
                yield component

        elif any(word in message_lower for word in ["python", "code", "script"]):
            # Route to Python agent
            # Python 에이전트로 라우팅
            async for component in self.python_agent.send_message(context, message):
                yield component

        else:
            # Route to general agent
            # 일반 에이전트로 라우팅
            async for component in self.general_agent.send_message(context, message):
                yield component

# Usage
# 사용
router = AgentRouter()

async for component in router.route("Show me total sales", context):
    print(component.simple_component.text)
```

### Example 17: Conversation Branching
### 예제 17: 대화 분기

```python
"""
Create branches in conversations for "what-if" scenarios
"what-if" 시나리오를 위한 대화 분기 생성
"""
from vanna.core.storage import ConversationStore, Conversation

class BranchingConversationStore(ConversationStore):
    """
    Conversation store with branching support
    분기 지원이 있는 대화 저장소
    """

    def __init__(self):
        self.conversations = {}
        self.branches = {}  # Map conversation_id -> list of branch_ids

    async def create_branch(
        self,
        conversation_id: str,
        branch_name: str,
        user: User
    ) -> str:
        """
        Create a branch from current conversation
        현재 대화에서 분기 생성

        Returns: branch_id
        반환: branch_id
        """
        # Load original conversation
        # 원본 대화 로드
        original = await self.get_conversation(conversation_id, user)
        if not original:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Create branch ID
        # 분기 ID 생성
        branch_id = f"{conversation_id}:branch:{branch_name}"

        # Copy conversation
        # 대화 복사
        branched = Conversation(
            id=branch_id,
            user=original.user,
            messages=original.messages.copy(),  # Copy all messages
            metadata={
                "branch_from": conversation_id,
                "branch_name": branch_name,
                "created_at": datetime.now().isoformat()
            }
        )

        # Save branch
        # 분기 저장
        await self.update_conversation(branched)

        # Track branch
        # 분기 추적
        if conversation_id not in self.branches:
            self.branches[conversation_id] = []
        self.branches[conversation_id].append(branch_id)

        return branch_id

    async def list_branches(self, conversation_id: str) -> List[str]:
        """
        List all branches of a conversation
        대화의 모든 분기 나열
        """
        return self.branches.get(conversation_id, [])

    async def merge_branch(
        self,
        branch_id: str,
        target_id: str,
        user: User
    ):
        """
        Merge branch back into main conversation
        분기를 메인 대화에 다시 병합
        """
        # Load both conversations
        # 두 대화 모두 로드
        branch = await self.get_conversation(branch_id, user)
        target = await self.get_conversation(target_id, user)

        if not branch or not target:
            raise ValueError("Conversation not found")

        # Find divergence point
        # 분기점 찾기
        original_length = len(target.messages)

        # Append new messages from branch
        # 분기의 새 메시지 추가
        target.messages.extend(branch.messages[original_length:])

        # Save merged conversation
        # 병합된 대화 저장
        await self.update_conversation(target)

# Usage
# 사용
store = BranchingConversationStore()

# Create branch for "what-if" scenario
# "what-if" 시나리오를 위한 분기 생성
branch_id = await store.create_branch(
    conversation_id="conv123",
    branch_name="alternative_analysis",
    user=user
)

# Use branch in agent
# 에이전트에서 분기 사용
async for component in agent.send_message(
    context,
    "What if we exclude outliers?",
    conversation_id=branch_id  # Use branch instead of main
):
    print(component.simple_component.text)

# If satisfied, merge back
# 만족하면 다시 병합
await store.merge_branch(branch_id, "conv123", user)
```

---

**More examples coming soon!**
**더 많은 예제가 곧 제공됩니다!**

For questions or contributions, please visit the GitHub repository.
질문이나 기여는 GitHub 저장소를 방문하세요.

**Happy coding! 즐거운 코딩 되세요!** 🎉
