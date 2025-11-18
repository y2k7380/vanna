"""
Tool registry for the Vanna Agents framework.
Vanna Agents 프레임워크를 위한 도구 레지스트리

This module provides the ToolRegistry class for managing and executing tools.
이 모듈은 도구를 관리하고 실행하기 위한 ToolRegistry 클래스를 제공합니다.

The ToolRegistry is responsible for:
ToolRegistry는 다음을 담당합니다:

1. Tool Registration - Adding tools and configuring their access groups
   도구 등록 - 도구를 추가하고 접근 그룹 설정

2. Permission Checking - Validating user access to tools based on groups
   권한 확인 - 그룹 기반으로 사용자의 도구 접근 권한 검증

3. Argument Validation - Using Pydantic to validate tool arguments
   인자 검증 - Pydantic을 사용하여 도구 인자 검증

4. Argument Transformation - Applying user-specific transformations (e.g., RLS)
   인자 변환 - 사용자별 변환 적용 (예: Row Level Security)

5. Tool Execution - Running the tool and returning results
   도구 실행 - 도구를 실행하고 결과 반환

6. Audit Logging - Recording tool access and invocations for compliance
   감사 로깅 - 컴플라이언스를 위한 도구 접근 및 호출 기록
"""

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar, Union

from .tool import Tool, ToolCall, ToolContext, ToolRejection, ToolResult, ToolSchema
from .user import User

if TYPE_CHECKING:
    from .audit import AuditLogger
    from .agent.config import AuditConfig

T = TypeVar("T")


class _LocalToolWrapper(Tool[T]):
    """Wrapper for tools with configurable access groups.

    접근 그룹 설정이 가능한 도구 래퍼

    This internal class wraps a tool to override its access_groups property.
    It's used when registering tools with custom access restrictions via
    register_local_tool().

    이 내부 클래스는 도구를 래핑하여 access_groups 속성을 오버라이드합니다.
    register_local_tool()을 통해 사용자 정의 접근 제한이 있는
    도구를 등록할 때 사용됩니다.
    """

    def __init__(self, wrapped_tool: Tool[T], access_groups: List[str]):
        self._wrapped_tool = wrapped_tool
        self._access_groups = access_groups

    @property
    def name(self) -> str:
        return self._wrapped_tool.name

    @property
    def description(self) -> str:
        return self._wrapped_tool.description

    @property
    def access_groups(self) -> List[str]:
        return self._access_groups

    def get_args_schema(self) -> Type[T]:
        return self._wrapped_tool.get_args_schema()

    async def execute(self, context: ToolContext, args: T) -> ToolResult:
        return await self._wrapped_tool.execute(context, args)


