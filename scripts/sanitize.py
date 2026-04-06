import os
import re

# ───────────────────────────────────────────────
# 설정
# ───────────────────────────────────────────────

TARGET_DIR = "temp_notes/private"


# ───────────────────────────────────────────────
# 유틸리티
# ───────────────────────────────────────────────


def sanitize_url(text: str) -> str:
    """
    Quartz FullSlug 규칙에 맞게 URL을 정제합니다.
    - 앞뒤 슬래시 제거 (FullSlug는 leading/trailing slash 불허)
    - 괄호 제거
    - 공백 → 하이픈
    """
    text = text.strip().strip("/")
    text = text.replace("(", "").replace(")", "")
    text = re.sub(r"\s+", "-", text)
    return text


def extract_permalink(content: str) -> str | None:
    """
    YAML Frontmatter에서 permalink 값을 추출합니다.
    없으면 None 반환.
    """
    match = re.search(r'^permalink:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    if match:
        return sanitize_url(match.group(1))
    return None


# ───────────────────────────────────────────────
# 1단계: 파일명 → permalink 매핑 테이블 구축
# ───────────────────────────────────────────────


def build_mapping(target: str) -> dict[str, str]:
    """
    {파일명(확장자 제외): permalink} 딕셔너리를 만듭니다.
    permalink가 선언된 노트만 포함합니다.
    (없는 노트의 링크는 치환 대상에서 제외 → 원본 유지)
    """
    mapping: dict[str, str] = {}

    for root, _, files in os.walk(target):
        for f in files:
            if not f.endswith(".md"):
                continue

            base_name = os.path.splitext(f)[0]  # 확장자 제거, 문자열
            path = os.path.join(root, f)

            with open(path, "r", encoding="utf-8") as fp:
                content = fp.read()

            permalink = extract_permalink(content)
            if permalink:
                mapping[base_name] = permalink

    print(f"📋 permalink 매핑 완료: {len(mapping)}개 노트")
    return mapping


# ───────────────────────────────────────────────
# 2단계: 위키링크 치환
# ───────────────────────────────────────────────

# Obsidian 위키링크 전체 형식 커버
# [[파일명]]
# [[파일명|표시텍스트]]
# [[폴더/파일명]]
# [[파일명#헤딩]]
# [[폴더/파일명#헤딩|표시텍스트]]
# 이미지 ![[...]] 는 제외
WIKILINK_PATTERN = re.compile(
    r"(?<!\!)"  # 이미지 제외 (앞에 ! 없을 때만)
    r"\[\["
    r"([^|\]#\n]+)"  # group(1): 파일 경로 (폴더/파일명 포함)
    r"(#[^|\]\n]*)?"  # group(2): 헤딩 (#heading, 없을 수도 있음)
    r"(\|[^\]\n]*)?"  # group(3): 표시 텍스트 (|alias, 없을 수도 있음)
    r"\]\]"
)


def replace_wikilinks(content: str, mapping: dict[str, str]) -> str:
    """
    본문의 위키링크를 permalink 기반으로 치환합니다.
    permalink가 없는 노트는 원본 링크를 그대로 유지합니다.
    """

    def replacer(match: re.Match) -> str:
        raw_path = match.group(1).strip()  # 파일 경로 부분
        heading = match.group(2) or ""  # #헤딩
        alias = match.group(3) or ""  # |표시텍스트

        # Obsidian은 파일명(마지막 세그먼트)으로 링크를 해석
        # 전체 경로로도 한 번 더 시도 (폴더/파일명 형태 대비)
        file_name = raw_path.split("/")[-1]
        permalink = mapping.get(file_name) or mapping.get(raw_path)

        if permalink is None:
            # permalink 없는 노트 → 원본 유지
            return match.group(0)

        return f"[[{permalink}{heading}{alias}]]"

    return WIKILINK_PATTERN.sub(replacer, content)


# ───────────────────────────────────────────────
# 3단계: frontmatter permalink 필드 정제
# ───────────────────────────────────────────────

PERMALINK_FIELD_PATTERN = re.compile(r"^(permalink):\s*(.*)", re.MULTILINE)


def sanitize_frontmatter_permalink(content: str) -> str:
    """
    Frontmatter의 permalink 값을 Quartz FullSlug 규칙에 맞게 정제합니다.
    (앞뒤 슬래시·괄호 제거, 공백 → 하이픈)
    """

    def replacer(match: re.Match) -> str:
        value = match.group(2).strip()
        return f"permalink: {sanitize_url(value)}"

    return PERMALINK_FIELD_PATTERN.sub(replacer, content)


# ───────────────────────────────────────────────
# 4단계: 파일명 정제 (물리적 rename)
# ───────────────────────────────────────────────


def rename_files(target: str) -> None:
    """
    파일명에 포함된 괄호·공백을 제거합니다.
    topdown=False로 하위 디렉터리부터 처리합니다.
    """
    for root, _, files in os.walk(target, topdown=False):
        for f in files:
            if not f.endswith(".md"):
                continue

            base, ext = os.path.splitext(f)
            new_base = sanitize_url(base)
            new_name = new_base + ext

            if f == new_name:
                continue

            src = os.path.join(root, f)
            dst = os.path.join(root, new_name)

            try:
                os.rename(src, dst)
                print(f"✅ 파일명 변경: {f} → {new_name}")
            except OSError as e:
                print(f"❌ 변경 실패 ({f}): {e}")


# ───────────────────────────────────────────────
# 메인
# ───────────────────────────────────────────────


def main() -> None:
    if not os.path.exists(TARGET_DIR):
        print(f"⚠️  경로가 없습니다: {TARGET_DIR}")
        return

    print(f"🚀 전처리 시작: {TARGET_DIR}\n")

    # 1. 매핑 테이블 구축
    mapping = build_mapping(TARGET_DIR)

    # 2. 본문 위키링크 + frontmatter permalink 정제
    changed = 0
    for root, _, files in os.walk(TARGET_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue

            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as fp:
                original = fp.read()

            updated = replace_wikilinks(original, mapping)
            updated = sanitize_frontmatter_permalink(updated)

            if original != updated:
                with open(path, "w", encoding="utf-8") as fp:
                    fp.write(updated)
                changed += 1

    print(f"🔗 링크 치환 완료: {changed}개 파일 수정\n")

    # 3. 파일명 물리적 rename
    rename_files(TARGET_DIR)

    print("\n✨ 전처리 완료")


if __name__ == "__main__":
    main()
