"""
Tool domain interface.
도구(Tool) 도메인 인터페이스

This module contains the abstract base class for tools.
이 모듈은 도구의 추상 베이스 클래스를 포함합니다.

Tools are the primary way for the LLM to interact with external systems.
Each tool defines:
- A name and description that the LLM sees
- A Pydantic schema for argument validation
- An execute method that performs the actual work
- Optional access control via groups

도구는 LLM이 외부 시스템과 상호작용하는 주요 방법입니다.
각 도구는 다음을 정의합니다:
- LLM이 보는 이름과 설명
- 인자 검증을 위한 Pydantic 스키마
- 실제 작업을 수행하는 execute 메서드
- 그룹을 통한 선택적 접근 제어
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Type, TypeVar

from .models import ToolContext, ToolResult, ToolSchema

# Type variable for tool argument types
# This allows each tool to define its own argument type
# 도구 인자 타입을 위한 타입 변수
# 각 도구가 자신만의 인자 타입을 정의할 수 있게 합니다
T = TypeVar("T")


class Tool(ABC, Generic[T]):
    """Abstract base class for tools.

    도구의 추상 베이스 클래스

    Example implementation:
    예제 구현:

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
                return "Performs basic math operations"

            def get_args_schema(self) -> Type[CalculatorArgs]:
                return CalculatorArgs

            async def execute(self, context: ToolContext, args: CalculatorArgs) -> ToolResult:
                if args.operation == "add":
                    result = args.a + args.b
                    return ToolResult(
                        success=True,
                        result_for_llm=f"Result: {result}"
                    )
                # ... handle other operations
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this tool.

        고유한 도구 이름

        This is how the LLM will refer to the tool in its tool calls.
        Must be unique across all registered tools.
        Use lowercase with underscores (e.g., "run_sql", "search_files")

        LLM이 도구 호출 시 사용할 이름입니다.
        등록된 모든 도구 중에서 고유해야 합니다.
        소문자와 언더스코어 사용 권장 (예: "run_sql", "search_files")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does.

        도구가 무엇을 하는지 설명

        This description is shown to the LLM to help it understand when to use the tool.
        Be clear and specific about:
        - What the tool does
        - When to use it
        - What kind of results it returns

        이 설명은 LLM이 도구를 언제 사용할지 이해하도록 돕습니다.
        다음을 명확하고 구체적으로 작성하세요:
        - 도구가 무엇을 하는지
        - 언제 사용하는지
        - 어떤 종류의 결과를 반환하는지
        """
        pass

    @property
    def access_groups(self) -> List[str]:
        """Groups permitted to access this tool.

        이 도구에 접근 가능한 그룹

        Returns empty list by default (accessible to all users).
        Override this to restrict access to specific user groups.

        기본적으로 빈 리스트를 반환합니다 (모든 사용자가 접근 가능).
        특정 사용자 그룹으로 접근을 제한하려면 이 메서드를 오버라이드하세요.

        Example:
        예제:
            return ["admin", "data_analyst"]  # Only admin and data_analyst groups can use this tool
        """
        return []

    @abstractmethod
    def get_args_schema(self) -> Type[T]:
        """Return the Pydantic model for arguments.

        인자를 위한 Pydantic 모델 반환

        The returned class should be a Pydantic BaseModel that defines
        all the arguments this tool accepts. This schema is:
        1. Sent to the LLM so it knows what arguments to provide
        2. Used to validate arguments before execution

        반환된 클래스는 이 도구가 받는 모든 인자를 정의하는
        Pydantic BaseModel이어야 합니다. 이 스키마는:
        1. LLM에게 전달되어 어떤 인자를 제공해야 하는지 알려줌
        2. 실행 전 인자 검증에 사용됨
        """
        pass

    @abstractmethod
    async def execute(self, context: ToolContext, args: T) -> ToolResult:
        """Execute the tool with validated arguments.

        검증된 인자로 도구 실행

        This is the main method that performs the tool's work.
        It receives:
        - context: Contains user info, conversation_id, request_id, agent_memory, etc.
        - args: Already validated against the Pydantic schema

        Returns a ToolResult with:
        - success: Whether the operation succeeded
        - result_for_llm: Text description of the result (LLM will read this)
        - ui_component: Optional rich UI component to show the user
        - error: Error message if success=False

        이것은 도구의 작업을 수행하는 메인 메서드입니다.
        받는 것:
        - context: 사용자 정보, conversation_id, request_id, agent_memory 등 포함
        - args: Pydantic 스키마로 이미 검증됨

        반환하는 ToolResult:
        - success: 작업 성공 여부
        - result_for_llm: 결과에 대한 텍스트 설명 (LLM이 읽음)
        - ui_component: 사용자에게 보여줄 선택적 리치 UI 컴포넌트
        - error: success=False일 때 에러 메시지

        Args:
            context: Execution context containing user, conversation_id, and request_id
            args: Validated tool arguments

        Returns:
            ToolResult with success status, result for LLM, and optional UI component
        """
        pass

    def get_schema(self) -> ToolSchema:
        """Generate tool schema for LLM.

        LLM을 위한 도구 스키마 생성

        This method is called automatically by the framework to create
        the JSON schema that's sent to the LLM. You usually don't need
        to override this method.

        The schema includes:
        - Tool name and description
        - JSON schema of the arguments (from Pydantic model)
        - Access groups for permission checks

        이 메서드는 프레임워크에 의해 자동으로 호출되어
        LLM에게 전송될 JSON 스키마를 생성합니다.
        일반적으로 이 메서드를 오버라이드할 필요는 없습니다.

        스키마에 포함되는 것:
        - 도구 이름과 설명
        - 인자의 JSON 스키마 (Pydantic 모델에서 생성)
        - 권한 확인을 위한 접근 그룹
        """
        from typing import Any, cast

        # Get the Pydantic model class for this tool's arguments
        # 이 도구의 인자를 위한 Pydantic 모델 클래스 가져오기
        args_model = self.get_args_schema()

        # Convert Pydantic model to JSON schema format
        # Pydantic 모델을 JSON 스키마 형식으로 변환
        # This schema tells the LLM what arguments it can provide
        # 이 스키마는 LLM에게 어떤 인자를 제공할 수 있는지 알려줌
        schema = (
            cast(Any, args_model).model_json_schema()
            if hasattr(args_model, "model_json_schema")
            else {}
        )

        # Build the complete tool schema
        # 완전한 도구 스키마 구성
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=schema,
            access_groups=self.access_groups,
        )