class ToolRegistry:
    """Registry for managing tools.

    도구 관리를 위한 레지스트리

    The ToolRegistry is the central place where all tools are registered
    and managed. It handles:
    - Storing tools by name
    - Validating user permissions before execution
    - Validating and transforming tool arguments
    - Executing tools with proper error handling
    - Audit logging of all tool activities

    ToolRegistry는 모든 도구가 등록되고 관리되는 중심 장소입니다.
    다음을 처리합니다:
    - 이름별로 도구 저장
    - 실행 전 사용자 권한 검증
    - 도구 인자 검증 및 변환
    - 적절한 에러 처리를 통한 도구 실행
    - 모든 도구 활동의 감사 로깅

    Example:
    예제:
        registry = ToolRegistry()
        registry.register_local_tool(
            tool=RunSqlTool(db_connection),
            access_groups=["data_analyst", "admin"]
        )
    """

    def __init__(
        self,
        audit_logger: Optional["AuditLogger"] = None,
        audit_config: Optional["AuditConfig"] = None,
    ) -> None:
        # Dictionary mapping tool names to Tool instances
        # 도구 이름을 Tool 인스턴스에 매핑하는 딕셔너리
        self._tools: Dict[str, Tool[Any]] = {}

        # Optional audit logger for compliance tracking
        # 컴플라이언스 추적을 위한 선택적 감사 로거
        self.audit_logger = audit_logger

        # Configuration for audit logging behavior
        # 감사 로깅 동작을 위한 설정
        if audit_config is not None:
            self.audit_config = audit_config
        else:
            from .agent.config import AuditConfig

            self.audit_config = AuditConfig()

    def register_local_tool(self, tool: Tool[Any], access_groups: List[str]) -> None:
        """Register a local tool with optional access group restrictions.

        접근 그룹 제한이 있는 로컬 도구 등록

        This method adds a tool to the registry. If access_groups are specified,
        only users belonging to at least one of those groups can use the tool.

        이 메서드는 레지스트리에 도구를 추가합니다. access_groups가 지정되면,
        해당 그룹 중 최소 하나에 속한 사용자만 도구를 사용할 수 있습니다.

        Args:
            tool: The tool to register
                  등록할 도구
            access_groups: List of groups that can access this tool.
                          If None or empty, tool is accessible to all users.
                          이 도구에 접근 가능한 그룹 목록.
                          None이거나 비어있으면 모든 사용자가 접근 가능.

        Raises:
            ValueError: If a tool with this name is already registered
                       이 이름의 도구가 이미 등록되어 있는 경우

        Example:
        예제:
            # Register a tool only for admins
            # 관리자만 사용할 수 있는 도구 등록
            registry.register_local_tool(
                tool=DeleteDataTool(),
                access_groups=["admin"]
            )

            # Register a tool accessible to all users
            # 모든 사용자가 접근 가능한 도구 등록
            registry.register_local_tool(
                tool=CalculatorTool(),
                access_groups=[]
            )
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")

        if access_groups:
            # Wrap the tool to override its access groups
            # 도구를 래핑하여 접근 그룹 오버라이드
            wrapped_tool = _LocalToolWrapper(tool, access_groups)
            self._tools[tool.name] = wrapped_tool
        else:
            # No access restrictions, register as-is
            # 접근 제한 없음, 그대로 등록
            self._tools[tool.name] = tool

    async def get_tool(self, name: str) -> Optional[Tool[Any]]:
        """Get a tool by name."""
        return self._tools.get(name)

    async def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    async def get_schemas(self, user: Optional[User] = None) -> List[ToolSchema]:
        """Get schemas for all tools accessible to user."""
        schemas = []
        for tool in self._tools.values():
            if user is None or await self._validate_tool_permissions(tool, user):
                schemas.append(tool.get_schema())
        return schemas

    async def _validate_tool_permissions(self, tool: Tool[Any], user: User) -> bool:
        """Validate if user has access to tool based on group membership.

        그룹 멤버십 기반으로 사용자의 도구 접근 권한 검증

        Checks for intersection between user's group memberships and tool's access groups.
        If tool has no access groups specified, it's accessible to all users.

        사용자의 그룹 멤버십과 도구의 접근 그룹 간의 교집합을 확인합니다.
        도구에 접근 그룹이 지정되지 않은 경우 모든 사용자가 접근 가능합니다.

        Permission logic:
        권한 로직:
        - If tool.access_groups is empty → grant access to everyone
          tool.access_groups가 비어있으면 → 모든 사람에게 접근 허용
        - If user belongs to ANY group in tool.access_groups → grant access
          사용자가 tool.access_groups의 어떤 그룹이든 속하면 → 접근 허용
        - Otherwise → deny access
          그 외 → 접근 거부

        Example:
        예제:
            # Tool requires "admin" or "analyst" groups
            # 도구가 "admin" 또는 "analyst" 그룹 필요
            tool.access_groups = ["admin", "analyst"]

            # User in admin group → access granted
            # admin 그룹의 사용자 → 접근 허용
            user.group_memberships = ["admin", "viewer"]  # ✓

            # User in analyst group → access granted
            # analyst 그룹의 사용자 → 접근 허용
            user.group_memberships = ["analyst"]  # ✓

            # User with no matching groups → access denied
            # 일치하는 그룹이 없는 사용자 → 접근 거부
            user.group_memberships = ["viewer"]  # ✗
        """
        tool_access_groups = tool.access_groups

        # No restrictions if tool has no access groups
        # 도구에 접근 그룹이 없으면 제한 없음
        if not tool_access_groups:
            return True

        # Convert both to sets for efficient intersection check
        # 효율적인 교집합 확인을 위해 둘 다 집합으로 변환
        user_groups = set(user.group_memberships)
        tool_groups = set(tool_access_groups)

        # Grant access if any group in user.group_memberships exists in tool.access_groups
        # user.group_memberships의 어떤 그룹이든 tool.access_groups에 존재하면 접근 허용
        # The & operator finds the intersection of two sets
        # & 연산자는 두 집합의 교집합을 찾습니다
        return bool(user_groups & tool_groups)

    async def transform_args(
        self,
        tool: Tool[T],
        args: T,
        user: User,
        context: ToolContext,
    ) -> Union[T, ToolRejection]:
        """Transform and validate tool arguments based on user context.

        사용자 컨텍스트 기반으로 도구 인자 변환 및 검증

        This method allows per-user transformation of tool arguments, such as:
        이 메서드는 다음과 같은 사용자별 도구 인자 변환을 허용합니다:

        - Applying row-level security (RLS) to SQL queries
          SQL 쿼리에 행 레벨 보안(RLS) 적용
        - Filtering available options based on user permissions
          사용자 권한에 따라 사용 가능한 옵션 필터링
        - Validating required arguments are present
          필수 인자가 있는지 검증
        - Redacting sensitive fields
          민감한 필드 삭제

        The default implementation performs no transformation (NoOp).
        Subclasses can override this method to implement custom transformation logic.

        기본 구현은 변환을 수행하지 않습니다 (NoOp).
        서브클래스는 이 메서드를 오버라이드하여 사용자 정의 변환 로직을 구현할 수 있습니다.

        Example override for Row-Level Security:
        행 레벨 보안을 위한 오버라이드 예제:

            class SecureToolRegistry(ToolRegistry):
                async def transform_args(self, tool, args, user, context):
                    if tool.name == "run_sql":
                        # Add WHERE clause to restrict data access
                        # 데이터 접근 제한을 위해 WHERE 절 추가
                        if "region" not in user.attributes:
                            return ToolRejection(
                                reason="User must have a region assigned"
                            )
                        original_sql = args.sql
                        args.sql = f"{original_sql} WHERE region = '{user.attributes['region']}'"
                    return args

        Args:
            tool: The tool being executed
                  실행 중인 도구
            args: Already Pydantic-validated arguments
                  이미 Pydantic으로 검증된 인자
            user: The user executing the tool
                  도구를 실행하는 사용자
            context: Full execution context
                    전체 실행 컨텍스트

        Returns:
            Either:
            반환값:
            - Transformed arguments (may be unchanged if no transformation needed)
              변환된 인자 (변환이 필요 없으면 변경되지 않을 수 있음)
            - ToolRejection with explanation of why args were rejected
              인자가 거부된 이유에 대한 설명과 함께 ToolRejection
        """
        # Default: no transformation (NoOp)
        # 기본값: 변환 없음 (NoOp)
        return args

    async def execute(
        self,
        tool_call: ToolCall,
        context: ToolContext,
    ) -> ToolResult:
        """Execute a tool call with validation.

        검증을 통한 도구 호출 실행

        This is the main entry point for tool execution. It performs a complete
        execution pipeline:
        이것은 도구 실행의 주요 진입점입니다. 완전한 실행 파이프라인을 수행합니다:

        1. Tool lookup - Find the tool by name
           도구 조회 - 이름으로 도구 찾기
        2. Permission check - Verify user has access
           권한 확인 - 사용자가 접근 권한을 가지고 있는지 검증
        3. Argument validation - Validate args with Pydantic
           인자 검증 - Pydantic으로 인자 검증
        4. Argument transformation - Apply user-specific transformations
           인자 변환 - 사용자별 변환 적용
        5. Audit logging - Record the invocation
           감사 로깅 - 호출 기록
        6. Execution - Run the tool
           실행 - 도구 실행
        7. Result logging - Record the result
           결과 로깅 - 결과 기록

        Args:
            tool_call: The LLM's tool call request (name + arguments)
                      LLM의 도구 호출 요청 (이름 + 인자)
            context: Execution context with user, conversation_id, etc.
                    사용자, conversation_id 등을 포함한 실행 컨텍스트

        Returns:
            ToolResult with success status, result text, and optional UI component
            성공 상태, 결과 텍스트, 선택적 UI 컴포넌트를 포함한 ToolResult
        """
        # Step 1: Look up the tool
        # 1단계: 도구 조회
        tool = await self.get_tool(tool_call.name)
        if not tool:
            msg = f"Tool '{tool_call.name}' not found"
            return ToolResult(
                success=False,
                result_for_llm=msg,
                ui_component=None,
                error=msg,
            )

        # Step 2: Validate user has permission to use this tool
        # 2단계: 사용자가 이 도구를 사용할 권한이 있는지 검증
        if not await self._validate_tool_permissions(tool, context.user):
            msg = f"Insufficient group access for tool '{tool_call.name}'"

            # Log the access denial for security auditing
            # 보안 감사를 위해 접근 거부 기록
            if (
                self.audit_logger
                and self.audit_config
                and self.audit_config.log_tool_access_checks
            ):
                await self.audit_logger.log_tool_access_check(
                    user=context.user,
                    tool_name=tool_call.name,
                    access_granted=False,
                    required_groups=tool.access_groups,
                    context=context,
                    reason=msg,
                )

            return ToolResult(
                success=False,
                result_for_llm=msg,
                ui_component=None,
                error=msg,
            )

        # Step 3: Validate and parse arguments using Pydantic
        # 3단계: Pydantic을 사용하여 인자 검증 및 파싱
        try:
            # Get the Pydantic model that defines expected arguments
            # 예상되는 인자를 정의하는 Pydantic 모델 가져오기
            args_model = tool.get_args_schema()

            # Validate the LLM's arguments against the schema
            # LLM의 인자를 스키마에 대해 검증
            # This will raise an exception if args don't match the schema
            # 인자가 스키마와 일치하지 않으면 예외를 발생시킵니다
            validated_args = args_model.model_validate(tool_call.arguments)
        except Exception as e:
            msg = f"Invalid arguments: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=msg,
                ui_component=None,
                error=msg,
            )

        # Step 4: Transform/validate arguments based on user context
        # 4단계: 사용자 컨텍스트 기반 인자 변환/검증
        # This allows applying user-specific rules like Row-Level Security
        # 이를 통해 행 레벨 보안과 같은 사용자별 규칙을 적용할 수 있습니다
        transform_result = await self.transform_args(
            tool=tool,
            args=validated_args,
            user=context.user,
            context=context,
        )

        # Check if transformation rejected the arguments
        # 변환이 인자를 거부했는지 확인
        if isinstance(transform_result, ToolRejection):
            return ToolResult(
                success=False,
                result_for_llm=transform_result.reason,
                ui_component=None,
                error=transform_result.reason,
            )

        # Use transformed arguments for execution
        # 실행을 위해 변환된 인자 사용
        final_args = transform_result

        # Step 5a: Audit successful access check
        # 5a단계: 성공적인 접근 확인 감사
        if (
            self.audit_logger
            and self.audit_config
            and self.audit_config.log_tool_access_checks
        ):
            await self.audit_logger.log_tool_access_check(
                user=context.user,
                tool_name=tool_call.name,
                access_granted=True,
                required_groups=tool.access_groups,
                context=context,
            )

        # Step 5b: Audit tool invocation
        # 5b단계: 도구 호출 감사
        # Record that this tool was called, who called it, and with what arguments
        # 이 도구가 호출되었음을 기록하고, 누가 호출했으며, 어떤 인자로 호출했는지 기록
        if (
            self.audit_logger
            and self.audit_config
            and self.audit_config.log_tool_invocations
        ):
            # Get UI features if available from context
            # 컨텍스트에서 사용 가능한 경우 UI 기능 가져오기
            ui_features = context.metadata.get("ui_features_available", [])
            await self.audit_logger.log_tool_invocation(
                user=context.user,
                tool_call=tool_call,
                ui_features=ui_features,
                context=context,
                sanitize_parameters=self.audit_config.sanitize_tool_parameters,
            )

        # Step 6: Execute the tool
        # 6단계: 도구 실행
        try:
            # Measure execution time for performance monitoring
            # 성능 모니터링을 위한 실행 시간 측정
            start_time = time.perf_counter()

            # Call the tool's execute method with the validated/transformed args
            # 검증/변환된 인자로 도구의 execute 메서드 호출
            result = await tool.execute(context, final_args)

            # Calculate how long the tool took to execute
            # 도구 실행에 걸린 시간 계산
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Add execution time to metadata for observability
            # 관찰성을 위해 메타데이터에 실행 시간 추가
            result.metadata["execution_time_ms"] = execution_time_ms

            # Step 7: Audit tool result
            # 7단계: 도구 결과 감사
            # Record what the tool returned (success/failure, result data)
            # 도구가 무엇을 반환했는지 기록 (성공/실패, 결과 데이터)
            if (
                self.audit_logger
                and self.audit_config
                and self.audit_config.log_tool_results
            ):
                await self.audit_logger.log_tool_result(
                    user=context.user,
                    tool_call=tool_call,
                    result=result,
                    context=context,
                )

            return result

        except Exception as e:
            # Handle unexpected errors during tool execution
            # 도구 실행 중 예기치 않은 에러 처리
            msg = f"Execution failed: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=msg,
                ui_component=None,
                error=msg,
            )
