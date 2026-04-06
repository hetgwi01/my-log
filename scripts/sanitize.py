import os
import re


def sanitize_url(text):
    """URL 주소로 쓰일 부분에서 괄호와 공백을 제거합니다."""
    if isinstance(text, tuple):
        text = text
    if not text:
        return ""
    # 문자열로 변환 후 괄호 및 공백 제거
    return str(text).replace("(", "").replace(")", "").replace(" ", "-")


def get_slug_from_content(content):
    """YAML Frontmatter에서 slug 값을 추출합니다."""
    match = re.search(r'^slug:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    if match:
        return match.group(1).strip().lstrip("/")
    return None


def final_run():
    """파일명과 링크를 슬러그 기반으로 매핑하고 정제하는 메인 함수"""
    target = "temp_notes/private"
    if not os.path.exists(target):
        print(f"⚠️ {target} 경로가 없습니다.")
        return

    print(f"🚀 {target} 전처리를 시작합니다. (Link-to-Slug 매핑 모드)")

    # 1. 파일명 -> 슬러그 매핑 생성
    # Quartz가 링크를 해석할 때 사용할 지도를 만듭니다.
    mapping = {}
    for root, dirs, files in os.walk(target):
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8") as file:
                    c = file.read()

                # os.path.splitext(f)을 사용하여 튜플이 아닌 파일명(문자열)만 추출
                base_name = os.path.splitext(f)
                slug = get_slug_from_content(c)

                # 슬러그가 있으면 정제된 슬러그를, 없으면 정제된 파일명을 밸류로 사용
                mapping[base_name] = (
                    sanitize_url(slug) if slug else sanitize_url(base_name)
                )

    # 2. 본문 내 위키링크 및 메타데이터 치환
    for root, dirs, files in os.walk(target):
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8") as file:
                    content = file.read()

                # [핵심] 위키링크 [[타겟]] -> [[슬러그|원본텍스트]]로 교체
                # 이미지(![[ ]])는 건드리지 않도록 부정형 전방탐색(?<!\!) 사용
                def replace_logic(match):
                    target_name = match.group(1).strip()
                    display_part = (
                        match.group(2) if match.group(2) else f"|{target_name}"
                    )

                    # 매핑 테이블에 있으면 슬러그로, 없으면 기본 정제된 이름으로 연결
                    final_link = mapping.get(target_name, sanitize_url(target_name))
                    return f"[[{final_link}{display_part}]]"

                new_content = re.sub(
                    r"(?<!\!)\[\[([^|\]]+)(\|[^\]]+)?\]\]", replace_logic, content
                )

                # Frontmatter의 slug와 aliases 필드도 404 방지를 위해 정제
                def sanitize_field(match):
                    field_name = match.group(1)
                    field_value = match.group(2).strip()
                    return f"{field_name}: {sanitize_url(field_value)}"

                new_content = re.sub(
                    r"^(slug|aliases):\s*(.*)",
                    sanitize_field,
                    new_content,
                    flags=re.MULTILINE,
                )

                if content != new_content:
                    with open(p, "w", encoding="utf-8") as file:
                        file.write(new_content)

    # 3. 물리적 파일명 변경 (정제된 링크가 찾아올 수 있도록)
    for root, dirs, files in os.walk(target, topdown=False):
        for f in files:
            if f.endswith(".md"):
                # 튜플 에러 방지를 위해 인덱스 사용
                old_base, ext = os.path.splitext(f)
                new_base = sanitize_url(old_base)
                new_name = new_base + ext

                if f != new_name:
                    try:
                        os.rename(os.path.join(root, f), os.path.join(root, new_name))
                        print(f"✅ 파일명 변경: {f} -> {new_name}")
                    except OSError as e:
                        print(f"❌ 변경 실패: {e}")


if __name__ == "__main__":
    final_run()
