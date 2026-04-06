import os
import re


def sanitize_for_web(text):
    # 주소창과 매칭 시스템에서 문제를 일으키는 괄호와 공백을 제거합니다.
    if not text:
        return ""
    return text.replace("(", "").replace(")", "").replace(" ", "-")


def run_sanitization(target_path):
    if not os.path.exists(target_path):
        print(f"⚠️ {target_path} 경로가 없습니다. (정제를 건너뜁니다)")
        return

    print(f"🚀 {target_path} 경로 전처리를 시작합니다. (Private 전용 / 이미지 보호)")

    # 1. 파일 내용 수정 (내부 링크와 메타데이터 미리 정제)
    for root, dirs, files in os.walk(target_path):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
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
                # 파일을 옮기기 전이므로 여기서 slug를 정제하면 Sync 스크립트가 정제된 경로를 읽게 됩니다.
                def replace_fm(match):
                    key = match.group(1)
                    val = match.group(2)
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
                new_name = sanitize_for_web(name)
                if name != new_name:
                    try:
                        os.rename(
                            os.path.join(root, name), os.path.join(root, new_name)
                        )
                        print(f"✅ 명칭 변경: {name} -> {new_name}")
                    except OSError:
                        pass


if __name__ == "__main__":
    # [수정] 오직 private 폴더만 정제 대상으로 지정합니다.
    # public과 portfolio는 이 과정을 거치지 않고 원본 그대로 유지됩니다.
    run_sanitization("temp_notes/private")
