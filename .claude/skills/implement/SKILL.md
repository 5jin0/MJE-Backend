---
name: implement
description: Behavior Backlog를 기반으로 실제 동작하는 코드를 구현한다
---

Behavior Backlog를 기반으로 실제 동작하는 코드를 구현한다.

## 입력

$ARGUMENTS

---

## 구현 절차

1. 위 Backlog의 **Title**을 읽고 구현 목표를 파악한다
2. **Success Criteria**를 분석하여 완료 기준을 명확히 한다
3. **Todo** 항목을 기반으로 구현 범위를 결정한다
4. CLAUDE.MD의 아키텍처 원칙을 반드시 준수하여 코드를 생성한다

---

## 아키텍처 준수 규칙

- 프로젝트는 FastAPI + DDD Layered Architecture를 따른다
- 도메인: home / recommendation / courses
- 계층 의존성: Controller → Service → Domain / Service → Repository Interface
- Domain은 순수 Python (FastAPI, SQLAlchemy, Pydantic, Redis 사용 금지)
- Controller는 Form만 사용, Service는 DTO만 사용
- 이벤트는 각 도메인의 domain/events에 정의
- export_logs는 infrastructure/api/export_logs에 위치

---

## 출력 형식

### Project Structure

구현에 필요한 파일 목록 (경로 포함)

### Implementation

각 파일의 실제 구현 코드 (실행 가능한 완성 코드)

### Explanation

- 각 계층의 역할 설명
- 핵심 설계 결정 사항
- 실행 방법 (필요 시)
