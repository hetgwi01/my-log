import os
import re


def sanitize_url(text):
    if not text:
        return ""
    return text.replace("(", "").replace(")", "").replace(" ", "-")


def run_sanitization(target_path):
    if not os.path.exists(target_path):
        return

    print(f"🚀 {target_path} 라우팅 맵 생성 및 링크 치환을 시작합니다.")

    # 1. 라우팅 맵 빌드: { "정제된파일명": "정제된슬러그" }
    route_map = {}
    md_files = []

    for root, dirs, files in os.walk(target_path):
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                md_files.append(full_path)

                # 파일명에서 확장자 뺀 것 (예: 01_싱글톤(Singleton))
                file_id = os.path.splitext(file)
                sanitized_id = sanitize_url(file_id)

                # 파일 내부에서 slug 추출
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    slug_match = re.search(r"^slug:\s*(.*)", content, re.MULTILINE)
                    if slug_match:
                        actual_slug = slug_match.group(1).strip()
                        route_map[sanitized_id] = sanitize_url(actual_slug)
                    else:
                        # slug가 없으면 파일의 상대 경로를 정제해서 주소로 사용
                        rel_path = os.path.relpath(full_path, target_path)
                        route_map[sanitized_id] = sanitize_url(
                            os.path.splitext(rel_path)
                        )

    # 2. 파일 내용 수정 (링크 치환 및 메타데이터 정제)
    for path in md_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # [A] 위키링크 치환: [[파일명|별칭]] -> [[슬러그|별칭]]
        def replace_link(match):
            target = match.group(1)
            alias_part = match.group(2) if match.group(2) else ""
            sanitized_target = sanitize_url(target)

            # 맵에 있는 목적지(Slug)라면 그 주소로 직접 치환
            if sanitized_target in route_map:
                return f"[[{route_map[sanitized_target]}{alias_part}]]"
            return f"[[{sanitized_target}{alias_part}]]"

        # 이미지는 제외하고 일반 링크만 치환
        content = re.sub(r"(?<!\!)\[\[([^|\]]+)(\|[^\]]+)?\]\]", replace_link, content)

        # [B] Frontmatter 내 slug 자체도 정제 (404 방지)
        content = re.sub(
            r"^slug:\s*(.*)",
            lambda m: f"slug: {sanitize_url(m.group(1).strip())}",
            content,
            flags=re.MULTILINE,
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    # 3. 물리적 파일명 변경 (마지막에 실행)
    for path in md_files:
        dir_name = os.path.dirname(path)
        base_name = os.path.basename(path)
        new_name = sanitize_url(base_name)
        if base_name != new_name:
            os.rename(path, os.path.join(dir_name, new_name))

    print(f"✨ {len(route_map)}개의 노드에 대한 라우팅 처리가 완료되었습니다.")


if __name__ == "__main__":
    run_sanitization("temp_notes/private")
