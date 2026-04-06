import os
import re


def sanitize_url(text):
    if not text:
        return ""
    # URL 주소로 쓰일 부분에서 괄호와 공백을 제거합니다.
    return text.replace("(", "").replace(")", "").replace(" ", "-")


def get_slug_from_content(content):
    # YAML Frontmatter에서 slug 값을 추출합니다.
    match = re.search(r'^slug:\s*["\']?([^"\'\n]+)["\']?', content, re.MULTILINE)
    if match:
        return match.group(1).strip().lstrip("/")
    return None


def run_sanitization(target_path):
    if not os.path.exists(target_path):
        print(f"⚠️ {target_path} 경로가 없습니다.")
        return

    print(f"🚀 {target_path} 전처리를 시작합니다. (Link-to-Slug 매핑 모드)")

    slug_map = {}  # {원래파일명: 정제된슬러그}

    # Step 1: 모든 파일의 Slug 주소를 수집하여 지도를 만듭니다.
    for root, dirs, files in os.walk(target_path):
        for file_name in files:
            if file_name.endswith(".md"):
                path = os.path.join(root, file_name)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                base_name = os.path.splitext(file_name)
                slug = get_slug_from_content(content)

                if slug:
                    # 슬러그가 있으면 정제해서 저장
                    slug_map[base_name] = sanitize_url(slug)
                else:
                    # 슬러그가 없으면 상대 경로를 슬러그로 간주
                    rel_path = os.path.relpath(path, target_path)
                    slug_map[base_name] = sanitize_url(
                        os.path.splitext(rel_path).replace("\\", "/")
                    )

    # Step 2: 수집된 지도를 바탕으로 본문의 링크를 수정합니다.
    for root, dirs, files in os.walk(target_path):
        for file_name in files:
            if file_name.endswith(".md"):
                path = os.path.join(root, file_name)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # [핵심] 위키링크 [[타겟]] -> [[슬러그|타겟]] 으로 치환
                def replace_link_with_slug(match):
                    target = match.group(1).strip()
                    display = match.group(2) if match.group(2) else f"|{target}"

                    # 지도가 있으면 슬러그로, 없으면 기존 타겟 정제해서 사용
                    final_target = slug_map.get(target, sanitize_url(target))
                    return f"[[{final_target}{display}]]"

                # 이미지(![[ ]])는 제외하고 일반 링크만 처리
                new_content = re.sub(
                    r"(?<!\!)\[\[([^|\]]+)(\|[^\]]+)?\]\]", replace_wikilink, content
                )  # 아래 정규식 함수 사용

                # [B] Frontmatter 내의 slug/aliases도 정제 (404 방지)
                new_content = re.sub(
                    r"^(slug|aliases):\s*(.*)",
                    lambda m: f"{m.group(1)}: {sanitize_url(m.group(2).strip())}",
                    new_content,
                    flags=re.MULTILINE,
                )

                if content != new_content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)

    # Step 3: 물리적 파일명 변경 (정제된 슬러그가 찾아올 수 있게)
    for root, dirs, files in os.walk(target_path, topdown=False):
        for name in files:
            if name.endswith(".md"):
                base, ext = os.path.splitext(name)
                new_name = sanitize_url(base) + ext
                if name != new_name:
                    try:
                        os.rename(
                            os.path.join(root, name), os.path.join(root, new_name)
                        )
                    except OSError:
                        pass


def replace_wikilink(match):
    # 위에서 정의한 로직을 정규식 매치 함수로 분리
    # (본 로직은 편의를 위해 여기에 작성하나 실제 실행 시 위와 통합됩니다)
    pass


# 실제 실행용 정제 함수 (위의 로직을 더 견고하게 다듬은 버전)
def final_run():
    target = "temp_notes/private"
    if not os.path.exists(target):
        return

    # 1. 맵 생성
    mapping = {}
    for r, d, fs in os.walk(target):
        for f in fs:
            if f.endswith(".md"):
                p = os.path.join(r, f)
                with open(p, "r", encoding="utf-8") as file:
                    c = file.read()
                bn = os.path.splitext(f)
                s = get_slug_from_content(c)
                mapping[bn] = sanitize_url(s) if s else sanitize_url(bn)

    # 2. 링크 치환
    for r, d, fs in os.walk(target):
        for f in fs:
            if f.endswith(".md"):
                p = os.path.join(r, f)
                with open(p, "r", encoding="utf-8") as file:
                    c = file.read()

                # 링크 타겟을 맵에 있는 슬러그로 교체
                nc = re.sub(
                    r"(?<!\!)\[\[([^|\]]+)(\|[^\]]+)?\]\]",
                    lambda m: (
                        f"[[{mapping.get(m.group(1).strip(), sanitize_url(m.group(1).strip()))}{m.group(2) if m.group(2) else '|' + m.group(1).strip()}]]"
                    ),
                    c,
                )

                # slug, aliases 필드 정제
                nc = re.sub(
                    r"^(slug|aliases):\s*(.*)",
                    lambda m: f"{m.group(1)}: {sanitize_url(m.group(2).strip())}",
                    nc,
                    flags=re.MULTILINE,
                )

                with open(p, "w", encoding="utf-8") as file:
                    file.write(nc)

    # 3. 파일명 정제
    for r, d, fs in os.walk(target, topdown=False):
        for f in fs:
            if f.endswith(".md"):
                nb, ex = os.path.splitext(f)
                nn = sanitize_url(nb) + ex
                if f != nn:
                    os.rename(os.path.join(r, f), os.path.join(r, nn))


if __name__ == "__main__":
    final_run()
