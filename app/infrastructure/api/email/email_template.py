from app.domains.recommendation.service.dto.response.get_course_detail_response_dto import (
    GetCourseDetailResponseDto,
)
from app.infrastructure.config.config import settings


def build_course_email(dto: GetCourseDetailResponseDto) -> tuple[str, str, str]:
    """Returns (subject, html_body, text_body)."""
    representative_name = dto.places[0].name if dto.places else dto.area
    subject = f"[{settings.SERVICE_NAME}] {representative_name} 데이트 코스 추천"

    place_rows_html = ""
    place_rows_text = ""
    for p in dto.places:
        move_str = f"{p.move_time_to_next_minutes}분 이동" if p.move_time_to_next_minutes else ""
        place_rows_html += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee;">
            <strong>{p.order}. [{p.place_type.upper()}] {p.name}</strong><br>
            <span style="color:#666;">{p.category}</span><br>
            {p.road_address}<br>
            {p.start_time} ~ {p.end_time} ({p.duration_minutes}분)<br>
            <em>{p.short_description}</em>
          </td>
        </tr>
        {"<tr><td style='padding:4px;color:#999;text-align:center;'>↓ " + move_str + "</td></tr>" if move_str else ""}
        """
        place_rows_text += (
            f"{p.order}. [{p.place_type.upper()}] {p.name}\n"
            f"   {p.category} | {p.road_address}\n"
            f"   {p.start_time} ~ {p.end_time} ({p.duration_minutes}분)\n"
            f"   {p.short_description}\n"
            + (f"   ↓ {move_str}\n" if move_str else "")
            + "\n"
        )

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <h2 style="color:#333;">{dto.title}</h2>
      <p style="color:#555;">{dto.description}</p>
      <p>
        <strong>지역:</strong> {dto.area} &nbsp;|&nbsp;
        <strong>출발:</strong> {dto.start_time} &nbsp;|&nbsp;
        <strong>이동수단:</strong> {dto.transport} &nbsp;|&nbsp;
        <strong>예상 소요:</strong> {dto.estimated_duration_minutes}분
      </p>
      <h3 style="color:#444;">코스 일정</h3>
      <table style="width:100%;border-collapse:collapse;">
        {place_rows_html}
      </table>
      <hr>
      <p style="color:#999;font-size:12px;">본 메일은 {settings.SERVICE_NAME} 서비스에서 발송되었습니다.</p>
    </body></html>
    """

    text = (
        f"{dto.title}\n"
        f"{dto.description}\n\n"
        f"지역: {dto.area} | 출발: {dto.start_time} | 이동수단: {dto.transport} | 예상 소요: {dto.estimated_duration_minutes}분\n\n"
        f"코스 일정\n{'=' * 40}\n"
        f"{place_rows_text}"
        f"\n본 메일은 {settings.SERVICE_NAME} 서비스에서 발송되었습니다."
    )

    return subject, html, text
