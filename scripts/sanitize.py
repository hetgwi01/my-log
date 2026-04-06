import os
import re

# ───────────────────────────────────────────────
# 설정
# ───────────────────────────────────────────────

# Mirroring Sync 이후 content/ 폴더를 대상으로 실행
TARGET_DIR = "content"


# ───────────────────────────────────────────────
# 유틸리티
# ───────────────────────────────────────────────


def sanitize_url(text: str) -> str:
    """
    URL에 쓰일 문자열을 정제합니다.
    - 앞뒤 슬래시 제거
    - 괄호 제거
    - 공백 → 하이픈
    """
    text = text.strip().strip("/")
    text = text.replace("(", "").replace(")", "")
    text = re.sub(r"\s+", "-", text)
    return text


def extract_slug(content: str) -> str | None:
    """
    YAML Frontmatter에서 slug 값을 추출합니다.
    없으면 None 반환.
    """
    match = re.search(r'^slug:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    if match:
        return sanitize_url(match.group(1))
    return None


# ───────────────────────────────────────────────
# 1단계: 파일명 → slug 매핑 테이블 구축
# ───────────────────────────────────────────────


def build_mapping(target: str) -> dict[str, str]:
    """
    {파일명(확장자 제외): slug} 딕셔너리를 만듭니다.

    Mirroring Sync 단계에서 이미 slug 기반으로 파일이 content/에 배치되어 있음.
    slug가 선언된 노트만 포함합니다.

    예시:
      "01_싱글톤(Singleton)" → "cs/design-pattern/creational-pattern/Singleton"
    """
    mapping: dict[str, str] = {}

    for root, _, files in os.walk(target):
        for f in files:
            if not f.endswith(".md"):
                continue

            base_name = os.path.splitext(f)[0]
            path = os.path.join(root, f)

            with open(path, "r", encoding="utf-8") as fp:
                content = fp.read()

            slug = extract_slug(content)
            if slug:
                mapping[base_name] = slug

    print(f"📋 slug 매핑 완료: {len(mapping)}개 노트")
    for name, slug in mapping.items():
        print(f"   {name!r:40s} → {slug}")
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
    r"(?<!\!)"  # 이미지 제외
    r"\[\["
    r"([^|\]#\n]+)"  # group(1): 파일 경로
    r"(#[^|\]\n]*)?"  # group(2): 헤딩
    r"(\|[^\]\n]*)?"  # group(3): 표시 텍스트
    r"\]\]"
)


def replace_wikilinks(content: str, mapping: dict[str, str]) -> str:
    """
    위키링크 타겟을 slug 값(= content/ 내 실제 경로)으로 치환합니다.
    slug 없는 노트는 원본 유지.

    예시:
      [[01_싱글톤(Singleton)|Singleton]]
      → [[cs/design-pattern/creational-pattern/Singleton|Singleton]]
    """

    def replacer(match: re.Match) -> str:
        raw_path = match.group(1).strip()
        heading = match.group(2) or ""
        alias = match.group(3) or ""

        # Obsidian은 파일명(마지막 세그먼트)으로 링크를 해석
        file_name = raw_path.split("/")[-1]
        slug = mapping.get(file_name) or mapping.get(raw_path)

        if slug is None:
            return match.group(0)  # slug 없으면 원본 유지

        return f"[[{slug}{heading}{alias}]]"

    return WIKILINK_PATTERN.sub(replacer, content)


# ───────────────────────────────────────────────
# 메인
# ───────────────────────────────────────────────


def main() -> None:
    if not os.path.exists(TARGET_DIR):
        print(f"⚠️  경로가 없습니다: {TARGET_DIR}")
        return

    print(f"🚀 링크 치환 시작: {TARGET_DIR}\n")

    # 1. 파일명 → slug 매핑 테이블 구축
    mapping = build_mapping(TARGET_DIR)
    print()

    # 2. 위키링크 치환
    changed = 0
    for root, _, files in os.walk(TARGET_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue

            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as fp:
                original = fp.read()

            updated = replace_wikilinks(original, mapping)

            if original != updated:
                with open(path, "w", encoding="utf-8") as fp:
                    fp.write(updated)
                changed += 1

    print(f"🔗 링크 치환 완료: {changed}개 파일 수정")
    print("\n✨ 전처리 완료")


if __name__ == "__main__":
    main()
