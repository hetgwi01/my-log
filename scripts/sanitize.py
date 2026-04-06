import os
import re


def sanitize_for_web(text):
    # [에러 방지] 튜플이 들어올 경우 첫 번째 문자열 요소를 사용하고, 아닐 경우 문자열로 강제 변환합니다.
    if isinstance(text, tuple):
        text = text

    if text is None:
        return ""

    text = str(text)
    # 주소창과 매칭 시스템에서 문제를 일으키는 괄호와 공백을 제거합니다.
    return text.replace("(", "").replace(")", "").replace(" ", "-")


def run_sanitization(target_path):
    if not os.path.exists(target_path):
        print(f"⚠️ {target_path} 경로가 없습니다. (정제를 건너뜜)")
        return

    print(f"🚀 {target_path} 전처리를 시작합니다. (Private 전용 / 이미지 보호)")

    # 1. 파일 내용 수정 (내부 링크와 메타데이터 미리 정제)
    for root, dirs, files in os.walk(target_path):
        for file_name in files:
            if file_name.endswith(".md"):
                path = os.path.join(root, file_name)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # [A] 위키링크 정제 (이미지는 ![[ 이므로 제외)
                content = re.sub(
                    r"(?<!\!)\[\[([^|\]]+)(\|[^\]]+)?\]\]",
                    lambda m: (
                        f"[[{sanitize_for_web(m.group(1))}{m.group(2) if m.group(2) else ''}]]"
                    ),
                    content,
                )

                # [B] Frontmatter 내의 slug/aliases 정제
                def replace_fm(match):
                    key = match.group(1)
                    val = match.group(2)
                    # val.strip()은 문자열을 반환하므로 안전합니다.
                    return f"{key}: {sanitize_for_web(val.strip())}"

                content = re.sub(
                    r"^(slug|aliases):\s*(.*)", replace_fm, content, flags=re.MULTILINE
                )

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

    # 2. 물리적 파일명 변경 (MD 파일만)
    for root, dirs, files in os.walk(target_path, topdown=False):
        for name in files:
            if name.endswith(".md"):
                # os.path.splitext는 (이름, 확장자) 튜플을 반환하므로 분리해서 처리해야 합니다.
                base_name, ext = os.path.splitext(name)
                new_base = sanitize_for_web(base_name)
                new_name = new_base + ext

                if name != new_name:
                    try:
                        os.rename(
                            os.path.join(root, name), os.path.join(root, new_name)
                        )
                        print(f"✅ 명칭 변경: {name} -> {new_name}")
                    except OSError as e:
                        print(f"❌ 변경 실패: {e}")


if __name__ == "__main__":
    # 소스 저장소의 private 폴더만 타겟팅합니다.
    run_sanitization("temp_notes/private")
